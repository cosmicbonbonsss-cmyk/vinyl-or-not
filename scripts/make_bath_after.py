#!/usr/bin/env python3
"""Rebuild gallery/after-bath-medium-oak.jpg (Denver bath)."""
from __future__ import annotations
from pathlib import Path
import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
GALLERY = ROOT / "gallery"
TEXTURES = ROOT / "textures"
WORK = Path("/workspace/gallery-work")
WORK.mkdir(parents=True, exist_ok=True)
RNG = np.random.default_rng(47)


def make_depth_planks(tex_bgr, out_w=4400, out_h=3400, plank_w=120, seam=2):
    t = cv2.rotate(tex_bgr, cv2.ROTATE_90_CLOCKWISE)
    t = cv2.resize(t, (t.shape[1] * 2, t.shape[0] * 2), interpolation=cv2.INTER_AREA)
    lab = cv2.cvtColor(t, cv2.COLOR_BGR2LAB).astype(np.float32)
    L = lab[:, :, 0]
    m = float(L.mean())
    lab[:, :, 0] = np.clip((L - m) * 0.70 + m + 8, 0, 255)
    t = cv2.cvtColor(lab.astype(np.uint8), cv2.COLOR_LAB2BGR)
    th, tw = t.shape[:2]
    floor = np.zeros((out_h, out_w, 3), np.uint8)
    seam_c = np.array([16, 20, 26], np.uint8)
    x, col = 0, 0
    while x < out_w:
        pw = plank_w + int(RNG.integers(-6, 10))
        x2 = min(x + pw, out_w)
        stagger = int((col % 2) * out_h * 0.25) + int(RNG.integers(0, 40))
        y = -stagger
        while y < out_h:
            length = int(pw * float(RNG.uniform(55, 100)))
            y2 = y + length
            ya, yb = max(0, y), min(out_h, y2)
            if yb > ya:
                bw = max(28, min(tw // 2, tw - 1))
                sx = int(RNG.integers(0, max(1, tw - bw)))
                band = t[:, sx : sx + bw]
                oy = int(RNG.integers(0, th))
                tiled = np.concatenate([band, np.flip(band, 0), band, np.flip(band, 0), band], 0)
                need = max(yb - ya + 40, th)
                while tiled.shape[0] - oy < need:
                    tiled = np.concatenate([tiled, np.flip(tiled, 0)], 0)
                board = cv2.resize(
                    tiled[oy : oy + need], (x2 - x, yb - ya), interpolation=cv2.INTER_LINEAR
                )
                j = float(RNG.uniform(0.97, 1.03))
                floor[ya:yb, x:x2] = np.clip(board.astype(np.float32) * j, 0, 255).astype(np.uint8)
                if 0 < yb < out_h:
                    floor[yb : min(out_h, yb + seam), x:x2] = seam_c
            y = y2 + seam
        if x2 < out_w:
            floor[:, x2 : min(out_w, x2 + seam)] = seam_c
        x = x2 + seam
        col += 1
    return floor


def ortho(sheet, h, w, y_top, taper=0.10):
    fh = h - y_top
    tw = int(w * (1 + taper))
    scaled = cv2.resize(sheet, (tw, max(fh * 2, fh + 80)), interpolation=cv2.INTER_LINEAR)
    band = scaled[-fh:]
    if band.shape[0] != fh:
        band = cv2.resize(band, (band.shape[1], fh), interpolation=cv2.INTER_LINEAR)
    bw = band.shape[1]
    mapx = np.zeros((fh, w), np.float32)
    mapy = np.zeros((fh, w), np.float32)
    for i in range(fh):
        t = i / max(fh - 1, 1)
        usable = bw * (1 - taper * (1 - t))
        x0 = (bw - usable) * 0.5
        mapx[i] = x0 + np.linspace(0, usable - 1e-3, w)
        mapy[i] = i
    rem = cv2.remap(band, mapx, mapy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101)
    out = np.zeros((h, w, 3), np.uint8)
    out[y_top:] = rem
    return out


def horizon_line(w, pts, k=15):
    xs = np.array([p[0] for p in pts], float)
    ys = np.array([p[1] for p in pts], float)
    hzn = np.interp(np.arange(w), xs, ys)
    return np.convolve(np.pad(hzn, (k // 2, k // 2), "edge"), np.ones(k) / k, "valid")


def make_bath() -> Path:
    before = cv2.imread(str(GALLERY / "before-bath-checkered.jpg"))
    assert before is not None
    h, w = before.shape[:2]
    tex = cv2.imread(str(TEXTURES / "medium-oak.jpg"))
    assert tex is not None

    bgr = before.astype(np.float32)
    bright = bgr.mean(2)
    sat = bgr.max(2) - bgr.min(2)
    B, Gc, R = bgr[:, :, 0], bgr[:, :, 1], bgr[:, :, 2]
    black = (bright < 115) & (sat < 55)
    white = (bright > 145) & (sat < 55)
    bn = cv2.dilate(black.astype(np.uint8) * 255, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (51, 51))) > 0
    wn = cv2.dilate(white.astype(np.uint8) * 255, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (51, 51))) > 0
    chk_raw = (black & wn) | (white & bn)
    green = (Gc > R + 12) & (Gc > B + 12)
    L = cv2.cvtColor(before, cv2.COLOR_BGR2LAB)[:, :, 0].astype(np.float32)
    lv = cv2.blur((L - cv2.blur(L, (9, 9))) ** 2, (9, 9))

    # Horizon at baseboard bottom (no climb)
    horizon = horizon_line(
        w,
        [
            (0, 798), (80, 785), (160, 770), (240, 756), (320, 746),
            (400, 738), (480, 734), (560, 732), (640, 731), (720, 732),
            (800, 734), (880, 740), (960, 750), (1040, 762), (1120, 778), (1199, 795),
        ],
    )
    FLOOR_TOP = int(horizon.min()) - 1
    poly = np.zeros((h, w), np.uint8)
    cv2.fillPoly(
        poly,
        [np.array([(0, h - 1), (w - 1, h - 1)] + [(x, int(round(horizon[x]))) for x in range(w - 1, -1, -1)], np.int32)],
        255,
    )
    for x in range(w):
        poly[: int(round(horizon[x])), x] = 0

    # --- Fixture ROIs (geometry first; exclude from checker) ---
    toilet_roi = np.zeros((h, w), np.uint8)
    cv2.fillPoly(
        toilet_roi,
        [np.array([
            (708, 635), (802, 620), (858, 650), (870, 715), (862, 775),
            (848, 832), (822, 872), (782, 890), (748, 886), (718, 852),
            (700, 798), (694, 738), (702, 678),
        ], np.int32)],
        255,
    )
    cv2.rectangle(toilet_roi, (702, 555), (848, 698), 255, -1)

    stool_roi = np.zeros((h, w), np.uint8)
    cv2.fillPoly(stool_roi, [np.array([[398, 776], [540, 776], [544, 844], [394, 844]], np.int32)], 255)
    # Real leg columns from before photo (white vertical runs)
    for lx0, lx1 in ((397, 408), (528, 548)):
        cv2.rectangle(stool_roi, (lx0, 844), (lx1, 899), 255, -1)
    # Front/mid legs (shorter / thinner)
    for lx0, lx1 in ((430, 436), (508, 516)):
        cv2.rectangle(stool_roi, (lx0, 844), (lx1, 899), 255, -1)

    ped_roi = np.zeros((h, w), np.uint8)
    cv2.ellipse(ped_roi, (288, 878), (44, 24), 0, 0, 360, 255, -1)
    cv2.ellipse(ped_roi, (282, 812), (17, 42), 0, 0, 360, 255, -1)

    plant_roi = np.zeros((h, w), np.uint8)
    cv2.ellipse(plant_roi, (148, 858), (62, 34), 0, 0, 360, 255, -1)  # pot wider
    cv2.ellipse(plant_roi, (115, 775), (38, 55), -12, 0, 360, 255, -1)

    trash_roi = np.zeros((h, w), np.uint8)
    cv2.ellipse(trash_roi, (868, 788), (30, 24), 0, 0, 360, 255, -1)

    fix_roi = np.maximum(np.maximum(toilet_roi, stool_roi), np.maximum(np.maximum(ped_roi, plant_roi), trash_roi))

    # Checker on floor only — never inside fixture ROIs
    chk = chk_raw & (fix_roi == 0) & (poly > 0)

    # Porcelain / fixture masks from ROI ∩ color (allow white even if chk_raw)
    porc = (toilet_roi > 0) & (bright > 140) & (sat < 55) & (lv < 350) & ~black
    toilet = porc.astype(np.uint8) * 255
    toilet = cv2.morphologyEx(toilet, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))
    toilet = cv2.dilate(toilet, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
    toilet[chk] = 0  # still never claim actual floor tiles

    stool = ((stool_roi > 0) & (bright > 135) & (sat < 55) & ~black).astype(np.uint8) * 255
    stool[chk] = 0
    ped = ((ped_roi > 0) & (bright > 125) & (sat < 55) & ~black).astype(np.uint8) * 255
    ped[chk] = 0
    plant = ((plant_roi > 0) & (((bright > 120) & (sat < 55)) | green) & ~black).astype(np.uint8) * 255
    plant[chk] = 0
    trash = ((trash_roi > 0) & (bright > 145) & (sat < 50) & ~black).astype(np.uint8) * 255
    trash[chk] = 0

    fixtures = np.maximum(np.maximum(toilet, stool), np.maximum(np.maximum(ped, plant), trash))

    # Floor mask
    mask = np.zeros((h, w), np.uint8)
    mask[(poly > 0) & chk] = 255
    floorish = (poly > 0) & (fixtures == 0) & (fix_roi == 0) & ~green & (bright > 8) & (bright < 250) & (sat < 90)
    # Also allow floorish inside fix_roi only where clearly checker
    floorish |= (poly > 0) & chk
    mask[floorish] = 255
    mask[fixtures > 0] = 0

    for _ in range(22):
        dil = cv2.dilate(mask, np.ones((5, 5), np.uint8))
        grow = (dil > 0) & (poly > 0) & (fixtures == 0) & (mask == 0) & ~green
        # don't grow onto bright fixture porcelain
        grow &= ~((fix_roi > 0) & (bright > 150) & (sat < 45) & ~chk)
        if not grow.any():
            break
        mask[grow] = 255
    mask[(poly > 0) & chk] = 255
    mask[fixtures > 0] = 0
    for x in range(w):
        mask[: int(round(horizon[x])), x] = 0
    # Bottom corners to frame
    mask[h - 50 :, :] = np.maximum(mask[h - 50 :, :], 255)
    mask[fixtures > 0] = 0
    for x in range(w):
        mask[: int(round(horizon[x])), x] = 0

    occ = fixtures.copy()

    sheet = make_depth_planks(tex)
    warped = ortho(sheet, h, w, max(FLOOR_TOP - 8, 0), taper=0.10)
    L_light = cv2.GaussianBlur(L, (151, 151), 0)
    Lt = cv2.cvtColor(warped, cv2.COLOR_BGR2LAB)[:, :, 0].astype(np.float32)
    ratio = np.clip(L_light / np.maximum(cv2.GaussianBlur(Lt, (51, 51), 0), 1), 0.85, 1.15)
    yy = np.linspace(0.92, 1.08, h).astype(np.float32)[:, None]
    floor = np.clip(warped.astype(np.float32) * ratio[..., None] * yy[..., None], 0, 255)

    fm = (mask > 128).astype(np.float32)
    fm_soft = cv2.GaussianBlur(fm, (0, 0), 0.55)
    near_fix = cv2.dilate(occ, np.ones((7, 7), np.uint8)) > 0
    fm = np.where(near_fix, fm, fm_soft)
    fm[occ > 128] = 0
    for x in range(w):
        fm[: int(round(horizon[x])), x] = 0

    after = np.clip(before.astype(np.float32) * (1 - fm[..., None]) + floor * fm[..., None], 0, 255).astype(np.uint8)
    after[occ > 0] = before[occ > 0]
    after[porc] = before[porc]

    # Force-fill remaining checker / pale floor holes
    for _ in range(28):
        diff = np.abs(after.astype(np.float32) - before.astype(np.float32)).mean(2)
        fill = (poly > 0) & (occ == 0) & ~porc & chk & (diff < 22)
        fill |= (
            (poly > 0) & (occ == 0) & ~porc & (diff < 12)
            & ~green & (bright > 5) & (bright < 248) & (sat < 90)
            & ~((fix_roi > 0) & (bright > 150) & (sat < 45))
        )
        # dark tile leftovers that are not foliage
        fill |= (poly > 0) & (occ == 0) & ~porc & black & ~green & (diff < 15) & (fix_roi == 0)
        if not fill.any():
            break
        after[fill] = np.clip(floor[fill], 0, 255).astype(np.uint8)
        after[occ > 0] = before[occ > 0]
        after[porc] = before[porc]

    for x in range(w):
        after[: int(round(horizon[x])), x] = before[: int(round(horizon[x])), x]
    after[porc] = before[porc]
    after[occ > 0] = before[occ > 0]
    # Absolute restore of all fixture ROI bright porcelain/pot
    restore = (fix_roi > 0) & (bright > 130) & (sat < 55) & ~chk & ~black
    after[restore] = before[restore]
    # Kill residual wood on porcelain: any warm-brown pixels inside toilet ROI that were bright porcelain in before
    warm = (after[:, :, 2].astype(np.float32) > after[:, :, 0].astype(np.float32) + 12) & (
        after.astype(np.float32).mean(2) < 150
    )
    wood_on = (toilet_roi > 0) & warm & (bright > 145) & (sat < 50) & ~chk
    after[wood_on] = before[wood_on]
    after[porc] = before[porc]

    diff = np.abs(after.astype(np.float32) - before.astype(np.float32)).mean(2)
    chk_in = (poly > 0) & chk & ~porc
    holes = ((poly > 0) & (occ == 0) & ~porc & (diff < 8) & (bright > 150) & (sat < 45) & (fix_roi == 0))
    print(
        "bath",
        "floor_y", int(np.where(diff > 8)[0].min()) if (diff > 8).any() else None,
        "cov", round(float((diff > 8).mean()), 4),
        "toiletΔ", round(float(diff[porc].mean()), 3) if porc.any() else 0,
        "checker", round(float(((chk_in) & (diff > 6)).sum() / max(1, chk_in.sum())), 3),
        "wallΔ", round(float(diff[:FLOOR_TOP].mean()), 4),
        "holes", int(holes.sum()),
        "potΔ", round(float(diff[plant_roi > 0].mean()), 2),
    )

    path = GALLERY / "after-bath-medium-oak.jpg"
    cv2.imwrite(str(path), after, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
    cv2.imwrite(str(WORK / "bath-after-final.jpg"), after, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
    cv2.imwrite(str(WORK / "bath-toilet-crop-final.jpg"),
                np.concatenate([before[640:900, 540:960], after[640:900, 540:960]], axis=1),
                [int(cv2.IMWRITE_JPEG_QUALITY), 95])
    print("wrote", path, path.stat().st_size)
    return path


if __name__ == "__main__":
    make_bath()
