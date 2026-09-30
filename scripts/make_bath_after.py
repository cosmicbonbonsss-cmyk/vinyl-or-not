#!/usr/bin/env python3
"""Rebuild gallery/after-bath-medium-oak.jpg (Denver bath).

- textures/medium-oak.jpg, near-orthographic paste (no extreme CUBIC smear)
- before-bath-checkered.jpg never written
- Floor to back wall under sink/window/toilet; toilet porcelain fully clear
- Lighting from heavily blurred L so checker pattern does not ghost into oak
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


def ortho(sheet, h, w, y_top, taper=0.03):
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
    bn = (
        cv2.dilate(black.astype(np.uint8) * 255, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (51, 51)))
        > 0
    )
    wn = (
        cv2.dilate(white.astype(np.uint8) * 255, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (51, 51)))
        > 0
    )
    chk = (black & wn) | (white & bn)
    green = (Gc > R + 12) & (Gc > B + 12)
    L = cv2.cvtColor(before, cv2.COLOR_BGR2LAB)[:, :, 0].astype(np.float32)
    lv = cv2.blur((L - cv2.blur(L, (9, 9))) ** 2, (9, 9))

    horizon = horizon_line(
        w,
        [
            (0, 780),
            (80, 768),
            (160, 752),
            (240, 738),
            (320, 728),
            (400, 722),
            (480, 718),
            (560, 716),
            (640, 715),
            (720, 715),
            (800, 716),
            (880, 720),
            (960, 726),
            (1040, 736),
            (1120, 750),
            (1199, 768),
        ],
    )
    FLOOR_TOP = int(horizon.min()) - 2
    poly = np.zeros((h, w), np.uint8)
    cv2.fillPoly(
        poly,
        [
            np.array(
                [(0, h - 1), (w - 1, h - 1)]
                + [(x, int(round(horizon[x]))) for x in range(w - 1, -1, -1)],
                np.int32,
            )
        ],
        255,
    )
    poly[:FLOOR_TOP] = 0

    toilet_hull = np.zeros((h, w), np.uint8)
    cv2.ellipse(toilet_hull, (750, 740), (132, 132), 0, 0, 360, 255, -1)
    cv2.ellipse(toilet_hull, (755, 820), (118, 92), 0, 0, 360, 255, -1)
    cv2.ellipse(toilet_hull, (755, 870), (128, 48), 0, 0, 360, 255, -1)
    cv2.rectangle(toilet_hull, (635, 575), (865, 735), 255, -1)
    toilet = ((toilet_hull > 0) & (bright > 125) & (sat < 55) & (lv < 280) & ~black).astype(
        np.uint8
    ) * 255
    toilet = cv2.morphologyEx(
        toilet, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11))
    )
    toilet = cv2.dilate(toilet, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    toilet[chk] = 0

    stool_hull = np.zeros((h, w), np.uint8)
    cv2.fillPoly(
        stool_hull, [np.array([[398, 778], [538, 778], [542, 842], [394, 842]], np.int32)], 255
    )
    for lx in (400, 420, 514, 534):
        cv2.rectangle(stool_hull, (lx - 3, 840), (lx + 3, 920), 255, -1)
    stool = ((stool_hull > 0) & (bright > 130) & (sat < 50) & ~chk).astype(np.uint8) * 255

    ped_hull = np.zeros((h, w), np.uint8)
    cv2.ellipse(ped_hull, (288, 870), (38, 24), 0, 0, 360, 255, -1)
    cv2.ellipse(ped_hull, (282, 810), (16, 38), 0, 0, 360, 255, -1)
    ped = ((ped_hull > 0) & (bright > 120) & (sat < 50) & ~chk).astype(np.uint8) * 255

    plant_hull = np.zeros((h, w), np.uint8)
    cv2.ellipse(plant_hull, (150, 845), (70, 36), 0, 0, 360, 255, -1)
    cv2.ellipse(plant_hull, (110, 770), (36, 54), -12, 0, 360, 255, -1)
    plant = (
        ((plant_hull > 0) & (((bright > 120) & (sat < 50)) | green) & ~chk)
    ).astype(np.uint8) * 255

    mask = poly.copy()
    mask[toilet > 0] = 0
    mask[stool > 0] = 0
    mask[ped > 0] = 0
    mask[plant > 0] = 0
    mask[(poly > 0) & chk] = 255
    mask[:FLOOR_TOP] = 0
    for _ in range(10):
        dil = cv2.dilate(mask, np.ones((5, 5), np.uint8))
        grow = (
            (dil > 0)
            & (poly > 0)
            & (toilet == 0)
            & (stool == 0)
            & (ped == 0)
            & (plant == 0)
            & (mask == 0)
        )
        grow &= ~((bright > 200) & (sat < 25))
        mask[grow] = 255

    occ = np.maximum(np.maximum(toilet, stool), np.maximum(ped, plant))
    occ[chk] = 0

    sheet = make_depth_planks(tex)
    warped = ortho(sheet, h, w, FLOOR_TOP - 6, taper=0.03)
    # Kill checker ghosting: light from heavily blurred L only
    L_light = cv2.GaussianBlur(L, (151, 151), 0)
    Lt = cv2.cvtColor(warped, cv2.COLOR_BGR2LAB)[:, :, 0].astype(np.float32)
    Lt_blur = cv2.GaussianBlur(Lt, (51, 51), 0)
    ratio = np.clip(L_light / np.maximum(Lt_blur, 1), 0.85, 1.15)
    yy = np.linspace(0.92, 1.08, h).astype(np.float32)[:, None]
    floor = np.clip(warped.astype(np.float32) * ratio[..., None] * yy[..., None], 0, 255)

    fm = (mask > 128).astype(np.float32)
    fm = cv2.GaussianBlur(fm, (0, 0), 0.8)
    fm[occ > 128] = 0
    fm[poly == 0] = 0
    fm[:FLOOR_TOP] = 0
    after = np.clip(
        before.astype(np.float32) * (1 - fm[..., None]) + floor * fm[..., None], 0, 255
    ).astype(np.uint8)
    after[occ > 0] = before[occ > 0]

    porc = ((toilet_hull > 0) & (bright > 125) & (sat < 55) & (lv < 300) & ~chk)
    after[porc] = before[porc]
    tu = porc.astype(np.uint8) * 255

    for _ in range(14):
        diff = np.abs(after.astype(np.float32) - before.astype(np.float32)).mean(2)
        fill = (poly > 0) & (tu == 0) & (diff < 16) & chk
        fill |= (
            (poly > 0)
            & (tu == 0)
            & (occ == 0)
            & (diff < 12)
            & ~green
            & (bright > 15)
            & (bright < 250)
            & (sat < 85)
        )
        fill &= ~((bright > 155) & (sat < 40) & (lv < 160) & ~chk)
        if not fill.any():
            break
        after[fill] = np.clip(floor[fill], 0, 255).astype(np.uint8)
        after[tu > 0] = before[tu > 0]
        after[occ > 0] = before[occ > 0]
    after[:FLOOR_TOP] = before[:FLOOR_TOP]
    after[porc] = before[porc]

    diff = np.abs(after.astype(np.float32) - before.astype(np.float32)).mean(2)
    chk_in = (poly > 0) & chk & (tu == 0)
    print(
        "bath",
        "floor_y",
        int(np.where(diff > 8)[0].min()) if (diff > 8).any() else None,
        "cov",
        round(float((diff > 8).mean()), 4),
        "toiletΔ",
        round(float(diff[porc].mean()), 3) if porc.any() else 0,
        "checker",
        round(float(((chk_in) & (diff > 6)).sum() / max(1, chk_in.sum())), 3),
        "wallΔ",
        round(float(diff[:FLOOR_TOP].mean()), 4),
    )

    path = GALLERY / "after-bath-medium-oak.jpg"
    cv2.imwrite(str(path), after, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
    cv2.imwrite(str(WORK / "bath-after-final.jpg"), after, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
    cv2.imwrite(
        str(WORK / "bath-toilet-crop-final.jpg"),
        np.concatenate([before[640:900, 540:960], after[640:900, 540:960]], axis=1),
        [int(cv2.IMWRITE_JPEG_QUALITY), 95],
    )
    print("wrote", path, path.stat().st_size)
    return path


if __name__ == "__main__":
    make_bath()
