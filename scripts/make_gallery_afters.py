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
    """Warm-oak floor on open-plan carpet. Full chair silhouettes; gentle perspective."""
    before = cv2.imread(str(GALLERY / "before-open-carpet.jpg"))
    h, w = before.shape[:2]
    tex = cv2.imread(str(TEXTURES / "warm-oak.jpg"))
    # Depth-running planks with gentle taper (reads as receding floor)
    sheet = make_planks(tex, along="y", plank_w=130, out_w=4000, out_h=3800)
    bgr = before.astype(np.float32)
    bright = bgr.mean(2)
    sat = bgr.max(2) - bgr.min(2)
    Bb, Rr = bgr[:, :, 0], bgr[:, :, 2]

    horizon = horizon_line(
        w,
        [
            (0, 728), (60, 720), (140, 700), (220, 665), (300, 615),
            (380, 558), (460, 508), (540, 468), (620, 442), (700, 422),
            (780, 412), (860, 410), (940, 418), (1020, 438), (1100, 472), (1199, 522),
        ],
    )
    env = np.zeros((h, w), np.uint8)
    cv2.fillPoly(
        env,
        [np.array([(0, h - 1), (w - 1, h - 1)] + [(x, int(round(horizon[x]))) for x in range(w - 1, -1, -1)], np.int32)],
        255,
    )
    env[: int(h * 0.36)] = 0
    for x in range(w):
        env[: int(round(horizon[x])), x] = 0

    # Armchairs — cover full bases including legs; morph-smooth
    arm = np.zeros((h, w), np.uint8)
    cv2.fillPoly(
        arm,
        [np.array([
            (0, 450), (245, 432), (318, 470), (350, 540), (348, 690),
            (318, 742), (260, 762), (125, 768), (0, 752),
        ], np.int32)],
        255,
    )
    cv2.fillPoly(
        arm,
        [np.array([
            (280, 435), (435, 428), (505, 458), (525, 522), (512, 610),
            (468, 658), (385, 662), (298, 622), (278, 530),
        ], np.int32)],
        255,
    )
    cv2.rectangle(arm, (395, 445), (525, 550), 255, -1)
    cv2.fillPoly(
        arm,
        [np.array([(448, 405), (660, 398), (740, 462), (715, 558), (535, 562), (442, 492)], np.int32)],
        255,
    )
    arm = cv2.morphologyEx(arm, cv2.MORPH_CLOSE, np.ones((11, 11), np.uint8))
    arm = cv2.morphologyEx(arm, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    # Trim a few px from bottom so floor meets fabric without blocky island of carpet
    arm_bottom = arm.copy()
    arm_bottom[:700] = 0
    arm_bottom = cv2.erode(arm_bottom, np.ones((5, 5), np.uint8))
    arm[700:] = arm_bottom[700:]

    # Dining chairs: seat + back + wood legs only (no pale-carpet hole masks)
    chair_defs = [
        (806, 552, 38, 24, 450),
        (898, 565, 38, 24, 465),
        (978, 550, 38, 24, 450),
        (768, 475, 36, 26, 392),
        (858, 464, 36, 24, 382),
        (948, 476, 36, 26, 392),
    ]
    seat_core = np.zeros((h, w), np.uint8)
    chair_back = np.zeros((h, w), np.uint8)
    leg_geo = np.zeros((h, w), np.uint8)
    for cx, cy, rx, ry, back_top in chair_defs:
        cv2.ellipse(seat_core, (cx, cy), (rx, ry), 0, 0, 360, 255, -1)
        # backrest above seat — do not extend to floor
        cv2.rectangle(chair_back, (cx - rx + 6, back_top), (cx + rx - 6, cy - ry + 4), 255, -1)
        for dx in (-rx + 12, rx - 16):
            cv2.rectangle(leg_geo, (cx + dx - 3, cy + 4), (cx + dx + 3, min(h - 1, cy + ry + 70)), 255, -1)
        for dx in (-rx + 16, rx - 20):
            cv2.rectangle(leg_geo, (cx + dx - 3, cy - 2), (cx + dx + 3, min(h - 1, cy + ry + 50)), 255, -1)

    pale_fab = (bright > 135) & (bright < 205) & (sat < 50)
    wood_leg = (Rr > Bb + 10) & (bright > 40) & (bright < 140) & (sat > 18) & (sat < 90)
    # ONLY pale fabric inside seat ellipses — never restore carpet (that punches white holes)
    seats = ((seat_core > 0) & pale_fab).astype(np.uint8) * 255
    seats = cv2.morphologyEx(seats, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    backs = ((chair_back > 0) & pale_fab & (bright < 195)).astype(np.uint8) * 255
    legs = ((leg_geo > 0) & wood_leg).astype(np.uint8) * 255
    legs = cv2.morphologyEx(legs, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))

    table = np.zeros((h, w), np.uint8)
    cv2.ellipse(table, (880, 500), (170, 45), 0, 0, 360, 255, -1)
    table_keep = ((table > 0) & (bright < 125) & (Rr > Bb + 5)).astype(np.uint8) * 255

    furn = np.maximum(np.maximum(np.maximum(arm, seats), np.maximum(backs, legs)), table_keep)

    # Floor: entire env below horizon minus furniture (force continuous oak)
    mask = env.copy()
    mask[furn > 0] = 0
    # Force pale carpet anywhere in env that's not furniture
    carpet = (env > 0) & (furn == 0) & (bright > 85) & (bright < 240) & (sat < 80)
    mask[carpet] = 255
    # Dining under-table force
    dzone = np.zeros((h, w), bool)
    dzone[440:780, 630:1145] = True
    mask[dzone & (furn == 0) & (bright > 90) & (sat < 70)] = 255
    mask[furn > 0] = 0
    for x in range(w):
        mask[: int(round(horizon[x])), x] = 0
    for _ in range(12):
        dil = cv2.dilate(mask, np.ones((3, 3), np.uint8))
        grow = (dil > 0) & (env > 0) & (furn == 0) & (mask == 0) & (bright > 90) & (sat < 75)
        if not grow.any():
            break
        mask[grow] = 255
    mask[furn > 0] = 0
    for x in range(w):
        mask[: int(round(horizon[x])), x] = 0

    warped = ortho(sheet, h, w, int(horizon.min()) - 2, taper=0.14)
    L0 = cv2.cvtColor(before, cv2.COLOR_BGR2LAB)[:, :, 0].astype(np.float32)
    Lt = cv2.cvtColor(warped, cv2.COLOR_BGR2LAB)[:, :, 0].astype(np.float32)
    ratio = np.clip(
        cv2.GaussianBlur(L0, (61, 61), 0) / np.maximum(cv2.GaussianBlur(Lt, (61, 61), 0), 1),
        0.78, 1.22,
    )
    m = mask > 128
    shift = 92.0 / max(float(L0[m].mean()) if m.any() else 92.0, 1)
    floor = np.clip(warped.astype(np.float32) * (ratio * shift * 0.88)[..., None], 0, 255)

    fm = m.astype(np.float32)
    fm[furn > 128] = 0
    soft = cv2.GaussianBlur(fm, (0, 0), 0.5)
    near_f = cv2.dilate(furn, np.ones((5, 5), np.uint8)) > 0
    fm = np.where(near_f, fm, soft)
    fm[furn > 128] = 0

    after = np.clip(before.astype(np.float32) * (1 - fm[..., None]) + floor * fm[..., None], 0, 255).astype(np.uint8)
    after[furn > 0] = before[furn > 0]

    for _ in range(16):
        diff = np.abs(after.astype(np.float32) - before.astype(np.float32)).mean(2)
        below = np.zeros((h, w), bool)
        for x in range(w):
            below[int(round(horizon[x])) :, x] = True
        still = (
            below & (furn == 0) & (diff < 20) & (bright > 90) & (bright < 235) & (sat < 70)
        )
        # don't fill seat cores
        still &= seat_core == 0
        if not still.any():
            break
        after[still] = np.clip(floor[still], 0, 255).astype(np.uint8)
        after[furn > 0] = before[furn > 0]

    after[seats > 0] = before[seats > 0]
    after[backs > 0] = before[backs > 0]
    after[legs > 0] = before[legs > 0]
    after[arm > 0] = before[arm > 0]
    after[table_keep > 0] = before[table_keep > 0]

    save_qa("open", before, mask, after, furn)
    path = GALLERY / "after-open-warm-oak.jpg"
    cv2.imwrite(str(path), after, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
    applied = (mask > 128) & (furn < 128)
    ys = np.where(applied)[0]
    print("open", path, "floor_y", int(ys.min()) if len(ys) else None, "-", int(ys.max()) if len(ys) else None, "cov", round(float(applied.mean()), 4))
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
