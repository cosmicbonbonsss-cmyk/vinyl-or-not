#!/usr/bin/env python3
"""Gallery AFTER composites: site plank textures, perspective-warped onto floor.

Constraints:
- Floor ONLY — planks must not climb walls, wainscoting, baseboards, radiators, sills.
- Never paint over bath toilet porcelain (delegated to make_bath_after).
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


def horizon_mask(h, w, horizon_pts):
    xs = np.array([p[0] for p in horizon_pts], dtype=np.float64)
    ys = np.array([p[1] for p in horizon_pts], dtype=np.float64)
    horizon = np.interp(np.arange(w), xs, ys)
    k = 11
    pad = np.pad(horizon, (k // 2, k // 2), mode="edge")
    horizon = np.convolve(pad, np.ones(k) / k, mode="valid")
    mask = np.zeros((h, w), np.uint8)
    poly = [(0, h - 1), (w - 1, h - 1)] + [
        (x, int(round(horizon[x]))) for x in range(w - 1, -1, -1)
    ]
    cv2.fillPoly(mask, [np.array(poly, np.int32)], 255)
    return mask, horizon


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

    # Cap BELOW baseboard under window (~y580) and follow right-wall junction.
    # Do NOT dip to ~y428 — that paints wood-toned wainscot/panels.
    horizon_pts = [
        (0, 588),
        (80, 584),
        (160, 580),
        (240, 576),
        (320, 572),
        (400, 568),
        (460, 562),
        (520, 555),
        (560, 545),
        (600, 520),
        (640, 500),
        (680, 488),
        (720, 480),
        (760, 485),
        (800, 508),
        (840, 522),
        (880, 536),
        (920, 548),
        (960, 560),
        (1000, 570),
        (1040, 580),
        (1080, 590),
        (1120, 602),
        (1160, 614),
        (1199, 622),
    ]
    floor_mask, horizon = horizon_mask(h, w, horizon_pts)

    # Strip gray wall pixels at the top edge of the mask
    lab = cv2.cvtColor(before, cv2.COLOR_BGR2LAB).astype(np.float32)
    chroma = np.sqrt((lab[:, :, 1] - 128) ** 2 + (lab[:, :, 2] - 128) ** 2)
    wallish = (chroma < 12) & (lab[:, :, 0] > 155)
    for x in range(w):
        y0 = int(round(horizon[x]))
        for y in range(y0, min(h, y0 + 12)):
            if wallish[y, x]:
                floor_mask[y, x] = 0
            else:
                break

    dst = np.array(
        [[0, h - 1], [w - 1, h - 1], [1050, float(horizon[1050])], [100, float(horizon[100])]],
        np.float32,
    )
    src = np.array(
        [[100, 2900], [5100, 2900], [5100, 2900 - 400 * 4], [100, 2900 - 400 * 4]], np.float32
    )
    warped = warp_floor(sheet, (h, w), src, dst)
    after = composite(
        before, warped, floor_mask, None,
        lighting=True, light_mix=0.70, light_clip=(0.78, 1.20), sharpen=True,
    )
    save_qa("living", before, floor_mask, None, after, sheet)
    path = GALLERY / "after-living-warm-oak.jpg"
    cv2.imwrite(str(path), after, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
    ys = np.where(floor_mask > 128)[0]
    gray = cv2.cvtColor(after[int(h * 0.55) :, :], cv2.COLOR_BGR2GRAY)
    wall_band = np.zeros((h, w), bool)
    for x in range(w):
        wall_band[: max(0, int(horizon[x]) - 4), x] = True
    diff = np.abs(after.astype(np.float32) - before.astype(np.float32)).mean(axis=2)
    print(
        "living", path, "floor_y", int(ys.min()), "-", int(ys.max()),
        "cov", float((floor_mask > 128).mean()),
        "lap", round(float(cv2.Laplacian(gray, cv2.CV_64F).var()), 1),
        "wallΔ", round(float(diff[wall_band].mean()), 3),
    )
    return after


def make_open():
    before = cv2.imread(str(GALLERY / "before-open-carpet.jpg"))
    h, w = before.shape[:2]
    tex = cv2.imread(str(TEXTURES / "warm-oak.jpg"))
    sheet = make_plank_floor(
        tex,
        out_w=4800,
        out_h=5200,
        plank_w=360,
        seam=3,
        grain_along="y",
        rotate_tex90=False,
        length_mult=(70.0, 110.0),
        contrast=0.70,
        tex_scale=1.35,
        jitter=(0.96, 1.04),
        seam_rgb=(28, 34, 42),
    )

    # Conservative horizon — below walls/baseboards; left raised by chairs
    horizon_pts = [
        (0, 755),
        (80, 748),
        (160, 742),
        (240, 720),
        (300, 690),
        (360, 655),
        (420, 620),
        (480, 575),
        (540, 545),
        (600, 520),
        (660, 500),
        (720, 455),
        (780, 445),
        (840, 440),
        (900, 442),
        (960, 450),
        (1020, 465),
        (1080, 485),
        (1140, 515),
        (1199, 548),
    ]
    floor_mask, horizon = horizon_mask(h, w, horizon_pts)
    floor_mask[: int(h * 0.42), :] = 0
    for x in range(w):
        floor_mask[: int(horizon[x]), x] = 0

    bgr = before.astype(np.float32)
    bright = bgr.mean(axis=2)
    sat = bgr.max(axis=2) - bgr.min(axis=2)
    Bb, Gg, Rr = bgr[:, :, 0], bgr[:, :, 1], bgr[:, :, 2]

    occ = np.zeros((h, w), np.uint8)
    cv2.fillPoly(
        occ,
        [np.array([(0, 470), (235, 450), (310, 485), (345, 555), (340, 670),
                   (310, 725), (260, 745), (120, 755), (0, 740)], np.int32)],
        255,
    )
    cv2.fillPoly(
        occ,
        [np.array([(285, 445), (425, 438), (490, 468), (515, 530), (500, 605),
                   (455, 648), (375, 652), (305, 620), (280, 535)], np.int32)],
        255,
    )
    cv2.rectangle(occ, (400, 450), (520, 550), 255, -1)
    cv2.fillPoly(
        occ,
        [np.array([(450, 410), (655, 405), (740, 465), (710, 555), (520, 560), (440, 490)], np.int32)],
        255,
    )
    cv2.ellipse(occ, (510, 470), (48, 60), 0, 0, 360, 255, -1)

    seats = np.zeros((h, w), np.uint8)
    for cx, cy, rx, ry in [
        (768, 490, 40, 48), (858, 478, 40, 46), (948, 490, 38, 48),
        (805, 568, 36, 40), (898, 580, 36, 40), (978, 565, 36, 40),
    ]:
        cv2.ellipse(seats, (cx, cy), (rx, ry), 0, 0, 360, 255, -1)
    cv2.ellipse(seats, (880, 458), (140, 18), 0, 0, 360, 255, -1)
    # Broader seat gate + geometric seat ellipses as hard occ (beige ≈ carpet)
    seat_occ = ((seats > 0) & (bright > 185) & (sat < 50)).astype(np.uint8) * 255
    seat_occ = cv2.dilate(seat_occ, np.ones((5, 5), np.uint8))

    wood_leg = (
        (floor_mask > 0) & (occ == 0) & (Rr > Bb + 8) & (Rr > Gg - 5)
        & (bright > 70) & (bright < 175) & (sat > 18) & (sat < 70)
    )
    dining_band = np.zeros((h, w), bool)
    dining_band[450:720, 700:1060] = True
    near_seat = cv2.dilate(seats, np.ones((40, 40), np.uint8)) > 0
    leg_occ = (wood_leg & dining_band & near_seat).astype(np.uint8) * 255
    leg_occ = cv2.dilate(leg_occ, np.ones((2, 2), np.uint8))

    arm_only = occ.copy()
    occ = np.maximum(np.maximum(occ, seat_occ), leg_occ)

    combined = floor_mask.copy()
    combined[occ > 0] = 0
    dining_carpet = (
        dining_band & (floor_mask > 0) & (bright > 140) & (bright < 205)
        & (sat < 45) & (seat_occ == 0)
    )
    combined[dining_carpet] = 255
    combined = cv2.morphologyEx(
        combined, cv2.MORPH_CLOSE,
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)), iterations=2,
    )
    combined[seat_occ > 0] = 0
    combined[arm_only > 0] = 0
    combined[dining_carpet] = 255
    combined[seat_occ > 0] = 0
    combined[arm_only > 0] = 0
    combined[floor_mask == 0] = 0
    combined[: int(h * 0.42), :] = 0

    occ2 = np.maximum(seat_occ, arm_only)

    dst = np.array(
        [[40, h - 1], [w - 40, h - 1], [1000, float(horizon[1000])], [200, float(horizon[200])]],
        np.float32,
    )
    src = np.array(
        [[200, 5000], [4600, 5000], [4600, 5000 - 360 * 8], [200, 5000 - 360 * 8]], np.float32
    )
    warped = warp_floor(sheet, (h, w), src, dst)
    after = composite(
        before, warped, combined, occ2,
        lighting=True, light_mix=0.70, light_clip=(0.78, 1.20), sharpen=True,
    )
    after[occ2 > 0] = before[occ2 > 0]
    # Post: restore pale dining/armchair upholstery if planks leaked on
    pale_band = np.zeros((h, w), bool)
    pale_band[460:620, 740:1020] = True
    pale_band[480:640, 40:500] = True
    pale = pale_band & (bright > 190) & (sat < 50)
    diff_tmp = np.abs(after.astype(np.float32) - before.astype(np.float32)).mean(axis=2)
    after[pale & (diff_tmp > 15)] = before[pale & (diff_tmp > 15)]

    save_qa("open", before, combined, occ2, after, sheet)
    path = GALLERY / "after-open-warm-oak.jpg"
    cv2.imwrite(str(path), after, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
    applied = (combined > 128) & (occ2 < 128)
    ys = np.where(applied)[0]
    gray = cv2.cvtColor(after[int(h * 0.55) :, :], cv2.COLOR_BGR2GRAY)
    wall_band = np.zeros((h, w), bool)
    for x in range(w):
        wall_band[: max(0, int(horizon[x]) - 4), x] = True
    diff = np.abs(after.astype(np.float32) - before.astype(np.float32)).mean(axis=2)
    print(
        "open", path, "floor_y",
        int(ys.min()) if len(ys) else None, "-", int(ys.max()) if len(ys) else None,
        "cov", float(applied.mean()),
        "lap", round(float(cv2.Laplacian(gray, cv2.CV_64F).var()), 1),
        "wallΔ", round(float(diff[wall_band].mean()), 3),
    )
    return after


def main():
    make_living()
    make_open()
    from make_bath_after import make_bath
    make_bath()
    print("done")


if __name__ == "__main__":
    main()
