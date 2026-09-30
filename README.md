# Vinyl or Not

Static **DIY** site for hard-surface flooring: photo reports, an LVP beginner-to-expert guide, measure tips, floor visualize, and a before/after gallery. Guided checklist (not computer vision / AI inspection). Free one-line type guess; paid full report unlock.

**Live:** https://cosmicbonbonsss-cmyk.github.io/vinyl-or-not/

## Tiers

| Tier | Price | What you get |
|------|-------|----------------|
| **Free** | $0 | 1–3 local photo previews + guided checklist → one-line flooring type guess + disclaimer |
| **Paid** | **$10–$15** (default **$12**) | Full report: type confirmation, condition, refinish-vs-replace, cost bands, subfloor red flags, DIY next-step checklist |

Single Stripe product / Payment Link for the paid price. Demo unlock with `?report=1` / sessionStorage.

## Features

- Landing pitch + DIY tool cards (photo report, measure, visualize, gallery, **guide**)
- Client-side photo upload (1–3) with FileReader thumbnails — no server upload in this prototype
- Guided checklist (seams, texture, underlayment, click edges, wear) — clearly labeled **not AI vision**
- Free teaser + disclaimer (not a licensed inspection)
- Paid unlock via Stripe Test Payment Link placeholder (`stripe-config.js`) or demo `?report=1`
- After teaser/report: education CTAs into the guide + measure / visualize / gallery (no retailer affiliate links)
- Plain HTML/CSS/JS — mobile-friendly, no frameworks
- **`guide.html` + `guide/`** — vinyl plank from zero to expert (understand LVP, tools, measure, prep, click-lock install, care, troubleshoot)
- `measure.html` — room measurement tips (length × width, 10–15% waste, doorways/closets, example)
- `visualize.html` — photo-only LVP overlay (4-corner quad + Three.js warp, ambientCG textures)
- **`projects.html`** — public DIY before/after gallery (seeded demos + localStorage uploads)
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

- **Free to browse** for everyone
- **Free to upload** DIY before/after — entries stay on that browser; clearly labeled demo storage
- Seeded demos + JSON import/export for packs

## Stripe setup

1. In Stripe (Test mode), create a **one-time** product at **$12** (or any price in **$10–$15**).
2. Create a **Payment Link** for that product.
3. Set the Payment Link **success URL** to:
   `https://cosmicbonbonsss-cmyk.github.io/vinyl-or-not/?report=1`
4. Put the link in `stripe-config.js` as `checkoutUrl` (see `stripe-config.example.js`).

If `checkoutUrl` is empty, Pay buttons use demo unlock so the prototype works without Stripe.

Unlock is client-side only (query param + `sessionStorage`) — fine for a static demo, not production payment enforcement.

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

- `index.html` — single-page flow (landing → photos → checklist → teaser → report)
- `guide.html` — guide hub
- `guide/` — chapter pages (start, what-is-lvp, tools, measure-plan, prep, install, finish-care, troubleshoot)
- `measure.html` — how to measure rooms for flooring square footage
- `visualize.html` / `visualize.js` / `visualize.css` — floor overlay prototype
- `textures/` — CC0 seamless plank JPGs (see `textures/CREDITS.md`)
- `projects.html` / `projects.js` — DIY before/after gallery
- `specs/` — planning-aid downloads
- `styles.css` — mobile-friendly layout (+ `.guide-*` helpers)
- `app.js` — previews, checklist rules, unlock
- `stripe-config.js` — public placeholders (`checkoutUrl`, `$12` / `$10–$15`)
- `stripe-config.example.js` — documented example Payment Link
