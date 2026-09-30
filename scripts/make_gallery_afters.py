#!/usr/bin/env python3
"""Gallery AFTER composites: site plank textures, perspective-warped onto floor.

Constraints:
- Never paint over the bath toilet (restore full toilet from before).
- Keep plank overlay at true floor height; do not run planks up the walls.
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
) -> np.ndarray:
    t = tex_bgr
    if rotate_tex90:
        t = cv2.rotate(t, cv2.ROTATE_90_CLOCKWISE)
    th, tw = t.shape[:2]
    t = cv2.resize(t, (tw * 2, th * 2), interpolation=cv2.INTER_CUBIC)
    th, tw = t.shape[:2]
    floor = np.zeros((out_h, out_w, 3), dtype=np.uint8)
    seam_color = np.array([16, 20, 26], dtype=np.uint8)

    def sample_board(dst_w, dst_h, along="x"):
        if along == "x":
            band_h = max(12, min(th // 3, th - 1))
            sy = int(RNG.integers(0, max(1, th - band_h)))
            band = t[sy : sy + band_h]
            ox = int(RNG.integers(0, tw))
            tiled = np.concatenate([band] * 8, axis=1)
            need = max(dst_w + 32, tw)
            if tiled.shape[1] - ox < need:
                tiled = np.concatenate([tiled, tiled], axis=1)
            patch = tiled[:, ox : ox + need]
            board = cv2.resize(patch, (dst_w, dst_h), interpolation=cv2.INTER_LINEAR)
        else:
            band_w = max(12, min(tw // 3, tw - 1))
            sx = int(RNG.integers(0, max(1, tw - band_w)))
            band = t[:, sx : sx + band_w]
            oy = int(RNG.integers(0, th))
            tiled = np.concatenate([band] * 8, axis=0)
            need = max(dst_h + 32, th)
            if tiled.shape[0] - oy < need:
                tiled = np.concatenate([tiled, tiled], axis=0)
            patch = tiled[oy : oy + need]
            board = cv2.resize(patch, (dst_w, dst_h), interpolation=cv2.INTER_LINEAR)
        jitter = float(RNG.uniform(0.88, 1.12))
        return np.clip(board.astype(np.float32) * jitter, 0, 255).astype(np.uint8)

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
    lab[:, :, 0] = np.clip((lab[:, :, 0] - 128) * 1.04 + 128, 0, 255)
    return cv2.cvtColor(lab.astype(np.uint8), cv2.COLOR_LAB2BGR)


def warp_floor(sheet, dst_hw, src_quad, dst_quad):
    h, w = dst_hw
    M = cv2.getPerspectiveTransform(src_quad.astype(np.float32), dst_quad.astype(np.float32))
    return cv2.warpPerspective(sheet, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)


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


def composite(before, warped, floor_mask, occluder_mask=None, lighting=True):
    fm = floor_mask.astype(np.float32) / 255.0
    if occluder_mask is not None:
        fm = fm * (1.0 - occluder_mask.astype(np.float32) / 255.0)
    m = fm[..., None]
    floor = warped.astype(np.float32)
    if lighting:
        floor = np.clip(floor * luminance_ratio(before, (fm * 255).astype(np.uint8))[..., None], 0, 255)
    out = before.astype(np.float32) * (1.0 - m) + floor * m
    return np.clip(out, 0, 255).astype(np.uint8)


def save_qa(name, before, floor_mask, occ, after, sheet=None):
    applied = floor_mask > 128
    if occ is not None:
        applied = applied & (occ < 128)
    cv2.imwrite(str(WORK / f"{name}-mask.png"), (applied.astype(np.uint8) * 255))
    ov = before.copy()
    ov[applied] = (ov[applied].astype(np.float32) * 0.4 + np.array([0, 150, 255]) * 0.6).astype(np.uint8)
    cv2.imwrite(str(WORK / f"{name}-mask-ov.jpg"), ov, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
    cv2.imwrite(str(WORK / f"{name}-after.jpg"), after, [int(cv2.IMWRITE_JPEG_QUALITY), 94])
    if sheet is not None:
        cv2.imwrite(str(WORK / f"{name}-sheet.jpg"), sheet[:1200, :1200], [int(cv2.IMWRITE_JPEG_QUALITY), 92])


# ---- Living: horizontal warm-oak planks, full floor to baseboards ----
def make_living():
    before = cv2.imread(str(GALLERY / "before-living-empty.jpg"))
    h, w = before.shape[:2]
    tex = cv2.imread(str(TEXTURES / "warm-oak.jpg"))
    sheet = make_plank_floor(
        tex, out_w=5200, out_h=3000, plank_w=210, seam=3,
        grain_along="x", rotate_tex90=True, length_mult=(55.0, 90.0),
    )
    # Stay on floor only — top edge = baseboard under windows (~y 490–540)
    floor_poly = [
        (0, h - 1), (w - 1, h - 1), (w - 1, 700),
        (1160, 640), (1100, 600), (1020, 560), (940, 535),
        (860, 518), (800, 508), (740, 502), (680, 498),
        (600, 496), (500, 494), (400, 492), (300, 491),
        (200, 494), (100, 512), (0, 542),
    ]
    floor_mask = poly_mask((h, w), floor_poly, feather=1)
    dst = np.array([[0, h - 1], [w - 1, h - 1], [1080, 500], [40, 535]], np.float32)
    src = np.array([[50, 2900], [5150, 2900], [5150, 2900 - 210 * 6], [50, 2900 - 210 * 6]], np.float32)
    warped = warp_floor(sheet, (h, w), src, dst)
    after = composite(before, warped, floor_mask, None, lighting=True)
    save_qa("living", before, floor_mask, None, after, sheet)
    path = GALLERY / "after-living-warm-oak.jpg"
    cv2.imwrite(str(path), after, [int(cv2.IMWRITE_JPEG_QUALITY), 94])
    ys = np.where(floor_mask > 128)[0]
    print("living", path, "floor_y", int(ys.min()), "-", int(ys.max()), "cov", float((floor_mask > 128).mean()))
    return after


# ---- Bath: medium oak; toilet MUST stay fully visible; floor stays low ----
def bath_toilet_occluder(before):
    """Hard protect: entire toilet silhouette restored from before."""
    h, w = before.shape[:2]
    occ = np.zeros((h, w), np.uint8)
    # Broad toilet hull (tank + bowl + base) — generous so no plank paints porcelain
    cv2.ellipse(occ, (730, 780), (175, 160), 0, 0, 360, 255, -1)
    cv2.rectangle(occ, (580, 620), (880, 899), 255, -1)
    cv2.ellipse(occ, (740, 860), (155, 70), 0, 0, 360, 255, -1)
    # Bin next to toilet
    cv2.circle(occ, (910, 820), 32, 255, -1)
    # Keep only bright porcelain / white-ish inside hull (don't block floor beside toilet)
    bgr = before.astype(np.float32)
    bright = bgr.mean(axis=2)
    sat = bgr.max(axis=2) - bgr.min(axis=2)
    porcelain = (bright > 155) & (sat < 45)
    # Also keep soft shadows on toilet (slightly darker white)
    near_white = (bright > 130) & (sat < 50) & (bgr[:, :, 0] > 120)
    keep = (occ > 0) & (porcelain | near_white)
    # Force-keep core toilet ellipse regardless (safety against under-mask)
    core = np.zeros((h, w), np.uint8)
    cv2.ellipse(core, (735, 800), (140, 130), 0, 0, 360, 255, -1)
    cv2.ellipse(core, (740, 860), (130, 55), 0, 0, 360, 255, -1)
    out = np.maximum(keep.astype(np.uint8) * 255, core)
    # Dilate so plank can't kiss the porcelain edge
    out = cv2.dilate(out, np.ones((7, 7), np.uint8))
    out = cv2.GaussianBlur(out, (5, 5), 0)
    return out


def bath_other_occluders(before):
    h, w = before.shape[:2]
    occ = np.zeros((h, w), np.uint8)
    # plant pot + lower leaves
    cv2.ellipse(occ, (150, 830), (95, 55), 0, 0, 360, 255, -1)
    cv2.ellipse(occ, (100, 750), (60, 85), -15, 0, 360, 255, -1)
    # pedestal
    cv2.ellipse(occ, (288, 868), (48, 35), 0, 0, 360, 255, -1)
    cv2.ellipse(occ, (280, 810), (26, 50), 0, 0, 360, 255, -1)
    # stool whole
    cv2.fillPoly(occ, [np.array([(375, 785), (555, 785), (565, 895), (365, 895)], np.int32)], 255)
    occ[:700, :] = 0
    bgr = before.astype(np.float32)
    bright = bgr.mean(axis=2)
    sat = bgr.max(axis=2) - bgr.min(axis=2)
    green = (bgr[:, :, 1] > bgr[:, :, 2] + 12) & (bgr[:, :, 1] > bgr[:, :, 0] + 12)
    pale = (bright > 150) & (sat < 45)
    keep = (occ > 0) & (pale | green)
    out = keep.astype(np.uint8) * 255
    out = cv2.dilate(out, np.ones((3, 3), np.uint8))
    out = cv2.GaussianBlur(out, (3, 3), 0)
    return out


def make_bath():
    before = cv2.imread(str(GALLERY / "before-bath-checkered.jpg"))
    h, w = before.shape[:2]
    tex = cv2.imread(str(TEXTURES / "medium-oak.jpg"))
    sheet = make_plank_floor(
        tex, out_w=4500, out_h=4000, plank_w=195, seam=3,
        grain_along="y", rotate_tex90=True, length_mult=(50.0, 85.0),
    )
    # Floor ONLY below wainscoting base (~y 730+) — leave wall clearly visible above
    floor_poly = [
        (0, h - 1), (w - 1, h - 1), (w - 1, 812),
        (1120, 782), (1000, 758), (880, 742), (740, 734),
        (600, 730), (460, 732), (320, 740), (160, 756), (0, 772),
    ]
    floor_mask = poly_mask((h, w), floor_poly, feather=0)
    # Hard clamp: nothing above y=728 gets floor (wall safety)
    floor_mask[:728, :] = 0

    toilet = bath_toilet_occluder(before)
    other = bath_other_occluders(before)
    occ = np.maximum(toilet, other)

    dst = np.array([[0, h - 1], [w - 1, h - 1], [1080, 732], [40, 762]], np.float32)
    src = np.array([[80, 3850], [4420, 3850], [4420, 3850 - 195 * 7], [80, 3850 - 195 * 7]], np.float32)
    warped = warp_floor(sheet, (h, w), src, dst)
    after = composite(before, warped, floor_mask, occ, lighting=True)

    # Final safety: force-restore any toilet-region pixels that still changed
    toilet_force = np.zeros((h, w), np.uint8)
    cv2.ellipse(toilet_force, (735, 790), (155, 145), 0, 0, 360, 255, -1)
    bgr = before.astype(np.float32)
    bright = bgr.mean(axis=2)
    sat = bgr.max(axis=2) - bgr.min(axis=2)
    restore = (toilet_force > 0) & ((bright > 140) & (sat < 50))
    after[restore] = before[restore]

    save_qa("bath", before, floor_mask, occ, after, sheet)
    # toilet crop QA
    cv2.imwrite(
        str(WORK / "bath-toilet-crop.jpg"),
        np.concatenate([before[650:900, 550:950], after[650:900, 550:950]], axis=1),
        [int(cv2.IMWRITE_JPEG_QUALITY), 94],
    )
    path = GALLERY / "after-bath-medium-oak.jpg"
    cv2.imwrite(str(path), after, [int(cv2.IMWRITE_JPEG_QUALITY), 94])
    applied = (floor_mask > 128) & (occ < 128)
    ys = np.where(applied)[0]
    # Measure toilet paint: diff in toilet core
    diff = np.abs(after.astype(float) - before.astype(float)).mean(axis=2)
    tcore = np.zeros((h, w), bool)
    yy, xx = np.ogrid[:h, :w]
    tcore = ((xx - 735) / 140) ** 2 + ((yy - 800) / 130) ** 2 <= 1
    painted = (diff > 10) & tcore & (bright > 150)
    print(
        "bath", path,
        "floor_y", int(ys.min()) if len(ys) else None, "-", int(ys.max()) if len(ys) else None,
        "cov", float(applied.mean()),
        "toilet_painted_px", int(painted.sum()),
    )
    return after


# ---- Open plan: warm oak into depth; floor stays on carpet plane ----
def make_open():
    before = cv2.imread(str(GALLERY / "before-open-carpet.jpg"))
    h, w = before.shape[:2]
    tex = cv2.imread(str(TEXTURES / "warm-oak.jpg"))
    sheet = make_plank_floor(
        tex, out_w=5000, out_h=4500, plank_w=185, seam=3,
        grain_along="y", rotate_tex90=False, length_mult=(52.0, 88.0),
    )
    # Floor envelope — do not climb furniture/walls; back edge ~y 400–420 at far carpet
    floor_poly = [
        (0, h - 1), (w - 1, h - 1), (w - 1, 500),
        (1100, 460), (980, 435), (860, 420), (740, 414),
        (640, 412), (560, 420), (480, 450), (400, 510),
        (320, 575), (230, 650), (120, 720), (0, 770),
    ]
    floor_mask = poly_mask((h, w), floor_poly, feather=1)
    # Wall safety: no overlay in top 38% of frame
    floor_mask[: int(h * 0.38), :] = 0

    # Occluders: furniture (not carpet)
    bgr = before.astype(np.float32)
    brightness = bgr.mean(axis=2)
    sat = bgr.max(axis=2) - bgr.min(axis=2)
    carpet = ((brightness > 155) & (sat < 48)) | ((brightness > 125) & (brightness <= 155) & (sat < 38))
    occ = np.zeros((h, w), np.uint8)
    cv2.fillPoly(occ, [np.array([(0, 450), (400, 440), (520, 565), (500, h - 1), (0, h - 1)], np.int32)], 255)
    cv2.rectangle(occ, (300, 450), (415, 640), 255, -1)
    for cx, cy, r in [(770, 530, 48), (860, 510, 48), (950, 530, 48), (800, 610, 38), (900, 620, 38), (980, 600, 38)]:
        cv2.circle(occ, (cx, cy), r, 255, -1)
    cv2.fillPoly(occ, [np.array([(460, 415), (650, 410), (730, 470), (700, 555), (510, 560), (440, 485)], np.int32)], 255)
    cv2.ellipse(occ, (510, 470), (48, 62), 0, 0, 360, 255, -1)
    # Keep furniture pixels; clear carpet between legs
    furniture = (occ > 0) & (~carpet)
    occ = furniture.astype(np.uint8) * 255
    dining = np.zeros((h, w), np.uint8)
    cv2.rectangle(dining, (700, 500), (1100, 700), 255, -1)
    occ[(dining > 0) & carpet] = 0
    for cx, cy, r in [(772, 575, 8), (852, 555, 8), (938, 575, 8), (814, 642, 7), (894, 655, 7), (974, 630, 7)]:
        cv2.circle(occ, (cx, cy), r, 255, -1)
    occ = cv2.GaussianBlur(occ, (5, 5), 0)

    dst = np.array([[0, h - 1], [w - 1, h - 1], [1020, 415], [80, 730]], np.float32)
    src = np.array([[120, 4350], [4880, 4350], [4880, 4350 - 185 * 9], [120, 4350 - 185 * 9]], np.float32)
    warped = warp_floor(sheet, (h, w), src, dst)
    after = composite(before, warped, floor_mask, occ, lighting=True)
    save_qa("open", before, floor_mask, occ, after, sheet)
    path = GALLERY / "after-open-warm-oak.jpg"
    cv2.imwrite(str(path), after, [int(cv2.IMWRITE_JPEG_QUALITY), 94])
    applied = (floor_mask > 128) & (occ < 128)
    ys = np.where(applied)[0]
    print("open", path, "floor_y", int(ys.min()) if len(ys) else None, "-", int(ys.max()) if len(ys) else None, "cov", float(applied.mean()))
    return after


def main():
    make_living()
    make_bath()
    make_open()
    print("done")


if __name__ == "__main__":
    main()
