# Vinyl or Not

Static **DIY** site for hard-surface flooring: a free photo report, an LVP beginner-to-expert guide, a room measure tool, and a before/after gallery. The photo report is a guided checklist (not computer vision). Everything on the site is free — no checkout.

**Live:** https://vinylornot.com/

## Features

- Landing pitch + DIY tool cards (photo report, measure, gallery, **guide**)
- Client-side photo upload (1–3). Photos stay on the device.
- Optional camera with an on-device blur and brightness check
- Guided checklist (seams, texture, underlayment, click edges, wear, flooring look) — clearly labeled **not AI vision**
- Free report: type, condition, refinish-vs-replace, cost band, subfloor notes, next steps
- After the report: guide + measure / gallery
- Amazon Associates links on the Tools chapter (`guide/tools.html`) plus a footer disclosure. Links are built by `affiliate.js`; the Associates tracking ID (`vinylornot-20`) lives in **`affiliate-config.js`** (`window.VINYL_AMAZON_TAG`)
- Plain HTML/CSS/JS — mobile-friendly, no frameworks
- **`guide.html` + `guide/`** — vinyl plank from zero to expert (understand LVP, tools, measure, prep, click-lock install, care, troubleshoot)
- `measure.html` — room measure tool (feet and inches, extra areas, waste, boxes, and planks) plus measuring tips
- **`projects.html`** — DIY before/after gallery (photos stay in this browser)
- **`specs/`** — planning-aid text files and a printable page (not linked from the site nav; the printable page is `noindex`)

## LVP guide (`guide.html`)

Progressive DIY path:

1. Start here → photo report + tool picker  
2. Understand LVP (cores, wear layers, waterproof claims, **thickness failure cases**)  
3. Is vinyl okay for the room (water, wear layer, pets, renters, resale)  
4. Tools & materials (detailed)  
5. Measure & plan  
6. Prep  
7. Install (click-lock focus)  
8. Finish & care  
9. Troubleshoot  

Chapters live under `guide/*.html`. Hub at `/guide.html` (`guide/index.html` redirects there).

Quick-answer pages (linked from the hub's **Quick answers** list, not numbered chapters): `guide/lvp-vs-laminate.html` and `guide/lvp-over-tile.html`.

Several guide pages and `measure.html` end with a short FAQ (`.guide-faq`) plus matching `FAQPage` JSON-LD. Keep the visible question/answer text and the JSON-LD in sync when editing.

After adding or renaming pages: add them to `sitemap.xml`, then run `python3 scripts/build_search_index.py`. Bump the `?v=` cache-bust query on `styles.css` / `search.js` (and inside `search.js` for the index) when CSS or JS changes.


## Project gallery (`projects.html`)

- Save before/after photos in this browser
- Download or restore a JSON backup on this device

## Local preview

```bash
cd vinyl-or-not
python3 -m http.server 8080
# open http://localhost:8080
```

Or open `index.html` directly in a browser.

## Deploy (GitHub Pages)

Repo publishes from `main` branch, root `/`.

## Files

- `index.html` — landing → photos → checklist → free report
- `guide.html` — guide hub
- `guide/` — chapter pages (start, what-is-lvp, is-it-okay, tools, measure-plan, prep, install, finish-care, troubleshoot) plus quick answers (lvp-vs-laminate, lvp-over-tile)
- `404.html` — not-found page (noindex, root-absolute links)
- `measure.html` — how to measure rooms for flooring square footage
- `textures/` — CC0 seamless plank JPGs (see `textures/CREDITS.md`)
- `projects.html` / `projects.js` — DIY before/after gallery
- `specs/` — planning-aid downloads
- `styles.css` — mobile-friendly layout (+ `.guide-*` helpers)
- `app.js` — previews, checklist rules, free report
- `photo-check.js` — on-device blur and brightness check
- `measure.js` — square footage, waste, boxes, and planks
- `affiliate-config.js` — Amazon Associates tag (single place to set it)
- `affiliate.js` — builds `data-amazon-search` / `data-amazon-asin` links with the tag
