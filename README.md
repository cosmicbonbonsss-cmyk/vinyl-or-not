# Vinyl or Not

Static **DIY** site for hard-surface flooring: a free photo report, an LVP beginner-to-expert guide, a room measure tool, floor visualize, and a before/after gallery. The photo report is a guided checklist (not computer vision). Everything on the site is free — no checkout.

**Live:** https://vinylornot.com/

## Features

- Landing pitch + DIY tool cards (photo report, measure, visualize, gallery, **guide**)
- Client-side photo upload (1–3). Photos stay on the device.
- Optional camera with an on-device blur and brightness check
- Guided checklist (seams, texture, underlayment, click edges, wear, flooring look) — clearly labeled **not AI vision**
- Free report: type, condition, refinish-vs-replace, cost band, subfloor notes, next steps
- After the report: guide + measure / visualize / gallery (no retailer affiliate links)
- Plain HTML/CSS/JS — mobile-friendly, no frameworks
- **`guide.html` + `guide/`** — vinyl plank from zero to expert (understand LVP, tools, measure, prep, click-lock install, care, troubleshoot)
- `measure.html` — room measure tool (feet and inches, extra areas, waste, boxes, and planks) plus measuring tips
- `visualize.html` — room photo LVP overlay (camera or upload, flooring looks, 4-corner quad)
- **`projects.html`** — DIY before/after gallery (local photos until a shared gallery is connected)
- **`specs/`** — downloadable planning aids (LVP overview, subfloor prep, moisture notes, waste factor, printable HTML)

## LVP guide (`guide.html`)

Progressive DIY path:

1. Start here → photo report + tool picker  
2. Understand LVP (cores, wear layers, waterproof claims, **thickness failure cases**)  
3. Tools & materials (detailed)  
4. Measure & plan  
5. Prep  
6. Install (click-lock focus)  
7. Finish & care  
8. Troubleshoot  

Chapters live under `guide/*.html`. Hub at `/guide.html` (`guide/index.html` redirects there).

## Project gallery (`projects.html`)

- **Upload** DIY before/after to the shared gallery feed
- Upload before/after photos in this browser, with JSON import/export for backups

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
- `guide/` — chapter pages (start, what-is-lvp, tools, measure-plan, prep, install, finish-care, troubleshoot)
- `measure.html` — how to measure rooms for flooring square footage
- `visualize.html` / `visualize.js` / `visualize.css` — floor overlay
- `textures/` — CC0 seamless plank JPGs (see `textures/CREDITS.md`)
- `projects.html` / `projects.js` — DIY before/after gallery
- `specs/` — planning-aid downloads
- `styles.css` — mobile-friendly layout (+ `.guide-*` helpers)
- `app.js` — previews, checklist rules, free report
- `photo-check.js` — on-device blur and brightness check
- `measure.js` — square footage, waste, boxes, and planks
