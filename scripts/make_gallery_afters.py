#!/usr/bin/env python3
"""Gallery AFTER composites: site plank textures onto floor.

- Living/Open: warm-oak.jpg; Bath delegated to make_bath_after.
- Living: LAB recolor of original floor (keeps plank perspective; no CUBIC smear).
- Open: near-orthographic paste; dining force-fill; seat-local pale protect only.
- Floor mask capped at wall–floor junctions; no climb onto walls/baseboards.
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
RNG = np.random.default_rng(17)


def make_planks(tex, out_w=4500, out_h=3200, plank_w=145, along="x"):
    t = tex.copy()
    if along == "x":
        t = cv2.rotate(t, cv2.ROTATE_90_CLOCKWISE)
    t = cv2.resize(
        t, (int(t.shape[1] * 1.8), int(t.shape[0] * 1.8)), interpolation=cv2.INTER_AREA
    )
    lab = cv2.cvtColor(t, cv2.COLOR_BGR2LAB).astype(np.float32)
    L = lab[:, :, 0]
    m = float(L.mean())
    lab[:, :, 0] = np.clip((L - m) * 0.58 + m + 10, 0, 255)
    t = cv2.cvtColor(lab.astype(np.uint8), cv2.COLOR_LAB2BGR)
    th, tw = t.shape[:2]
    floor = np.zeros((out_h, out_w, 3), np.uint8)
    seam = np.array([38, 44, 52], np.uint8)
    if along == "x":
        y, row = 0, 0
        while y < out_h:
            pw = plank_w + int(RNG.integers(-6, 10))
            y2 = min(y + pw, out_h)
            stagger = int((row % 2) * out_w * 0.3) + int(RNG.integers(0, 70))
            x = -stagger
            while x < out_w:
                length = int(pw * float(RNG.uniform(65, 115)))
                x2 = x + length
                xa, xb = max(0, x), min(out_w, x2)
                if xb > xa:
                    bh = max(32, min(th // 2, th - 1))
                    sy = int(RNG.integers(0, max(1, th - bh)))
                    band = t[sy : sy + bh]
                    ox = int(RNG.integers(0, tw))
                    tiled = np.concatenate(
                        [band, np.flip(band, 1), band, np.flip(band, 1), band], 1
                    )
                    need = max(xb - xa + 40, tw)
                    while tiled.shape[1] - ox < need:
                        tiled = np.concatenate([tiled, np.flip(tiled, 1)], 1)
                    board = cv2.resize(
                        tiled[:, ox : ox + need],
                        (xb - xa, y2 - y),
                        interpolation=cv2.INTER_LINEAR,
                    )
                    j = float(RNG.uniform(0.98, 1.02))
                    floor[y:y2, xa:xb] = np.clip(board.astype(np.float32) * j, 0, 255).astype(
                        np.uint8
                    )
                    if 0 < xb < out_w:
                        floor[y:y2, xb : min(out_w, xb + 2)] = seam
                x = x2 + 2
            if y2 < out_h:
                floor[y2 : min(out_h, y2 + 2), :] = seam
            y = y2 + 2
            row += 1
    else:
        x, col = 0, 0
        while x < out_w:
            pw = plank_w + int(RNG.integers(-6, 10))
            x2 = min(x + pw, out_w)
            stagger = int((col % 2) * out_h * 0.3) + int(RNG.integers(0, 70))
            y = -stagger
            while y < out_h:
                length = int(pw * float(RNG.uniform(65, 115)))
                y2 = y + length
                ya, yb = max(0, y), min(out_h, y2)
                if yb > ya:
                    bw = max(32, min(tw // 2, tw - 1))
                    sx = int(RNG.integers(0, max(1, tw - bw)))
                    band = t[:, sx : sx + bw]
                    oy = int(RNG.integers(0, th))
                    tiled = np.concatenate(
                        [band, np.flip(band, 0), band, np.flip(band, 0), band], 0
                    )
                    need = max(yb - ya + 40, th)
                    while tiled.shape[0] - oy < need:
                        tiled = np.concatenate([tiled, np.flip(tiled, 0)], 0)
                    board = cv2.resize(
                        tiled[oy : oy + need],
                        (x2 - x, yb - ya),
                        interpolation=cv2.INTER_LINEAR,
                    )
                    j = float(RNG.uniform(0.98, 1.02))
                    floor[ya:yb, x:x2] = np.clip(board.astype(np.float32) * j, 0, 255).astype(
                        np.uint8
                    )
                    if 0 < yb < out_h:
                        floor[yb : min(out_h, yb + 2), x:x2] = seam
                y = y2 + 2
            if x2 < out_w:
                floor[:, x2 : min(out_w, x2 + 2)] = seam
            x = x2 + 2
            col += 1
    return floor


def ortho(sheet, h, w, y_top, taper=0.035):
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


def horizon_line(w, pts, k=11):
    xs = np.array([p[0] for p in pts], float)
    ys = np.array([p[1] for p in pts], float)
    hzn = np.interp(np.arange(w), xs, ys)
    return np.convolve(np.pad(hzn, (k // 2, k // 2), "edge"), np.ones(k) / k, "valid")


def save_qa(name, before, mask, after, occ=None):
    applied = mask > 128
    if occ is not None:
        applied = applied & (occ < 128)
    cv2.imwrite(str(WORK / f"{name}-mask.png"), (applied.astype(np.uint8) * 255))
    ov = before.copy()
    ov[applied] = (ov[applied].astype(np.float32) * 0.4 + np.array([0, 160, 255]) * 0.6).astype(
        np.uint8
    )
    cv2.imwrite(str(WORK / f"{name}-mask-ov.jpg"), ov, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
    cv2.imwrite(str(WORK / f"{name}-after.jpg"), after, [int(cv2.IMWRITE_JPEG_QUALITY), 94])


def make_living():
    """LAB-recolor original floor to warm-oak — no perspective warp (no smear)."""
    before = cv2.imread(str(GALLERY / "before-living-empty.jpg"))
    h, w = before.shape[:2]
    tex = cv2.imread(str(TEXTURES / "warm-oak.jpg"))
    tlab = cv2.cvtColor(tex, cv2.COLOR_BGR2LAB).astype(np.float32)
    tgt_a = float(tlab[:, :, 1].mean())
    tgt_b = float(tlab[:, :, 2].mean())
    tgt_L = 98.0
    PANEL = 528

    # True junctions from hline QA: under-window ~550–560 floor start;
    # horizon sits just above junction (~534–542) so recolor fills the gold strip.
    horizon = horizon_line(
        w,
        [
            (0, 532),
            (40, 530),
            (100, 532),
            (180, 534),
            (280, 536),
            (380, 538),
            (480, 540),
            (580, 542),
            (680, 544),
            (760, 552),
            (840, 564),
            (920, 578),
            (1000, 590),
            (1080, 600),
            (1140, 610),
            (1199, 618),
        ],
    )
    mask = np.zeros((h, w), np.uint8)
    cv2.fillPoly(
        mask,
        [
            np.array(
                [(0, h - 1), (w - 1, h - 1)]
                + [(x, int(round(horizon[x]))) for x in range(w - 1, -1, -1)],
                np.int32,
            )
        ],
        255,
    )
    mask[:PANEL] = 0
    for x in range(w):
        mask[: int(round(horizon[x])), x] = 0

    bgr = before.astype(np.float32)
    bright = bgr.mean(2)
    sat = bgr.max(2) - bgr.min(2)
    lab = cv2.cvtColor(before, cv2.COLOR_BGR2LAB).astype(np.float32)
    chroma = np.sqrt((lab[:, :, 1] - 128) ** 2 + (lab[:, :, 2] - 128) ** 2)
    wallish = (chroma < 9) & (lab[:, :, 0] > 162) & (sat < 12)
    radiator = (bright > 182) & (sat < 14)
    mask[wallish | radiator] = 0

    m = mask > 128
    L0, A0, B0 = lab[:, :, 0], lab[:, :, 1], lab[:, :, 2]
    L_blur = cv2.GaussianBlur(L0, (21, 21), 0)
    detail = L0 - L_blur
    L_mean = float(L0[m].mean()) if m.any() else 140.0
    L_new = np.clip(L_blur * (tgt_L / max(L_mean, 1.0)) + detail * 0.75, 0, 255)
    A_new = np.clip(A0 * 0.05 + tgt_a * 0.95, 0, 255)
    B_new = np.clip(B0 * 0.05 + tgt_b * 0.95, 0, 255)
    recolor = lab.copy()
    recolor[:, :, 0] = L_new
    recolor[:, :, 1] = A_new
    recolor[:, :, 2] = B_new

    sheet = make_planks(tex, along="x", plank_w=140)
    grain = ortho(sheet, h, w, int(horizon.min()) - 2, taper=0.02).astype(np.float32)
    gL = cv2.cvtColor(grain.astype(np.uint8), cv2.COLOR_BGR2LAB)[:, :, 0].astype(np.float32)
    g_detail = gL - cv2.GaussianBlur(gL, (25, 25), 0)
    gw = (np.linspace(0.12, 0.20, h).astype(np.float32))[:, None]
    recolor[:, :, 0] = np.clip(recolor[:, :, 0] + g_detail * gw, 0, 255)
    guided = cv2.cvtColor(recolor.astype(np.uint8), cv2.COLOR_LAB2BGR).astype(np.float32)

    fm = m.astype(np.float32)
    fm = cv2.GaussianBlur(fm, (0, 0), 0.55)
    fm[wallish | radiator] = 0
    fm[:PANEL] = 0
    after = np.clip(before.astype(np.float32) * (1 - fm[..., None]) + guided * fm[..., None], 0, 255).astype(
        np.uint8
    )

    Rr, Bb = bgr[:, :, 2], bgr[:, :, 0]
    wood = (Rr > Bb + 5) & (bright > 30) & (bright < 225) & (sat > 8)
    below = np.zeros((h, w), bool)
    for x in range(w):
        below[int(round(horizon[x])) :, x] = True
    diff = np.abs(after.astype(np.float32) - before.astype(np.float32)).mean(2)
    still = below & wood & (diff < 14) & ~wallish & ~radiator
    still[:PANEL] = False
    if still.any():
        after[still] = np.clip(guided[still], 0, 255).astype(np.uint8)
    diff = np.abs(after.astype(np.float32) - before.astype(np.float32)).mean(2)
    after[(wallish | radiator) & (diff > 2)] = before[(wallish | radiator) & (diff > 2)]
    after[:PANEL] = before[:PANEL]

    save_qa("living", before, mask, after)
    path = GALLERY / "after-living-warm-oak.jpg"
    cv2.imwrite(str(path), after, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
    ys = np.where(mask > 128)[0]
    print(
        "living",
        path,
        "floor_y",
        int(ys.min()) if len(ys) else None,
        "-",
        int(ys.max()) if len(ys) else None,
        "cov",
        round(float((mask > 128).mean()), 4),
    )
    return after


def make_open():
    before = cv2.imread(str(GALLERY / "before-open-carpet.jpg"))
    h, w = before.shape[:2]
    tex = cv2.imread(str(TEXTURES / "warm-oak.jpg"))
    sheet = make_planks(tex, along="y", plank_w=125, out_w=4000, out_h=3800)
    bgr = before.astype(np.float32)
    bright = bgr.mean(2)
    sat = bgr.max(2) - bgr.min(2)
    Bb, Rr = bgr[:, :, 0], bgr[:, :, 2]

    horizon = horizon_line(
        w,
        [
            (0, 725),
            (60, 718),
            (140, 698),
            (220, 662),
            (300, 612),
            (380, 555),
            (460, 505),
            (540, 465),
            (620, 438),
            (700, 418),
            (780, 408),
            (860, 406),
            (940, 414),
            (1020, 434),
            (1100, 468),
            (1199, 518),
        ],
    )
    env = np.zeros((h, w), np.uint8)
    cv2.fillPoly(
        env,
        [
            np.array(
                [(0, h - 1), (w - 1, h - 1)]
                + [(x, int(round(horizon[x]))) for x in range(w - 1, -1, -1)],
                np.int32,
            )
        ],
        255,
    )
    env[: int(h * 0.38)] = 0
    for x in range(w):
        env[: int(round(horizon[x])), x] = 0

    arm = np.zeros((h, w), np.uint8)
    cv2.fillPoly(
        arm,
        [
            np.array(
                [
                    (0, 470),
                    (230, 450),
                    (300, 485),
                    (335, 555),
                    (330, 670),
                    (300, 725),
                    (250, 745),
                    (110, 750),
                    (0, 735),
                ],
                np.int32,
            )
        ],
        255,
    )
    cv2.fillPoly(
        arm,
        [
            np.array(
                [
                    (290, 448),
                    (420, 440),
                    (485, 468),
                    (508, 528),
                    (492, 600),
                    (450, 642),
                    (375, 644),
                    (308, 608),
                    (288, 538),
                ],
                np.int32,
            )
        ],
        255,
    )
    cv2.rectangle(arm, (408, 455), (512, 540), 255, -1)
    cv2.fillPoly(
        arm,
        [np.array([(458, 415), (650, 408), (728, 468), (698, 548), (528, 552), (448, 492)], np.int32)],
        255,
    )

    # Seat protect: geometric ellipses ONLY (pale carpet must NOT be treated as seats)
    seat_geo = np.zeros((h, w), np.uint8)
    for cx, cy, rx, ry in [
        (768, 475, 42, 36),
        (858, 464, 42, 34),
        (948, 476, 40, 36),
        (806, 552, 40, 32),
        (898, 565, 40, 32),
        (978, 550, 40, 32),
    ]:
        cv2.ellipse(seat_geo, (cx, cy), (rx, ry), 0, 0, 360, 255, -1)
    cv2.ellipse(seat_geo, (880, 436), (148, 22), 0, 0, 360, 255, -1)
    seat = ((seat_geo > 0) & (bright > 168) & (sat < 65)).astype(np.uint8) * 255
    seat = cv2.dilate(seat, np.ones((3, 3), np.uint8))

    dining = np.zeros((h, w), np.uint8)
    cv2.fillPoly(
        dining,
        [
            np.array(
                [
                    (640, 755),
                    (655, 580),
                    (700, 510),
                    (760, 475),
                    (850, 455),
                    (950, 460),
                    (1040, 495),
                    (1110, 560),
                    (1135, 720),
                    (1120, 770),
                    (640, 770),
                ],
                np.int32,
            )
        ],
        255,
    )

    mask = np.maximum(env, dining)
    mask[arm > 0] = 0
    mask[seat > 0] = 0
    carpet = ((env > 0) | (dining > 0)) & (arm == 0) & (seat == 0) & (bright > 85) & (bright < 240) & (
        sat < 85
    )
    mask[carpet] = 255
    # Force dining carpet rectangle (between chair legs) into mask
    drect = np.zeros((h, w), bool)
    drect[450:760, 640:1135] = True
    force = drect & (arm == 0) & (seat == 0) & (bright > 85) & (bright < 240) & (sat < 90)
    mask[force] = 255
    mask[arm > 0] = 0
    mask[seat > 0] = 0
    for x in range(w):
        mask[: int(round(horizon[x])), x] = 0

    wood_leg = (
        (Rr > Bb + 14)
        & (bright > 42)
        & (bright < 128)
        & (sat > 22)
        & (sat < 85)
        & (dining > 0)
    )
    near = cv2.dilate(seat_geo, np.ones((20, 20), np.uint8)) > 0
    leg = ((wood_leg & near).astype(np.uint8) * 255)
    leg = cv2.erode(leg, np.ones((2, 2), np.uint8))
    leg[(bright > 170) & (sat < 55)] = 0

    warped = ortho(sheet, h, w, int(horizon.min()) - 2, taper=0.035)
    L0 = cv2.cvtColor(before, cv2.COLOR_BGR2LAB)[:, :, 0].astype(np.float32)
    Lt = cv2.cvtColor(warped, cv2.COLOR_BGR2LAB)[:, :, 0].astype(np.float32)
    ratio = np.clip(
        cv2.GaussianBlur(L0, (61, 61), 0) / np.maximum(cv2.GaussianBlur(Lt, (61, 61), 0), 1),
        0.78,
        1.22,
    )
    m = mask > 128
    shift = 92.0 / max(float(L0[m].mean()) if m.any() else 92.0, 1)
    floor = np.clip(warped.astype(np.float32) * (ratio * shift * 0.88)[..., None], 0, 255)
    occ = np.maximum(arm, seat)
    fm = m.astype(np.float32)
    fm[occ > 128] = 0
    after = np.clip(
        before.astype(np.float32) * (1 - fm[..., None]) + floor * fm[..., None], 0, 255
    ).astype(np.uint8)
    after[occ > 0] = before[occ > 0]
    after[leg > 0] = before[leg > 0]

    for _ in range(12):
        diff = np.abs(after.astype(np.float32) - before.astype(np.float32)).mean(2)
        below = np.zeros((h, w), bool)
        for x in range(w):
            below[int(round(horizon[x])) :, x] = True
        still = (
            ((dining > 0) | (env > 0) | force)
            & (arm == 0)
            & (seat == 0)
            & (leg == 0)
            & below
            & (diff < 24)
            & (bright > 80)
            & (bright < 245)
            & (sat < 90)
        )
        if not still.any():
            break
        after[still] = np.clip(floor[still], 0, 255).astype(np.uint8)
        after[occ > 0] = before[occ > 0]
        after[leg > 0] = before[leg > 0]
    after[seat > 0] = before[seat > 0]

    save_qa("open", before, mask, after, occ)
    path = GALLERY / "after-open-warm-oak.jpg"
    cv2.imwrite(str(path), after, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
    applied = (mask > 128) & (occ < 128)
    ys = np.where(applied)[0]
    print(
        "open",
        path,
        "floor_y",
        int(ys.min()) if len(ys) else None,
        "-",
        int(ys.max()) if len(ys) else None,
        "cov",
        round(float(applied.mean()), 4),
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
