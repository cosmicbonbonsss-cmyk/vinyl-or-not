#!/usr/bin/env python3
"""Rebuild gallery/after-bath-medium-oak.jpg (Denver bath).

Flat baseboard horizon; checker-grown floor; tight porcelain/legs/pot.
Checker punch never strips stool legs or pot body (white-near-black false chk).
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


def ortho(sheet, h, w, y_top, taper=0.08):
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


def horizon_line(w, pts, k=25):
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
    black = (bright < 100) & (sat < 55)
    white = (bright > 150) & (sat < 55)
    bn = cv2.dilate(black.astype(np.uint8) * 255, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (35, 35))) > 0
    wn = cv2.dilate(white.astype(np.uint8) * 255, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (35, 35))) > 0
    chk_raw = (black & wn) | (white & bn)
    green = (Gc > R + 12) & (Gc > B + 12)
    L = cv2.cvtColor(before, cv2.COLOR_BGR2LAB)[:, :, 0].astype(np.float32)
    lv = cv2.blur((L - cv2.blur(L, (9, 9))) ** 2, (9, 9))

    # Near-flat horizon at baseboard
    horizon = horizon_line(
        w,
        [
            (0, 748), (100, 738), (200, 730), (300, 724), (400, 720),
            (500, 718), (600, 717), (700, 718), (800, 720), (900, 724),
            (1000, 730), (1100, 738), (1199, 748),
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

    # Toilet porcelain — tight silhouette; punch only black tiles
    toilet_geo = np.zeros((h, w), np.uint8)
    cv2.ellipse(toilet_geo, (785, 855), (62, 36), 0, 0, 360, 255, -1)
    cv2.ellipse(toilet_geo, (782, 795), (54, 52), 0, 0, 360, 255, -1)
    cv2.ellipse(toilet_geo, (778, 735), (44, 38), 0, 0, 360, 255, -1)
    cv2.rectangle(toilet_geo, (722, 555), (838, 710), 255, -1)
    porc = (toilet_geo > 0) & (bright > 145) & (sat < 55) & (lv < 400) & ~black
    toilet = porc.astype(np.uint8) * 255
    toilet = cv2.morphologyEx(toilet, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11)))
    toilet[toilet_geo == 0] = 0
    toilet = cv2.dilate(toilet, np.ones((3, 3), np.uint8))
    toilet[toilet_geo == 0] = 0
    toilet[black] = 0

    # Stool body + thin white legs (do not strip white-near-black chk)
    stool = np.zeros((h, w), np.uint8)
    cv2.fillPoly(stool, [np.array([[400, 776], [538, 776], [542, 842], [396, 842]], np.int32)], 255)
    for lx0, lx1 in ((397, 412), (526, 545), (426, 440), (503, 518)):
        cv2.rectangle(stool, (lx0, 842), (lx1, 899), 255, -1)
    stool = ((stool > 0) & (bright > 105) & (sat < 65) & ~black).astype(np.uint8) * 255
    stool = cv2.morphologyEx(stool, cv2.MORPH_CLOSE, np.ones((7, 3), np.uint8))
    stool[black] = 0

    ped = np.zeros((h, w), np.uint8)
    cv2.ellipse(ped, (288, 878), (40, 22), 0, 0, 360, 255, -1)
    cv2.ellipse(ped, (282, 818), (15, 38), 0, 0, 360, 255, -1)
    ped = ((ped > 0) & (bright > 125) & (sat < 55) & ~black).astype(np.uint8) * 255

    plant = np.zeros((h, w), np.uint8)
    cv2.ellipse(plant, (148, 865), (60, 38), 0, 0, 360, 255, -1)
    cv2.ellipse(plant, (148, 845), (58, 30), 0, 0, 360, 255, -1)
    cv2.ellipse(plant, (115, 770), (36, 55), -12, 0, 360, 255, -1)
    plant_keep = ((plant > 0) & ((((bright > 85) & (sat < 65)) | green) & ~black)).astype(np.uint8) * 255
    plant_keep = cv2.morphologyEx(plant_keep, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))
    plant_keep[black] = 0

    trash = np.zeros((h, w), np.uint8)
    cv2.ellipse(trash, (868, 788), (22, 18), 0, 0, 360, 255, -1)
    trash = ((trash > 0) & (bright > 145) & (sat < 50) & ~black).astype(np.uint8) * 255

    fixtures = np.maximum(np.maximum(toilet, stool), np.maximum(np.maximum(ped, plant_keep), trash))
    chk = chk_raw & (fixtures == 0) & (poly > 0)

    mask = np.zeros((h, w), np.uint8)
    mask[(poly > 0) & (fixtures == 0)] = 255
    mask[chk] = 255
    mask[fixtures > 0] = 0
    for _ in range(40):
        dil = cv2.dilate(mask, np.ones((5, 5), np.uint8))
        grow = (dil > 0) & (poly > 0) & (fixtures == 0) & (mask == 0) & ~green
        if not grow.any():
            break
        mask[grow] = 255
    mask[chk] = 255
    mask[fixtures > 0] = 0
    for x in range(w):
        mask[: int(round(horizon[x])), x] = 0
    mask[h - 40 :, :] = 255
    mask[fixtures > 0] = 0
    for x in range(w):
        mask[: int(round(horizon[x])), x] = 0

    sheet = make_depth_planks(tex)
    warped = ortho(sheet, h, w, max(FLOOR_TOP - 4, 0), taper=0.08)
    L_light = cv2.GaussianBlur(L, (151, 151), 0)
    Lt = cv2.cvtColor(warped, cv2.COLOR_BGR2LAB)[:, :, 0].astype(np.float32)
    ratio = np.clip(L_light / np.maximum(cv2.GaussianBlur(Lt, (51, 51), 0), 1), 0.85, 1.15)
    yy = np.linspace(0.92, 1.08, h).astype(np.float32)[:, None]
    floor = np.clip(warped.astype(np.float32) * ratio[..., None] * yy[..., None], 0, 255)

    fm = (mask > 128).astype(np.float32)
    near_fix = cv2.dilate(fixtures, np.ones((5, 5), np.uint8)) > 0
    soft = cv2.GaussianBlur(fm, (0, 0), 0.35)
    fm = np.where(near_fix, fm, soft)
    fm[fixtures > 128] = 0
    for x in range(w):
        fm[: int(round(horizon[x])), x] = 0

    after = np.clip(before.astype(np.float32) * (1 - fm[..., None]) + floor * fm[..., None], 0, 255).astype(np.uint8)
    after[fixtures > 0] = before[fixtures > 0]

    for _ in range(45):
        diff = np.abs(after.astype(np.float32) - before.astype(np.float32)).mean(2)
        fill = (poly > 0) & (fixtures == 0) & chk & (diff < 25)
        fill |= (poly > 0) & (fixtures == 0) & (diff < 12) & ~green & (bright > 5) & (bright < 248) & (sat < 90)
        fill |= (poly > 0) & (fixtures == 0) & black & ~green & (diff < 18)
        if not fill.any():
            break
        after[fill] = np.clip(floor[fill], 0, 255).astype(np.uint8)
        after[fixtures > 0] = before[fixtures > 0]

    for x in range(w):
        after[: int(round(horizon[x])), x] = before[: int(round(horizon[x])), x]
    after[fixtures > 0] = before[fixtures > 0]
    after[toilet > 0] = before[toilet > 0]
    after[stool > 0] = before[stool > 0]
    after[plant_keep > 0] = before[plant_keep > 0]

    warm = (after[:, :, 2].astype(np.float32) > after[:, :, 0].astype(np.float32) + 12) & (
        after.astype(np.float32).mean(2) < 150
    )
    after[(toilet > 0) & warm] = before[(toilet > 0) & warm]
    after[toilet > 0] = before[toilet > 0]

    diff = np.abs(after.astype(np.float32) - before.astype(np.float32)).mean(2)
    unch = (diff < 10) & (bright > 140) & (sat < 50) & (poly > 0) & (fixtures == 0)
    print(
        "bath",
        "floor_y", int(np.where(diff > 8)[0].min()) if (diff > 8).any() else None,
        "cov", round(float((diff > 8).mean()), 4),
        "toiletΔ", round(float(diff[toilet > 0].mean()), 3) if (toilet > 0).any() else 0,
        "unch_pale", int(unch.sum()),
        "wallΔ", round(float(diff[:FLOOR_TOP].mean()), 4),
    )

    path = GALLERY / "after-bath-medium-oak.jpg"
    cv2.imwrite(str(path), after, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
    cv2.imwrite(str(WORK / "bath-after-final.jpg"), after, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
    print("wrote", path, path.stat().st_size)
    return path


if __name__ == "__main__":
    make_bath()
