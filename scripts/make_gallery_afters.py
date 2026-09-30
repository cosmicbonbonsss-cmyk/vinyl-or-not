#!/usr/bin/env python3
"""Gallery AFTER composites: site plank textures onto floor.

- Living/Open: warm-oak.jpg; Bath delegated to make_bath_after.
- Living: LAB recolor of original floor (keeps plank perspective; no CUBIC smear).
- Open: rembg+solid armchairs; seat tops only (no floor ovals); floor to fireplace.
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
    """Warm-oak floor on open-plan carpet. Rembg armchairs; continuous dining; floor to fireplace."""
    before = cv2.imread(str(GALLERY / "before-open-carpet.jpg"))
    h, w = before.shape[:2]
    tex = cv2.imread(str(TEXTURES / "warm-oak.jpg"))
    bgr = before.astype(np.float32)
    bright = bgr.mean(2)
    sat = bgr.max(2) - bgr.min(2)
    Bb, Rr = bgr[:, :, 0], bgr[:, :, 2]
    Bb2, Gg2, Rr2 = bgr[:, :, 0], bgr[:, :, 1], bgr[:, :, 2]

    horizon = horizon_line(
        w,
        [
            (0, 540), (50, 522), (120, 502), (200, 488), (280, 474),
            (360, 462), (440, 452), (520, 446), (600, 442), (680, 440),
            (760, 444), (840, 454), (920, 474), (1000, 498), (1080, 528), (1199, 562),
        ],
        k=17,
    )
    env = np.zeros((h, w), np.uint8)
    cv2.fillPoly(
        env,
        [np.array([(0, h - 1), (w - 1, h - 1)] + [(x, int(round(horizon[x]))) for x in range(w - 1, -1, -1)], np.int32)],
        255,
    )
    for x in range(w):
        env[: int(round(horizon[x])), x] = 0

    furn = np.zeros((h, w), np.uint8)
    alpha_path = Path(__file__).resolve().parent / "masks" / "open-rembg-alpha.png"
    alpha = cv2.imread(str(alpha_path), 0)
    if alpha is None:
        raise FileNotFoundError(f"missing rembg alpha mask: {alpha_path}")
    arm = (alpha > 80).astype(np.uint8) * 255
    keep = np.zeros((h, w), np.uint8)
    keep[380:800, 0:540] = 255
    arm = cv2.bitwise_and(arm, keep)
    arm = cv2.morphologyEx(arm, cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8))
    arm = cv2.dilate(arm, np.ones((5, 5), np.uint8))
    cv2.fillPoly(
        arm,
        [np.array([
            (0, 440), (200, 418), (280, 455), (325, 525), (335, 630), (330, 720), (305, 765),
            (240, 785), (120, 792), (20, 788), (0, 770),
        ], np.int32)],
        255,
    )
    cv2.fillPoly(
        arm,
        [np.array([
            (250, 410), (400, 400), (475, 435), (500, 505), (490, 585), (455, 635), (375, 648),
            (285, 615), (255, 535), (248, 470),
        ], np.int32)],
        255,
    )
    table_roi = np.zeros((h, w), np.uint8)
    cv2.fillPoly(
        table_roi,
        [np.array([
            (455, 405), (560, 400), (575, 445), (570, 515), (545, 545), (490, 550), (460, 510), (450, 450),
        ], np.int32)],
        255,
    )
    arm[(table_roi > 0) & (alpha > 80)] = 255
    dark = (table_roi > 0) & (Rr > Bb + 8) & (bright > 40) & (bright < 110) & (sat > 18) & (sat < 70)
    lamp = (table_roi > 0) & (bright > 170) & (sat < 40)
    arm[dark | lamp] = 255
    core = (alpha > 80).astype(np.uint8) * 255
    core = cv2.bitwise_and(core, keep)
    core = cv2.dilate(core, np.ones((9, 9), np.uint8))
    core[dark | lamp] = 255
    arm[(arm > 0) & (core == 0) & (bright > 145) & (sat < 42)] = 0
    arm[:, 600:] = 0  # living furniture stays left of fireplace corridor
    furn = np.maximum(furn, arm)

    blue_roi = np.zeros((h, w), np.uint8)
    cv2.fillPoly(
        blue_roi,
        [np.array([(530, 395), (580, 392), (592, 435), (582, 470), (545, 478), (525, 440)], np.int32)],
        255,
    )
    furn[(blue_roi > 0) & (Bb2 > Rr2 + 12) & (Bb2 > Gg2 + 5) & (bright > 35) & (bright < 140)] = 255
    plant = np.zeros((h, w), np.uint8)
    cv2.ellipse(plant, (548, 428), (15, 30), 0, 0, 360, 255, -1)
    cv2.ellipse(plant, (548, 456), (11, 9), 0, 0, 360, 255, -1)
    furn[(plant > 0) & (((Gg2 > Rr2 + 10) & (Gg2 > Bb2 + 8)) | (bright < 80))] = 255

    pale = (bright > 125) & (bright < 205) & (sat < 48)
    wood = (Rr > Bb + 10) & (bright > 30) & (bright < 125) & (sat > 12) & (sat < 90)
    for cx, cy, rx, ry, bt, lb in [
        (806, 548, 32, 16, 448, 630), (898, 560, 32, 16, 458, 645), (978, 545, 32, 16, 442, 628),
        (768, 472, 30, 14, 390, 550), (858, 460, 30, 14, 380, 538), (948, 472, 30, 14, 390, 550),
    ]:
        back = np.zeros((h, w), np.uint8)
        cv2.rectangle(back, (cx - rx + 6, bt), (cx + rx - 6, cy - ry + 2), 255, -1)
        furn[(back > 0) & pale] = 255
        seat = np.zeros((h, w), np.uint8)
        cv2.ellipse(seat, (cx, cy), (rx - 2, max(ry - 2, 6)), 0, 0, 360, 255, -1)
        seat[cy:, :] = 0  # seat surface only — no floor ovals
        furn[(seat > 0) & pale] = 255
        for dx in (-rx + 12, rx - 14, -rx + 17, rx - 19):
            leg = np.zeros((h, w), np.uint8)
            cv2.rectangle(leg, (cx + dx - 2, cy + 10), (cx + dx + 2, lb), 255, -1)
            furn[(leg > 0) & wood] = 255
    tt = np.zeros((h, w), np.uint8)
    cv2.ellipse(tt, (885, 498), (150, 36), 0, 0, 360, 255, -1)
    furn[(tt > 0) & (bright < 125) & (Rr > Bb + 2)] = 255

    mask = env.copy()
    mask[furn > 0] = 0
    sm = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    near = cv2.dilate(furn, np.ones((13, 13), np.uint8)) > 0
    mask = np.where(near, mask, sm)
    mask[furn > 0] = 0
    for x in range(w):
        mask[: int(round(horizon[x])), x] = 0

    dz = np.zeros((h, w), bool)
    dz[490:775, 695:1145] = True
    mask[dz & (env > 0) & (furn == 0)] = 255
    fz = np.zeros((h, w), bool)
    fz[440:560, 450:850] = True
    mask[fz & (env > 0) & (furn == 0)] = 255
    lab = cv2.cvtColor(before, cv2.COLOR_BGR2LAB).astype(np.float32)
    seeds = [(600, 760), (900, 640), (700, 500), (550, 520), (1000, 590), (650, 480), (720, 490)]
    cmu = np.mean([lab[y, x] for x, y in seeds], 0)
    cd = np.sqrt(((lab - cmu) ** 2).sum(2))
    mask[(env > 0) & (furn == 0) & (cd < 30) & (bright > 95) & (sat < 55)] = 255
    mask[furn > 0] = 0
    for x in range(w):
        mask[: int(round(horizon[x])), x] = 0

    sheet = make_planks(tex, along="y", plank_w=125, out_w=4200, out_h=4000)
    warped = ortho(sheet, h, w, int(horizon.min()) - 2, taper=0.14)
    L0 = lab[:, :, 0]
    Lt = cv2.cvtColor(warped, cv2.COLOR_BGR2LAB)[:, :, 0].astype(np.float32)
    ratio = np.clip(
        cv2.GaussianBlur(L0, (81, 81), 0) / np.maximum(cv2.GaussianBlur(Lt, (81, 81), 0), 1),
        0.82, 1.18,
    )
    m = mask > 128
    shift = 100.0 / max(float(L0[m].mean()) if m.any() else 100.0, 1)
    yy = np.linspace(0.0, 1.0, h).astype(np.float32)[:, None]
    depth = 0.86 + 0.22 * yy
    ao = np.ones((h, w), np.float32)
    ao -= 0.11 * (cv2.dilate(furn, np.ones((23, 23), np.uint8)).astype(np.float32) / 255)
    floor = np.clip(warped.astype(np.float32) * (ratio * shift)[..., None] * depth[..., None] * ao[..., None], 0, 255)

    fm = (mask > 128).astype(np.float32)
    fm[furn > 0] = 0
    for x in range(w):
        fm[: int(round(horizon[x])), x] = 0
    soft = cv2.GaussianBlur(fm, (0, 0), 0.35)
    fm = np.where(near, fm, soft)
    fm[furn > 0] = 0

    after = np.clip(before.astype(np.float32) * (1 - fm[..., None]) + floor * fm[..., None], 0, 255).astype(np.uint8)
    after[furn > 0] = before[furn > 0]
    for _ in range(40):
        diff = np.abs(after.astype(np.float32) - before.astype(np.float32)).mean(2)
        below = np.zeros((h, w), bool)
        for x in range(w):
            below[int(round(horizon[x])) :, x] = True
        still = below & (furn == 0) & (diff < 15) & (cd < 32) & (bright > 90) & (sat < 55)
        still |= (dz | fz) & (furn == 0) & (diff < 18) & below
        if not still.any():
            break
        after[still] = np.clip(floor[still], 0, 255).astype(np.uint8)
        after[furn > 0] = before[furn > 0]
    after[furn > 0] = before[furn > 0]
    for x in range(w):
        after[: int(round(horizon[x])), x] = before[: int(round(horizon[x])), x]

    save_qa("open", before, mask, after, furn)
    path = GALLERY / "after-open-warm-oak.jpg"
    cv2.imwrite(str(path), after, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
    applied = (mask > 128) & (furn < 128)
    ys = np.where(applied)[0]
    print(
        "open", path,
        "floor_y", int(ys.min()) if len(ys) else None, "-", int(ys.max()) if len(ys) else None,
        "cov", round(float(applied.mean()), 4),
    )
    return after


def main():
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--living", action="store_true", help="also rebuild living (default: skip)")
    ap.add_argument("--open-only", action="store_true")
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()
    if args.all:
        make_living()
        make_open()
        from make_bath_after import make_bath
        make_bath()
    elif args.open_only:
        make_open()
    else:
        # Default: open only (living left unchanged; bath has its own script)
        if args.living:
            make_living()
        make_open()
    print("done")




if __name__ == "__main__":
    main()
