#!/usr/bin/env python3
"""Gallery AFTER composites: site plank textures, perspective-warped onto floor.

Constraints:
- Never paint over the bath toilet (restore full toilet from before).
- Keep plank overlay at true floor height; do not run planks up the walls.
- CUBIC warp + unsharp for crisp plank edges/grain (no Gaussian mush).
"""
from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
GALLERY = ROOT / "gallery"
TEXTURES = ROOT / "textures"
WORK = Path("/workspace/gallery-work")
WORK.mkdir(parents=True, exist_ok=True)
RNG = np.random.default_rng(23)


def make_plank_floor(
    tex_bgr: np.ndarray,
    *,
    out_w: int = 5200,
    out_h: int = 3200,
    plank_w: int = 200,
    seam: int = 3,
    grain_along: str = "x",
    rotate_tex90: bool = False,
    length_mult=(48.0, 80.0),
    contrast: float = 1.04,
    tex_scale: float = 2.0,
    jitter=(0.88, 1.12),
    seam_rgb=(16, 20, 26),
) -> np.ndarray:
    """Build a plank sheet. CUBIC upscale; mild contrast calm; crisp seams."""
    t = tex_bgr
    if rotate_tex90:
        t = cv2.rotate(t, cv2.ROTATE_90_CLOCKWISE)
    th, tw = t.shape[:2]
    if abs(tex_scale - 1.0) > 1e-3:
        t = cv2.resize(
            t,
            (max(8, int(round(tw * tex_scale))), max(8, int(round(th * tex_scale)))),
            interpolation=cv2.INTER_AREA if tex_scale < 1.0 else cv2.INTER_CUBIC,
        )
        th, tw = t.shape[:2]
    if abs(contrast - 1.0) > 1e-3:
        lab = cv2.cvtColor(t, cv2.COLOR_BGR2LAB).astype(np.float32)
        L = lab[:, :, 0]
        mean_L = float(L.mean())
        lab[:, :, 0] = np.clip((L - mean_L) * contrast + mean_L, 0, 255)
        for c in (1, 2):
            ch = lab[:, :, c]
            m = float(ch.mean())
            lab[:, :, c] = np.clip((ch - m) * min(1.0, contrast + 0.10) + m, 0, 255)
        t = cv2.cvtColor(lab.astype(np.uint8), cv2.COLOR_LAB2BGR)
    floor = np.zeros((out_h, out_w, 3), dtype=np.uint8)
    seam_color = np.array(seam_rgb, dtype=np.uint8)

    def sample_board(dst_w, dst_h, along="x"):
        def mirror_tile_1d(band, axis, need, origin):
            unit = band
            flip = np.flip(band, axis=axis)
            parts = []
            while True:
                total = sum(p.shape[axis] for p in parts) if parts else 0
                if total - origin >= need:
                    break
                parts.append(unit if len(parts) % 2 == 0 else flip)
                if len(parts) > 64:
                    break
            tiled = np.concatenate(parts, axis=axis)
            if axis == 1:
                return tiled[:, origin : origin + need]
            return tiled[origin : origin + need]

        if along == "x":
            band_h = max(14, min(max(22, th // 10), th - 1))
            sy = int(RNG.integers(0, max(1, th - band_h)))
            band = t[sy : sy + band_h]
            ox = int(RNG.integers(0, tw))
            need = max(dst_w + 32, tw)
            patch = mirror_tile_1d(band, 1, need, ox)
            board = cv2.resize(patch, (dst_w, dst_h), interpolation=cv2.INTER_CUBIC)
        else:
            band_w = max(14, min(max(22, tw // 10), tw - 1))
            sx = int(RNG.integers(0, max(1, tw - band_w)))
            band = t[:, sx : sx + band_w]
            oy = int(RNG.integers(0, th))
            need = max(dst_h + 32, th)
            patch = mirror_tile_1d(band, 0, need, oy)
            board = cv2.resize(patch, (dst_w, dst_h), interpolation=cv2.INTER_CUBIC)
        j = float(RNG.uniform(*jitter))
        return np.clip(board.astype(np.float32) * j, 0, 255).astype(np.uint8)

    if grain_along == "x":
        y, row = 0, 0
        while y < out_h:
            y2 = min(y + plank_w, out_h)
            stagger = int((row % 2) * out_w * 0.18) + int(RNG.integers(0, 30))
            x = -stagger
            while x < out_w:
                length = int(plank_w * float(RNG.uniform(*length_mult)))
                x2 = x + length
                xa, xb = max(0, x), min(out_w, x2)
                if xb > xa:
                    floor[y:y2, xa:xb] = sample_board(xb - xa, y2 - y, "x")
                    if 0 < xb < out_w:
                        floor[y:y2, xb : min(out_w, xb + seam)] = seam_color
                x = x2 + seam
            if y2 < out_h:
                floor[y2 : min(out_h, y2 + seam), :] = seam_color
            y = y2 + seam
            row += 1
    else:
        x, col = 0, 0
        while x < out_w:
            x2 = min(x + plank_w, out_w)
            stagger = int((col % 2) * out_h * 0.18) + int(RNG.integers(0, 30))
            y = -stagger
            while y < out_h:
                length = int(plank_w * float(RNG.uniform(*length_mult)))
                y2 = y + length
                ya, yb = max(0, y), min(out_h, y2)
                if yb > ya:
                    floor[ya:yb, x:x2] = sample_board(x2 - x, yb - ya, "y")
                    if 0 < yb < out_h:
                        floor[yb : min(out_h, yb + seam), x:x2] = seam_color
                y = y2 + seam
            if x2 < out_w:
                floor[:, x2 : min(out_w, x2 + seam)] = seam_color
            x = x2 + seam
            col += 1

    lab = cv2.cvtColor(floor, cv2.COLOR_BGR2LAB).astype(np.float32)
    lab[:, :, 0] = np.clip((lab[:, :, 0] - 128) * 1.06 + 128, 0, 255)
    return cv2.cvtColor(lab.astype(np.uint8), cv2.COLOR_LAB2BGR)


def warp_floor(sheet, dst_hw, src_quad, dst_quad):
    h, w = dst_hw
    M = cv2.getPerspectiveTransform(src_quad.astype(np.float32), dst_quad.astype(np.float32))
    return cv2.warpPerspective(
        sheet, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE
    )


def poly_mask(shape, poly, feather=0):
    h, w = shape
    mask = np.zeros((h, w), dtype=np.uint8)
    cv2.fillPoly(mask, [np.array(poly, np.int32)], 255)
    if feather > 0:
        k = feather * 2 + 1
        mask = cv2.GaussianBlur(mask, (k, k), 0.3)
    return mask


def luminance_ratio(bgr, mask, blur=71):
    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB).astype(np.float32)
    L = lab[:, :, 0]
    m = mask > 128
    mean_L = float(L[m].mean()) if np.any(m) else 128.0
    mean_L = max(mean_L, 1.0)
    k = blur if blur % 2 == 1 else blur + 1
    return np.clip(cv2.GaussianBlur(L, (k, k), 0) / mean_L, 0.62, 1.4)


def unsharp(img: np.ndarray, amount: float = 1.45, sigma: float = 0.7) -> np.ndarray:
    blur = cv2.GaussianBlur(img, (0, 0), sigma)
    return cv2.addWeighted(img, 1.0 + amount, blur, -amount, 0)


def composite(
    before,
    warped,
    floor_mask,
    occluder_mask=None,
    lighting=True,
    light_mix=1.0,
    light_clip=(0.62, 1.4),
    sharpen=True,
):
    """light_mix<1 blends luminance toward 1.0 (calmer); light_clip tightens extremes."""
    fm = floor_mask.astype(np.float32) / 255.0
    if occluder_mask is not None:
        fm = fm * (1.0 - occluder_mask.astype(np.float32) / 255.0)
    m = fm[..., None]
    floor = warped.astype(np.float32)
    if lighting:
        ratio = luminance_ratio(before, (fm * 255).astype(np.uint8))
        lo, hi = light_clip
        ratio = np.clip(ratio, lo, hi)
        if light_mix < 1.0:
            ratio = light_mix * ratio + (1.0 - light_mix)
        floor = np.clip(floor * ratio[..., None], 0, 255)
    out = before.astype(np.float32) * (1.0 - m) + floor * m
    out = np.clip(out, 0, 255).astype(np.uint8)
    if sharpen:
        applied = fm > 0.5
        sharp = unsharp(out, amount=1.40, sigma=0.65)
        out = out.copy()
        out[applied] = sharp[applied]
        if occluder_mask is not None:
            out[occluder_mask > 128] = before[occluder_mask > 128]
    return out


def save_qa(name, before, floor_mask, occ, after, sheet=None):
    applied = floor_mask > 128
    if occ is not None:
        applied = applied & (occ < 128)
    cv2.imwrite(str(WORK / f"{name}-mask.png"), (applied.astype(np.uint8) * 255))
    ov = before.copy()
    ov[applied] = (ov[applied].astype(np.float32) * 0.4 + np.array([0, 150, 255]) * 0.6).astype(
        np.uint8
    )
    cv2.imwrite(str(WORK / f"{name}-mask-ov.jpg"), ov, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
    cv2.imwrite(str(WORK / f"{name}-after.jpg"), after, [int(cv2.IMWRITE_JPEG_QUALITY), 94])
    if sheet is not None:
        cv2.imwrite(
            str(WORK / f"{name}-sheet.jpg"), sheet[:1200, :1200], [int(cv2.IMWRITE_JPEG_QUALITY), 92]
        )


# ---- Living: horizontal warm-oak planks, full floor to baseboards ----
def make_living():
    before = cv2.imread(str(GALLERY / "before-living-empty.jpg"))
    h, w = before.shape[:2]
    tex = cv2.imread(str(TEXTURES / "warm-oak.jpg"))
    sheet = make_plank_floor(
        tex,
        out_w=5200,
        out_h=3000,
        plank_w=400,
        seam=3,
        grain_along="x",
        rotate_tex90=True,
        length_mult=(80.0, 130.0),
        contrast=0.72,
        tex_scale=1.35,
        jitter=(0.96, 1.04),
        seam_rgb=(28, 34, 42),
    )
    floor_poly = [
        (0, h - 1),
        (w - 1, h - 1),
        (w - 1, 680),
        (1160, 620),
        (1100, 575),
        (1020, 545),
        (940, 528),
        (860, 512),
        (800, 502),
        (740, 496),
        (680, 492),
        (600, 490),
        (500, 488),
        (400, 486),
        (300, 486),
        (200, 490),
        (100, 508),
        (0, 538),
    ]
    floor_mask = poly_mask((h, w), floor_poly, feather=0)
    dst = np.array([[0, h - 1], [w - 1, h - 1], [1080, 500], [40, 535]], np.float32)
    src = np.array(
        [[50, 2900], [5150, 2900], [5150, 2900 - 400 * 4], [50, 2900 - 400 * 4]], np.float32
    )
    warped = warp_floor(sheet, (h, w), src, dst)
    after = composite(
        before,
        warped,
        floor_mask,
        None,
        lighting=True,
        light_mix=0.70,
        light_clip=(0.78, 1.20),
        sharpen=True,
    )
    save_qa("living", before, floor_mask, None, after, sheet)
    path = GALLERY / "after-living-warm-oak.jpg"
    cv2.imwrite(str(path), after, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
    ys = np.where(floor_mask > 128)[0]
    gray = cv2.cvtColor(after[int(h * 0.55) :, :], cv2.COLOR_BGR2GRAY)
    print(
        "living",
        path,
        "floor_y",
        int(ys.min()),
        "-",
        int(ys.max()),
        "cov",
        float((floor_mask > 128).mean()),
        "lap",
        round(float(cv2.Laplacian(gray, cv2.CV_64F).var()), 1),
    )
    return after


# ---- Open plan: warm oak into depth; hard furniture silhouettes ----
def make_open():
    before = cv2.imread(str(GALLERY / "before-open-carpet.jpg"))
    h, w = before.shape[:2]
    tex = cv2.imread(str(TEXTURES / "warm-oak.jpg"))
    sheet = make_plank_floor(
        tex,
        out_w=5000,
        out_h=4500,
        plank_w=380,
        seam=3,
        grain_along="y",
        rotate_tex90=False,
        length_mult=(80.0, 130.0),
        contrast=0.70,
        tex_scale=1.35,
        jitter=(0.96, 1.04),
        seam_rgb=(28, 34, 42),
    )
    floor_poly = [
        (0, h - 1),
        (w - 1, h - 1),
        (w - 1, 500),
        (1100, 460),
        (980, 435),
        (860, 420),
        (740, 414),
        (640, 412),
        (560, 420),
        (480, 450),
        (400, 510),
        (320, 575),
        (230, 650),
        (120, 720),
        (0, 770),
    ]
    floor_mask = poly_mask((h, w), floor_poly, feather=0)
    floor_mask[: int(h * 0.38), :] = 0

    bgr = before.astype(np.float32)
    bright = bgr.mean(axis=2)
    sat = bgr.max(axis=2) - bgr.min(axis=2)
    # BGR channels
    Bb, Gg, Rr = bgr[:, :, 0], bgr[:, :, 1], bgr[:, :, 2]

    # Hard occluders: solid armchair bodies (beige ≈ carpet — geometric required)
    occ = np.zeros((h, w), np.uint8)
    cv2.fillPoly(
        occ,
        [
            np.array(
                [
                    (0, 470),
                    (235, 450),
                    (310, 485),
                    (345, 555),
                    (340, 670),
                    (310, 725),
                    (260, 745),
                    (120, 755),
                    (0, 740),
                ],
                np.int32,
            )
        ],
        255,
    )
    cv2.fillPoly(
        occ,
        [
            np.array(
                [
                    (285, 445),
                    (425, 438),
                    (490, 468),
                    (515, 530),
                    (500, 605),
                    (455, 648),
                    (375, 652),
                    (305, 620),
                    (280, 535),
                ],
                np.int32,
            )
        ],
        255,
    )
    cv2.rectangle(occ, (400, 450), (520, 550), 255, -1)
    cv2.fillPoly(
        occ,
        [np.array([(450, 410), (655, 405), (740, 465), (710, 555), (520, 560), (440, 490)], np.int32)],
        255,
    )
    cv2.ellipse(occ, (510, 470), (48, 60), 0, 0, 360, 255, -1)

    # Dining seats only (bright pale upholstery) — floor between chairs stays planks
    seats = np.zeros((h, w), np.uint8)
    for cx, cy, rx, ry in [
        (768, 490, 36, 44),
        (858, 478, 36, 42),
        (948, 490, 34, 44),
        (805, 568, 32, 36),
        (898, 580, 32, 36),
        (978, 565, 32, 36),
    ]:
        cv2.ellipse(seats, (cx, cy), (rx, ry), 0, 0, 360, 255, -1)
    cv2.ellipse(seats, (880, 462), (125, 16), 0, 0, 360, 255, -1)
    seat_occ = ((seats > 0) & (bright > 198) & (sat < 42)).astype(np.uint8) * 255
    seat_occ = cv2.dilate(seat_occ, np.ones((3, 3), np.uint8))

    # Wood legs: brownish (R elevated vs B), mid tone — color-gated, not fat rectangles
    wood_leg = (
        (floor_mask > 0)
        & (occ == 0)
        & (Rr > Bb + 8)
        & (Rr > Gg - 5)
        & (bright > 70)
        & (bright < 175)
        & (sat > 18)
        & (sat < 70)
    )
    # Only keep wood_leg inside dining band where chairs live
    dining_band = np.zeros((h, w), bool)
    dining_band[450:720, 720:1050] = True
    # Require proximity to seat hulls so we don't paint random brown carpet
    near_seat = cv2.dilate(seats, np.ones((35, 35), np.uint8)) > 0
    leg_occ = (wood_leg & dining_band & near_seat).astype(np.uint8) * 255
    leg_occ = cv2.dilate(leg_occ, np.ones((2, 2), np.uint8))

    occ = np.maximum(np.maximum(occ, seat_occ), leg_occ)

    # Floor = full poly minus furniture
    combined = floor_mask.copy()
    combined[occ > 0] = 0
    # Dining carpet between chairs: force any carpet-like pixel back as floor
    # (seat_occ already removed bright seats; this undoes over-broad wood-leg claims)
    dining_carpet = (
        dining_band
        & (floor_mask > 0)
        & (bright > 150)
        & (bright < 198)
        & (sat < 40)
        & (Bb > 130)
        & (seat_occ == 0)
    )
    combined[dining_carpet] = 255
    # Close hairline gaps under thin legs
    combined = cv2.morphologyEx(
        combined,
        cv2.MORPH_CLOSE,
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)),
        iterations=1,
    )
    combined[seat_occ > 0] = 0
    combined[occ > 0] = 0
    # Re-apply dining carpet after occ (occ includes armchair polys outside dining — fine)
    combined[dining_carpet] = 255
    combined[seat_occ > 0] = 0
    combined[floor_mask == 0] = 0
    combined[: int(h * 0.38), :] = 0
    # Don't let wood-leg occ punch dining carpet back out during composite
    occ[dining_carpet] = 0
    occ[combined > 0] = 0

    dst = np.array([[0, h - 1], [w - 1, h - 1], [1020, 415], [80, 730]], np.float32)
    src = np.array(
        [[120, 4350], [4880, 4350], [4880, 4350 - 380 * 5], [120, 4350 - 380 * 5]], np.float32
    )
    warped = warp_floor(sheet, (h, w), src, dst)
    after = composite(
        before,
        warped,
        combined,
        occ,
        lighting=True,
        light_mix=0.70,
        light_clip=(0.78, 1.20),
        sharpen=True,
    )
    after[occ > 0] = before[occ > 0]

    save_qa("open", before, combined, occ, after, sheet)
    path = GALLERY / "after-open-warm-oak.jpg"
    cv2.imwrite(str(path), after, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
    applied = (combined > 128) & (occ < 128)
    ys = np.where(applied)[0]
    gray = cv2.cvtColor(after[int(h * 0.55) :, :], cv2.COLOR_BGR2GRAY)
    print(
        "open",
        path,
        "floor_y",
        int(ys.min()) if len(ys) else None,
        "-",
        int(ys.max()) if len(ys) else None,
        "cov",
        float(applied.mean()),
        "lap",
        round(float(cv2.Laplacian(gray, cv2.CV_64F).var()), 1),
    )
    return after



def main():
    make_living()
    make_open()
    # Bath uses dedicated sharper mask script
    from make_bath_after import make_bath

    make_bath()
    print("done")


if __name__ == "__main__":
    main()
