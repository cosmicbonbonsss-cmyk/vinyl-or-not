#!/usr/bin/env python3
"""Rebuild gallery/after-bath-medium-oak.jpg only (Denver bath).

- Real textures/medium-oak.jpg → depth-running planks, crisp seams/grain
- Same room as before-bath-checkered.jpg (before file never written)
- Toilet porcelain fully restored from before (zero plank overlay)
- Planks low (floor mask starts ~y 722; wainscoting stays)
- Does not touch living/open afters or site chrome
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


def make_depth_planks(
    tex_bgr: np.ndarray,
    *,
    out_w: int = 5200,
    out_h: int = 4500,
    plank_w: int = 195,
    seam: int = 6,
) -> np.ndarray:
    """Planks run into room depth; crisp dark seams + natural grain."""
    t = cv2.rotate(tex_bgr, cv2.ROTATE_90_CLOCKWISE)
    t = cv2.resize(t, (t.shape[1] * 3, t.shape[0] * 3), interpolation=cv2.INTER_CUBIC)
    th, tw = t.shape[:2]
    floor = np.zeros((out_h, out_w, 3), dtype=np.uint8)
    seam_c = np.array([10, 14, 18], dtype=np.uint8)

    def sample(dw: int, dh: int) -> np.ndarray:
        band_w = max(28, min(tw // 3, tw - 1))
        sx = int(RNG.integers(0, max(1, tw - band_w)))
        band = t[:, sx : sx + band_w]
        oy = int(RNG.integers(0, th))
        tiled = np.concatenate([band] * 18, axis=0)
        need = max(dh + 80, th)
        while tiled.shape[0] - oy < need:
            tiled = np.concatenate([tiled, tiled], axis=0)
        board = cv2.resize(tiled[oy : oy + need], (dw, dh), interpolation=cv2.INTER_CUBIC)
        j = float(RNG.uniform(0.93, 1.07))
        return np.clip(board.astype(np.float32) * j, 0, 255).astype(np.uint8)

    x, col = 0, 0
    while x < out_w:
        pw = plank_w + int(RNG.integers(-8, 12))
        x2 = min(x + pw, out_w)
        stagger = int((col % 2) * out_h * 0.24) + int(RNG.integers(0, 40))
        y = -stagger
        while y < out_h:
            length = int(pw * float(RNG.uniform(55.0, 95.0)))
            y2 = y + length
            ya, yb = max(0, y), min(out_h, y2)
            if yb > ya:
                floor[ya:yb, x:x2] = sample(x2 - x, yb - ya)
                if 0 < yb < out_h:
                    floor[yb : min(out_h, yb + seam), x:x2] = seam_c
            y = y2 + seam
        if x2 < out_w:
            floor[:, x2 : min(out_w, x2 + seam)] = seam_c
        x = x2 + seam
        col += 1

    lab = cv2.cvtColor(floor, cv2.COLOR_BGR2LAB).astype(np.float32)
    lab[:, :, 0] = np.clip((lab[:, :, 0] - 128) * 1.18 + 136, 0, 255)
    return cv2.cvtColor(lab.astype(np.uint8), cv2.COLOR_LAB2BGR)


def make_bath() -> Path:
    before = cv2.imread(str(GALLERY / "before-bath-checkered.jpg"))
    assert before is not None
    h, w = before.shape[:2]
    tex = cv2.imread(str(TEXTURES / "medium-oak.jpg"))
    assert tex is not None

    bgr = before.astype(np.float32)
    bright = bgr.mean(axis=2)
    sat = bgr.max(axis=2) - bgr.min(axis=2)
    black = (bright < 100) & (sat < 40)
    local_mean = cv2.blur(bright, (7, 7))
    local_var = cv2.blur((bright - local_mean) ** 2, (7, 7))
    smooth = local_var < 200
    checker = local_var > 280
    green = (bgr[:, :, 1] > bgr[:, :, 2] + 12) & (bgr[:, :, 1] > bgr[:, :, 0] + 12)

    sheet = make_depth_planks(tex)

    # Toilet: geometric + porcelain grow (covers right base edge)
    toilet = np.zeros((h, w), np.uint8)
    cv2.ellipse(toilet, (748, 745), (148, 138), 0, 0, 360, 255, -1)
    cv2.ellipse(toilet, (755, 808), (138, 88), 0, 0, 360, 255, -1)
    cv2.ellipse(toilet, (760, 862), (155, 48), 0, 0, 360, 255, -1)
    cv2.ellipse(toilet, (800, 850), (100, 55), 10, 0, 360, 255, -1)
    cv2.rectangle(toilet, (640, 620), (860, 760), 255, -1)
    cv2.circle(toilet, (912, 818), 36, 255, -1)
    bbox = np.zeros((h, w), bool)
    bbox[610:900, 600:960] = True
    toilet_m = (toilet > 0) & ~black & (bright > 110) & (sat < 55)
    toilet_m = toilet_m & (smooth | ((local_var < 400) & (bright > 160)))
    toilet_u8 = toilet_m.astype(np.uint8) * 255
    for _ in range(6):
        dil = cv2.dilate(toilet_u8, np.ones((5, 5), np.uint8))
        add = (
            (dil > 0)
            & (toilet_u8 == 0)
            & bbox
            & ~black
            & (bright > 125)
            & (sat < 55)
            & (local_var < 450)
        )
        toilet_u8[add] = 255
    toilet_u8[(toilet_u8 > 0) & black] = 0
    toilet_u8[(toilet_u8 > 0) & checker & (bright < 170)] = 0

    stool = np.zeros((h, w), np.uint8)
    cv2.fillPoly(
        stool,
        [np.array([[398, 786], [538, 786], [540, 812], [396, 812]], np.int32)],
        255,
    )
    cv2.fillPoly(
        stool,
        [np.array([[388, 812], [548, 812], [550, 845], [386, 845]], np.int32)],
        255,
    )
    for lx in [392, 412, 522, 542]:
        cv2.rectangle(stool, (lx - 3, 845), (lx + 3, 899), 255, -1)
    stool_u8 = ((stool > 0) & smooth & ~black & ~checker & (bright > 135)).astype(
        np.uint8
    ) * 255
    stool_u8 = cv2.dilate(stool_u8, np.ones((3, 3), np.uint8))
    stool_u8[(stool_u8 > 0) & (black | checker)] = 0

    ped = np.zeros((h, w), np.uint8)
    cv2.ellipse(ped, (288, 868), (44, 30), 0, 0, 360, 255, -1)
    cv2.ellipse(ped, (282, 808), (20, 44), 0, 0, 360, 255, -1)
    ped_u8 = ((ped > 0) & smooth & ~black & ~checker & (bright > 125)).astype(
        np.uint8
    ) * 255
    ped_u8 = cv2.dilate(ped_u8, np.ones((3, 3), np.uint8))
    ped_u8[(ped_u8 > 0) & (black | checker)] = 0

    plant = np.zeros((h, w), np.uint8)
    cv2.ellipse(plant, (145, 835), (82, 46), 0, 0, 360, 255, -1)
    cv2.ellipse(plant, (105, 760), (46, 68), -12, 0, 360, 255, -1)
    plant_u8 = (
        (plant > 0) & ((smooth & (bright > 125)) | green) & ~black
    ).astype(np.uint8) * 255
    plant_u8 = cv2.dilate(plant_u8, np.ones((3, 3), np.uint8))
    plant_u8[(plant_u8 > 0) & black] = 0

    occ = np.maximum(np.maximum(toilet_u8, stool_u8), np.maximum(ped_u8, plant_u8))

    floor_mask = np.zeros((h, w), np.uint8)
    pts = np.array(
        [
            [0, h - 1],
            [w - 1, h - 1],
            [w - 1, 808],
            [1140, 786],
            [1040, 766],
            [940, 750],
            [840, 736],
            [740, 728],
            [640, 724],
            [540, 722],
            [440, 724],
            [340, 730],
            [240, 742],
            [140, 756],
            [60, 770],
            [0, 780],
        ],
        np.int32,
    )
    cv2.fillPoly(floor_mask, [pts], 255)
    floor_mask[:718, :] = 0
    floor_mask[occ > 0] = 0

    dst = np.array([[0, h - 1], [w - 1, h - 1], [1100, 726], [25, 770]], np.float32)
    src = np.array(
        [[80, 4300], [5120, 4300], [5120, 4300 - 195 * 14], [80, 4300 - 195 * 14]],
        np.float32,
    )
    warped = cv2.warpPerspective(
        sheet,
        cv2.getPerspectiveTransform(src, dst),
        (w, h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE,
    )

    L = cv2.cvtColor(before, cv2.COLOR_BGR2LAB).astype(np.float32)[:, :, 0]
    mean_L = float(L[floor_mask > 0].mean()) if (floor_mask > 0).any() else 128.0
    ratio = np.clip(cv2.GaussianBlur(L, (51, 51), 0) / max(mean_L, 1.0), 0.78, 1.26)
    alpha = floor_mask.astype(np.float32) / 255.0
    floor = np.clip(warped.astype(np.float32) * ratio[..., None], 0, 255)
    after = before.astype(np.float32) * (1.0 - alpha[..., None]) + floor * alpha[..., None]
    after = np.clip(after, 0, 255).astype(np.uint8)

    after[occ > 0] = before[occ > 0]
    after[toilet_u8 > 0] = before[toilet_u8 > 0]

    # Catch leftover porcelain in toilet bbox
    diff = np.abs(after.astype(np.float32) - before.astype(np.float32)).mean(axis=2)
    restore = (
        bbox
        & (bright > 130)
        & (sat < 55)
        & ~black
        & (diff > 8)
        & (local_var < 350)
    )
    near = cv2.dilate(toilet_u8, np.ones((35, 35), np.uint8)) > 0
    restore = restore & near
    after[restore] = before[restore]
    tu = np.maximum(toilet_u8, restore.astype(np.uint8) * 255)

    # Unsharp floor only for crisp seams/grain
    diff = np.abs(after.astype(np.float32) - before.astype(np.float32)).mean(axis=2)
    applied = (diff > 12) & (tu == 0) & (occ == 0)
    blurred = cv2.GaussianBlur(after, (0, 0), 0.65)
    sharp = cv2.addWeighted(after, 1.85, blurred, -0.85, 0)
    after[applied] = sharp[applied]
    after[tu > 0] = before[tu > 0]
    after[occ > 0] = before[occ > 0]

    # Metrics
    diff = np.abs(after.astype(np.float32) - before.astype(np.float32)).mean(axis=2)
    yy, xx = np.ogrid[:h, :w]
    porc = (
        ((xx - 750) / 155) ** 2 + ((yy - 780) / 145) ** 2 <= 1
    ) & smooth & (bright > 145)
    ys = np.where(diff > 12)[0]
    print(
        "bath",
        "floor_y",
        int(ys.min()) if len(ys) else None,
        int(ys.max()) if len(ys) else None,
        "cov",
        float((diff > 12).mean()),
        "toilet_porc_diff>15",
        int((diff[porc] > 15).sum()) if porc.any() else 0,
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
