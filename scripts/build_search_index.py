#!/usr/bin/env python3
"""Build search-index.json for the on-site search box (search.js).

Reads the page list from sitemap.xml, so only public, indexable pages are
included. For each page it pulls the <title>, meta description, H1, and H2s,
then adds a few plain keywords so people can find pages the way they type
(for example "walnut kitchen" or "dog wear layer").

Run from the repo root after changing page titles or adding pages:

    python3 scripts/build_search_index.py

No dependencies beyond the Python standard library.
"""
from __future__ import annotations

import html
import json
import re
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://vinylornot.com/"
SUFFIXES = (" | Vinyl or Not", " — Vinyl or Not guide")

# Extra words people type that a page's headings may not contain.
EXTRA_KEYWORDS = {
    "": "home photo report identify floor is it vinyl checklist free tools",
    "guide.html": "guide hub chapters beginner learn lvp how to",
    "diy-install.html": "install installation how to diy click lock steps quick start yourself acclimate underlayment cutting seams transitions",
    "measure.html": "calculator square footage sq ft how much flooring do i need boxes waste planks measure room",
    "projects.html": "before after gallery projects photos makeover inspiration",
    "floors/": "floor looks wood look colors oak walnut maple room ideas",
    "guide/start.html": "start beginner first steps photo report",
    "guide/what-is-lvp.html": "what is lvp luxury vinyl plank spc wpc rigid core thickness mm wear layer mil waterproof glue down",
    "guide/is-it-okay.html": "bathroom kitchen water waterproof dogs pets kids renters rental resale wear layer mil plank size good okay",
    "guide/lvp-vs-laminate.html": "lvp vs laminate vinyl plank versus laminate compare comparison difference which is better bathroom kitchen basement dogs pets waterproof",
    "guide/lvp-over-tile.html": "lvp over tile vinyl plank over tile existing floor grout lines cover old floor carpet sheet vinyl hardwood height door underlayment",
    "guide/lvp-cost.html": "lvp cost price how much per square foot sq ft budget cheap installed labor diy vs pro installer quote 12x12 bedroom underlayment trim transitions removal 6 mil 12 mil 20 mil",
    "guide/lvp-basement.html": "lvp basement below grade concrete slab moisture test plastic sheet calcium chloride rh probe vapor barrier 6 mil poly underlayment flood flooding water leak mold dehumidifier humidity",
    "guide/tools.html": "tools materials checklist tapping block pull bar cutter saw spacers mallet underlayment knee pads 12 mil 20 mil",
    "guide/measure-plan.html": "measure plan layout direction which way planks run last row waste transitions square footage",
    "guide/prep.html": "prep subfloor flat level moisture concrete best underlayment for lvp pad vapor barrier flatness",
    "guide/install.html": "install installation how to click lock starter row stagger door jambs last row expansion gap",
    "guide/finish-care.html": "finish care cleaning baseboards trim quarter round transitions maintenance",
    "guide/troubleshoot.html": "troubleshoot fix problems gaps peaking buckling noise squeak broken lock repair",
}

ROOM_WORDS = {
    "living-room": "living room lounge family room",
    "bedroom": "bedroom",
    "kitchen": "kitchen",
    "bathroom": "bathroom bath",
}


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.description = ""
        self.robots = ""
        self.h1 = ""
        self.h2s: list[str] = []
        self._cur: str | None = None
        self._buf: list[str] = []
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("script", "style"):
            self._skip += 1
        elif tag == "meta" and a.get("name") == "description":
            self.description = a.get("content", "")
        elif tag == "meta" and a.get("name") == "robots":
            self.robots = a.get("content", "")
        elif tag in ("title", "h1", "h2") and self._cur is None:
            self._cur, self._buf = tag, []

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self._skip = max(0, self._skip - 1)
        elif tag == self._cur:
            text = re.sub(r"\s+", " ", "".join(self._buf)).strip()
            if tag == "title":
                self.title = text
            elif tag == "h1" and not self.h1:
                self.h1 = text
            elif tag == "h2" and text:
                self.h2s.append(text)
            self._cur = None

    def handle_data(self, data):
        if self._cur and not self._skip:
            self._buf.append(data)


def sitemap_paths() -> list[str]:
    xml = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    locs = re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", xml)
    return [html.unescape(u)[len(SITE):] for u in locs if u.startswith(SITE)]


def file_for(path: str) -> Path:
    if path == "" or path.endswith("/"):
        return ROOT / path / "index.html"
    return ROOT / path


def clean_title(t: str) -> str:
    for s in SUFFIXES:
        if t.endswith(s):
            t = t[: -len(s)]
    return t.strip()


def floor_keywords(path: str) -> str:
    slug = Path(path).stem
    for room, words in ROOM_WORDS.items():
        if slug.endswith("-" + room):
            look = slug[: -len(room) - 1].replace("-", " ")
            if look == "pine natural":
                look = "natural pine"
            return f"{look} {words} floor look wood look lvp vinyl plank"
    return ""


def build() -> list[dict]:
    entries = []
    for path in sitemap_paths():
        f = file_for(path)
        if not f.exists():
            raise SystemExit(f"sitemap lists {path!r} but {f} is missing")
        p = PageParser()
        p.feed(f.read_text(encoding="utf-8"))
        if "noindex" in p.robots.lower():
            continue
        title = clean_title(p.title) or p.h1
        kw = []
        if path.startswith("floors/") and path != "floors/":
            kw.append(floor_keywords(path))
            section = "Floor look"
        else:
            kw.append(EXTRA_KEYWORDS.get(path, ""))
            kw.extend(h for h in p.h2s if h.lower() not in ("where to go next",))
            if p.h1 and p.h1 != title:
                kw.append(p.h1)
            section = "Guide" if path.startswith("guide") else "Page"
            if path == "floors/":
                section = "Floor looks"
        words = re.findall(r"[a-z0-9]+", " ".join(kw).lower())
        seen, uniq = set(), []
        for w in words:
            if len(w) < 2:
                continue
            if w not in seen:
                seen.add(w)
                uniq.append(w)
        entries.append({
            "t": title,
            "u": path,
            "d": p.description,
            "k": " ".join(uniq),
            "s": section,
        })
    return entries


def main() -> None:
    entries = build()
    out = ROOT / "search-index.json"
    out.write_text(json.dumps(entries, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"wrote {out.relative_to(ROOT)}: {len(entries)} pages, {out.stat().st_size} bytes")


if __name__ == "__main__":
    main()
