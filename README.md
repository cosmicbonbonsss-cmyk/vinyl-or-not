# Vinyl or Not

Static prototype for **hard-surface flooring photo reports**. Guided checklist (not computer vision / AI inspection). Free one-line type guess; paid full report unlock.

**Live:** https://cosmicbonbonsss-cmyk.github.io/vinyl-or-not/

## Tiers

| Tier | Price | What you get |
|------|-------|----------------|
| **Free** | $0 | 1–3 local photo previews + guided checklist → one-line flooring type guess + disclaimer |
| **Paid** | **$10–$15** (default **$12**) | Full report: type confirmation, condition, refinish-vs-replace, cost bands, subfloor red flags, pro checklist, where-to-buy |
| **Pro tools** (same paid unlock) | **$10–$15** (default **$12**) | Blueprints, receipts, contractor profile editor; featured gallery placement for paid contractors |

No middle tier. Single Stripe product / Payment Link for the paid price. Pro tools unlock with `?pro=1` / `?report=1` / sessionStorage (`vinylProPaid`) — demo-friendly.

## Features

- Landing pitch for photo reports
- Client-side photo upload (1–3) with FileReader / object-URL thumbnails — no server upload in this prototype
- Guided checklist (seams, texture, underlayment, click edges, wear) — clearly labeled **not AI vision**
- Free teaser + disclaimer (not a licensed inspection)
- Paid unlock via Stripe Test Payment Link placeholder (`stripe-config.js`) or demo `?report=1`
- Where to buy: Home Depot, Floor & Decor, Lowe’s + ZIP/city Google Maps search + optional geolocation
- Plain HTML/CSS/JS — mobile-friendly, no frameworks
- `measure.html` — room measurement tips (length × width, 10–15% waste, doorways/closets, example)
- `visualize.html` — photo-only LVP overlay (4-corner quad + Three.js warp, ambientCG textures)
- **`pros.html`** — hub for installers, property managers & designers (trade pricing samples, quote form, specs, trade account stub, paid pro tools). `contractors.html` redirects here.
- **`specs/`** — downloadable planning aids (LVP overview, subfloor prep, moisture notes, waste factor, printable HTML)
- **`projects.html`** — public before/after gallery (seeded demos + localStorage uploads; featured placement for paid contractors)

## For pros (`pros.html`)

Audience jump links: **Installers** | **Property managers** | **Designers**

| Free | Paid (pro unlock) |
|------|-------------------|
| Trade/volume pricing illustration (sample only) | Blueprint uploads (localStorage) |
| Quick quote / bulk inquiry (mailto + clipboard; no auto-send) | Receipt uploads |
| Spec downloads | Personal contractor profile editor |
| Trade account stub (localStorage) | Featured gallery treatment for contractor posts |
| Tool links (measure, visualize, gallery, report) | |

## Project gallery (`projects.html`)

- **Free to browse** for everyone
- **Free to upload** (customers & contractors) — entries stay on that browser; clearly labeled demo storage
- **Featured** section / badge / accent border for paid contractors (`?pro=1` or session unlock) when role = contractor
- Seeded demos include one featured pro job; JSON import/export for packs

## Stripe setup

1. In Stripe (Test mode), create a **one-time** product at **$12** (or any price in **$10–$15**).
2. Create a **Payment Link** for that product.
3. Set the Payment Link **success URL** to:
   `https://cosmicbonbonsss-cmyk.github.io/vinyl-or-not/?report=1`
   (or `.../pros.html?pro=1` for pro tools).
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
- `measure.html` — how to measure rooms for flooring square footage
- `visualize.html` / `visualize.js` / `visualize.css` — floor overlay prototype
- `textures/` — CC0 seamless plank JPGs (see `textures/CREDITS.md`)
- `pros.html` / `pros.js` — pro hub (installers, PMs, designers) + paid tools
- `contractors.html` — redirect to `pros.html`
- `projects.html` / `projects.js` — before/after gallery
- `specs/` — planning-aid downloads
- `styles.css` — mobile-friendly layout
- `app.js` — previews, checklist rules, unlock, where-to-buy Maps/geo
- `stripe-config.js` — public placeholders (`checkoutUrl`, `$12` / `$10–$15`)
- `stripe-config.example.js` — documented example Payment Link
