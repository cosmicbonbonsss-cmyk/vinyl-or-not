#!/usr/bin/env python3
"""Rebuild gallery/after-bath-medium-oak.jpg only (Denver bath).

- textures/medium-oak.jpg → depth-running planks, CUBIC warp + unsharp
- before-bath-checkered.jpg never written
- Toilet porcelain fully restored (zero plank on porcelain core)
- Planks low (floor only; wainscoting untouched)
- Full floor poly minus tight fixtures — no white holes around pot/stool/toilet
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
    plank_w: int = 200,
    seam: int = 5,
) -> np.ndarray:
    t = cv2.rotate(tex_bgr, cv2.ROTATE_90_CLOCKWISE)
    t = cv2.resize(t, (t.shape[1] * 3, t.shape[0] * 3), interpolation=cv2.INTER_CUBIC)
    th, tw = t.shape[:2]
    floor = np.zeros((out_h, out_w, 3), dtype=np.uint8)
    seam_c = np.array([12, 16, 22], dtype=np.uint8)

    def sample(dw: int, dh: int) -> np.ndarray:
        band_w = max(32, min(tw // 3, tw - 1))
        sx = int(RNG.integers(0, max(1, tw - band_w)))
        band = t[:, sx : sx + band_w]
        oy = int(RNG.integers(0, th))
        tiled = np.concatenate([band, np.flip(band, 0), band, np.flip(band, 0)], axis=0)
        need = max(dh + 80, th)
        while tiled.shape[0] - oy < need:
            tiled = np.concatenate([tiled, np.flip(tiled, 0)], axis=0)
        board = cv2.resize(tiled[oy : oy + need], (dw, dh), interpolation=cv2.INTER_CUBIC)
        j = float(RNG.uniform(0.94, 1.06))
        return np.clip(board.astype(np.float32) * j, 0, 255).astype(np.uint8)

    x, col = 0, 0
    while x < out_w:
        pw = plank_w + int(RNG.integers(-6, 10))
        x2 = min(x + pw, out_w)
        stagger = int((col % 2) * out_h * 0.22) + int(RNG.integers(0, 36))
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
    lab[:, :, 0] = np.clip((lab[:, :, 0] - 128) * 1.22 + 134, 0, 255)
    return cv2.cvtColor(lab.astype(np.uint8), cv2.COLOR_LAB2BGR)


def unsharp(img: np.ndarray, amount: float = 1.35, sigma: float = 0.65) -> np.ndarray:
    blur = cv2.GaussianBlur(img, (0, 0), sigma)
    return cv2.addWeighted(img, 1.0 + amount, blur, -amount, 0)


def make_bath() -> Path:
    before = cv2.imread(str(GALLERY / "before-bath-checkered.jpg"))
    assert before is not None
    h, w = before.shape[:2]
    tex = cv2.imread(str(TEXTURES / "medium-oak.jpg"))
    assert tex is not None

    bgr = before.astype(np.float32)
    bright = bgr.mean(axis=2)
    sat = bgr.max(axis=2) - bgr.min(axis=2)
    L = cv2.cvtColor(before, cv2.COLOR_BGR2LAB)[:, :, 0].astype(np.float32)
    local_mean = cv2.blur(L, (9, 9))
    local_var = cv2.blur((L - local_mean) ** 2, (9, 9))
    black = (bright < 105) & (sat < 50)
    green = (bgr[:, :, 1] > bgr[:, :, 2] + 12) & (bgr[:, :, 1] > bgr[:, :, 0] + 12)
    smooth = local_var < 180

    # Full floor envelope — fill everything, then punch tight fixtures
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
    floor_mask[:720, :] = 0

    # ---- Tight occluders ----
    # Toilet: hull ∩ porcelain; tiny edge dilate; NEVER keep black tiles
    toilet_hull = np.zeros((h, w), np.uint8)
    cv2.ellipse(toilet_hull, (748, 748), (142, 132), 0, 0, 360, 255, -1)
    cv2.ellipse(toilet_hull, (752, 808), (128, 82), 0, 0, 360, 255, -1)
    cv2.ellipse(toilet_hull, (755, 858), (140, 40), 0, 0, 360, 255, -1)
    cv2.rectangle(toilet_hull, (650, 620), (845, 745), 255, -1)
    cv2.circle(toilet_hull, (912, 818), 26, 255, -1)

    toilet = (
        (toilet_hull > 0)
        & ~black
        & (bright > 130)
        & (sat < 52)
        & (smooth | ((local_var < 350) & (bright > 155)))
    ).astype(np.uint8) * 255
    core = np.zeros((h, w), np.uint8)
    cv2.ellipse(core, (750, 780), (115, 112), 0, 0, 360, 255, -1)
    cv2.ellipse(core, (755, 850), (105, 36), 0, 0, 360, 255, -1)
    toilet = np.maximum(
        toilet, ((core > 0) & ~black & (bright > 125)).astype(np.uint8) * 255
    )
    toilet = cv2.dilate(toilet, np.ones((3, 3), np.uint8))
    toilet[black] = 0

    # Stool: seat slabs + 4 thin legs (floor BETWEEN legs stays planks)
    stool = np.zeros((h, w), np.uint8)
    cv2.fillPoly(
        stool, [np.array([[402, 788], [534, 788], [536, 812], [400, 812]], np.int32)], 255
    )
    cv2.fillPoly(
        stool, [np.array([[392, 812], [544, 812], [546, 840], [390, 840]], np.int32)], 255
    )
    for lx in (396, 416, 518, 538):
        cv2.rectangle(stool, (lx - 4, 840), (lx + 4, 899), 255, -1)
    stool_u8 = ((stool > 0) & ~black & (bright > 145) & (sat < 48)).astype(np.uint8) * 255
    stool_u8 = cv2.dilate(stool_u8, np.ones((2, 2), np.uint8))
    stool_u8[black] = 0

    # Pedestal
    ped = np.zeros((h, w), np.uint8)
    cv2.ellipse(ped, (288, 868), (40, 26), 0, 0, 360, 255, -1)
    cv2.ellipse(ped, (282, 810), (17, 40), 0, 0, 360, 255, -1)
    ped_u8 = ((ped > 0) & ~black & (bright > 135) & (sat < 48)).astype(np.uint8) * 255
    ped_u8 = cv2.dilate(ped_u8, np.ones((3, 3), np.uint8))
    ped_u8[black] = 0

    # Plant pot (not surrounding floor)
    plant = np.zeros((h, w), np.uint8)
    cv2.ellipse(plant, (150, 840), (72, 38), 0, 0, 360, 255, -1)
    cv2.ellipse(plant, (110, 765), (40, 58), -12, 0, 360, 255, -1)
    plant_u8 = (
        ((plant > 0) & (((bright > 135) & (sat < 48)) | green) & ~black)
    ).astype(np.uint8) * 255
    plant_u8 = cv2.dilate(plant_u8, np.ones((3, 3), np.uint8))
    plant_u8[black] = 0

    occ = np.maximum(np.maximum(toilet, stool_u8), np.maximum(ped_u8, plant_u8))

    # Strip checkered floor tiles wrongly claimed by fixture dilate (white holes fix)
    white = (bright > 168) & (sat < 48)
    black_near = cv2.dilate(black.astype(np.uint8) * 255, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (25, 25))) > 0
    white_checker = white & black_near
    occ[black] = 0
    occ[white_checker] = 0
    # Restore toilet core after strip (porcelain is white but NOT checker-adjacent the same way)
    core2 = np.zeros((h, w), np.uint8)
    cv2.ellipse(core2, (750, 775), (110, 105), 0, 0, 360, 255, -1)
    cv2.ellipse(core2, (755, 848), (100, 34), 0, 0, 360, 255, -1)
    occ = np.maximum(occ, ((core2 > 0) & ~black & (bright > 130)).astype(np.uint8) * 255)

    floor_mask[occ > 0] = 0
    # Black checker tiles inside poly always get planks
    poly_only = np.zeros((h, w), np.uint8)
    cv2.fillPoly(poly_only, [pts], 255)
    poly_only[:720, :] = 0
    # Force checker tiles (black + white-adjacent-to-black) as floor — kills white holes
    white = (bright > 168) & (sat < 48)
    black_near = (
        cv2.dilate(black.astype(np.uint8) * 255, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (25, 25)))
        > 0
    )
    white_checker = white & black_near
    floor_mask[(poly_only > 0) & black] = 255
    floor_mask[(poly_only > 0) & white_checker] = 255
    floor_mask = cv2.morphologyEx(
        floor_mask,
        cv2.MORPH_CLOSE,
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)),
        iterations=1,
    )
    # Re-punch true fixture silhouettes (not checker)
    floor_mask[toilet > 0] = 0
    floor_mask[stool_u8 > 0] = 0
    floor_mask[ped_u8 > 0] = 0
    floor_mask[plant_u8 > 0] = 0
    floor_mask[(poly_only > 0) & black] = 255
    floor_mask[(poly_only > 0) & white_checker] = 255
    floor_mask[:720, :] = 0

    sheet = make_depth_planks(tex)
    dst = np.array([[0, h - 1], [w - 1, h - 1], [1100, 726], [25, 770]], np.float32)
    src = np.array(
        [[80, 4300], [5120, 4300], [5120, 4300 - 200 * 14], [80, 4300 - 200 * 14]],
        np.float32,
    )
    warped = cv2.warpPerspective(
        sheet,
        cv2.getPerspectiveTransform(src, dst),
        (w, h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE,
    )

    mean_L = float(L[floor_mask > 0].mean()) if (floor_mask > 0).any() else 128.0
    ratio = np.clip(cv2.GaussianBlur(L, (51, 51), 0) / max(mean_L, 1.0), 0.78, 1.26)
    alpha = floor_mask.astype(np.float32) / 255.0
    floor = np.clip(warped.astype(np.float32) * ratio[..., None], 0, 255)
    after = before.astype(np.float32) * (1.0 - alpha[..., None]) + floor * alpha[..., None]
    after = np.clip(after, 0, 255).astype(np.uint8)

    after[occ > 0] = before[occ > 0]
    after[toilet > 0] = before[toilet > 0]

    # Catch porcelain leftovers near toilet (smooth bright, not checker)
    bbox = np.zeros((h, w), bool)
    bbox[615:895, 620:940] = True
    diff = np.abs(after.astype(np.float32) - before.astype(np.float32)).mean(axis=2)
    near = cv2.dilate(toilet, np.ones((21, 21), np.uint8)) > 0
    restore = (
        bbox
        & near
        & (bright > 140)
        & (sat < 50)
        & ~black
        & (diff > 8)
        & (local_var < 300)
    )
    after[restore] = before[restore]
    tu = np.maximum(toilet, restore.astype(np.uint8) * 255)

    applied = (floor_mask > 0) & (tu == 0) & (occ == 0)
    # Also count black-forced floor
    applied = applied | ((poly_only > 0) & black & (tu == 0))
    sharp = unsharp(after, amount=1.35, sigma=0.65)
    after[applied] = sharp[applied]
    after[tu > 0] = before[tu > 0]
    after[occ > 0] = before[occ > 0]
    # Final: black tiles that are still before → force plank (in case occ ate them)
    still_black_hole = (poly_only > 0) & black & (
        np.abs(after.astype(np.float32) - before.astype(np.float32)).mean(axis=2) < 6
    )
    if still_black_hole.any():
        after[still_black_hole] = np.clip(
            warped[still_black_hole].astype(np.float32)
            * ratio[still_black_hole][..., None],
            0,
            255,
        ).astype(np.uint8)
        after[still_black_hole] = unsharp(after, amount=1.35, sigma=0.65)[still_black_hole]

    # Metrics
    diff = np.abs(after.astype(np.float32) - before.astype(np.float32)).mean(axis=2)
    yy, xx = np.ogrid[:h, :w]
    porc = (((xx - 750) / 120) ** 2 + ((yy - 780) / 110) ** 2 <= 1) & smooth & (bright > 150)
    ys = np.where(diff > 12)[0]
    print(
        "bath",
        "floor_y",
        int(ys.min()) if len(ys) else None,
        int(ys.max()) if len(ys) else None,
        "cov",
        float((diff > 12).mean()),
        "toilet_porc_meanΔ",
        float(diff[porc].mean()) if porc.any() else 0,
        "toilet_porc_diff>15",
        int((diff[porc] > 15).sum()) if porc.any() else 0,
        "black_covered",
        float(((black) & (poly_only > 0) & (diff > 12)).sum() / max(1, ((black) & (poly_only > 0)).sum())),
    )

    path = GALLERY / "after-bath-medium-oak.jpg"
    cv2.imwrite(str(path), after, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
    cv2.imwrite(str(WORK / "bath-after-final.jpg"), after, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
    cv2.imwrite(
        str(WORK / "bath-toilet-crop-final.jpg"),
        np.concatenate([before[640:900, 540:960], after[640:900, 540:960]], axis=1),
        [int(cv2.IMWRITE_JPEG_QUALITY), 95],
    )
    mask_viz = before.copy()
    m = (diff > 12)
    mask_viz[m] = (mask_viz[m].astype(np.float32) * 0.4 + np.array([0, 180, 255]) * 0.6).astype(
        np.uint8
    )
    cv2.imwrite(str(WORK / "bath-mask-final.jpg"), mask_viz, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
    print("wrote", path, path.stat().st_size)
    return path


if __name__ == "__main__":
    make_bath()
