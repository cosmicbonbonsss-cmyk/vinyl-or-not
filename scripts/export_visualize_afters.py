#!/usr/bin/env python3
"""Offline Visualize-faithful floor overlay (matches visualize.js rebuildFloor).

Bilinear subdivided quad (seg=48), tiled UVs, MeshBasicMaterial opacity 0.92.
No furniture masking — honest Visualize behavior.
"""
from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
GALLERY = ROOT / "gallery"
TEXTURES = ROOT / "textures"
OUT_DIR = ROOT / "scripts" / "_viz_exports"
OUT_DIR.mkdir(parents=True, exist_ok=True)

SEG = 48
OPACITY = 0.92
# Default tile-scale=6; warm-oak/medium-oak repeat=[6,6] => baseU=baseV=6
TILE_SCALE = 6.0
REPEAT = (6.0, 6.0)


def bilinear_point(fl, fr, br, bl, tx, ty):
    """Same as visualize.js: bottom=FL->FR, top=BL->BR, p=bottom->top."""
    bottom = fl * (1 - tx) + fr * tx
    top = bl * (1 - tx) + br * tx
    return bottom * (1 - ty) + top * ty


def build_mesh(corners_xy):
    """corners_xy: list of 4 (x,y) image-pixel coords FL,FR,BR,BL."""
    fl, fr, br, bl = [np.array(c, dtype=np.float64) for c in corners_xy]
    base_u = (REPEAT[0] / 6.0) * TILE_SCALE
    base_v = (REPEAT[1] / 6.0) * TILE_SCALE
    positions = []
    uvs = []
    for j in range(SEG + 1):
        ty = j / SEG
        for i in range(SEG + 1):
            tx = i / SEG
            p = bilinear_point(fl, fr, br, bl, tx, ty)
            positions.append(p)
            uvs.append((tx * base_u, ty * base_v))
    positions = np.asarray(positions, dtype=np.float64)
    uvs = np.asarray(uvs, dtype=np.float64)
    tris = []
    for j in range(SEG):
        for i in range(SEG):
            a = j * (SEG + 1) + i
            b = a + 1
            c = a + (SEG + 1)
            d = c + 1
            # Same winding as Three.js indices: a,c,b and b,c,d
            tris.append((a, c, b))
            tris.append((b, c, d))
    return positions, uvs, np.asarray(tris, dtype=np.int32)


def sample_texture(tex, u, v):
    """Repeat-wrap UV sample with bilinear filtering. tex is BGR uint8 HxWx3.
    Three.js flipY=true: V=0 at image bottom.
    """
    h, w = tex.shape[:2]
    # wrap
    u = u - np.floor(u)
    v = v - np.floor(v)
    # flipY: v_img = 1-v maps to top of file at v=1
    x = u * (w - 1)
    y = (1.0 - v) * (h - 1)
    x0 = np.floor(x).astype(np.int32)
    y0 = np.floor(y).astype(np.int32)
    x1 = np.minimum(x0 + 1, w - 1)
    y1 = np.minimum(y0 + 1, h - 1)
    fx = x - x0
    fy = y - y0
    c00 = tex[y0, x0].astype(np.float64)
    c10 = tex[y0, x1].astype(np.float64)
    c01 = tex[y1, x0].astype(np.float64)
    c11 = tex[y1, x1].astype(np.float64)
    return (
        c00 * (1 - fx)[:, None] * (1 - fy)[:, None]
        + c10 * fx[:, None] * (1 - fy)[:, None]
        + c01 * (1 - fx)[:, None] * fy[:, None]
        + c11 * fx[:, None] * fy[:, None]
    )


def rasterize_overlay(before_bgr, tex_bgr, corners_xy):
    """Rasterize bilinear floor mesh onto a copy of before; return BGR uint8."""
    h, w = before_bgr.shape[:2]
    positions, uvs, tris = build_mesh(corners_xy)
    # Accumulate coverage + color in float buffers
    acc = np.zeros((h, w, 3), dtype=np.float64)
    weight = np.zeros((h, w), dtype=np.float64)

    for a, b, c in tris:
        pts = positions[[a, b, c]]
        uv = uvs[[a, b, c]]
        # bounding box
        minx = max(int(np.floor(pts[:, 0].min())), 0)
        maxx = min(int(np.ceil(pts[:, 0].max())), w - 1)
        miny = max(int(np.floor(pts[:, 1].min())), 0)
        maxy = min(int(np.ceil(pts[:, 1].max())), h - 1)
        if minx > maxx or miny > maxy:
            continue
        # barycentric over bbox
        xs = np.arange(minx, maxx + 1)
        ys = np.arange(miny, maxy + 1)
        xx, yy = np.meshgrid(xs, ys)
        px = xx.ravel().astype(np.float64)
        py = yy.ravel().astype(np.float64)

        v0 = pts[2] - pts[0]
        v1 = pts[1] - pts[0]
        v2x = px - pts[0, 0]
        v2y = py - pts[0, 1]
        den = v0[0] * v1[1] - v1[0] * v0[1]
        if abs(den) < 1e-9:
            continue
        # bary for vertices 0,1,2 corresponding to a,b,c with:
        # P = (1-w1-w2)*A + w1*B + w2*C  where A=pts[0], B=pts[1], C=pts[2]
        # Using edge method:
        inv = 1.0 / den
        w_c = (v2x * v1[1] - v1[0] * v2y) * inv  # weight for pts[2]
        w_b = (v0[0] * v2y - v2x * v0[1]) * inv  # weight for pts[1]
        w_a = 1.0 - w_b - w_c
        inside = (w_a >= -1e-5) & (w_b >= -1e-5) & (w_c >= -1e-5)
        if not np.any(inside):
            continue
        ia = w_a[inside]
        ib = w_b[inside]
        ic = w_c[inside]
        su = ia * uv[0, 0] + ib * uv[1, 0] + ic * uv[2, 0]
        sv = ia * uv[0, 1] + ib * uv[1, 1] + ic * uv[2, 1]
        colors = sample_texture(tex_bgr, su, sv)
        xi = px[inside].astype(np.int32)
        yi = py[inside].astype(np.int32)
        # last-write / overwrite — triangles don't overlap interior
        acc[yi, xi] = colors
        weight[yi, xi] = 1.0

    out = before_bgr.astype(np.float64)
    m = weight > 0
    out[m] = out[m] * (1.0 - OPACITY) + acc[m] * OPACITY
    return np.clip(out, 0, 255).astype(np.uint8), weight


def export_job(name, before_path, tex_path, corners, out_png, out_jpg):
    before = cv2.imread(str(before_path))
    tex = cv2.imread(str(tex_path))
    assert before is not None and tex is not None
    after, weight = rasterize_overlay(before, tex, corners)
    cov = float((weight > 0).mean())
    print(f"{name}: size={before.shape[1]}x{before.shape[0]} coverage={cov:.4f}")
    cv2.imwrite(str(out_png), after)
    cv2.imwrite(str(out_jpg), after, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
    # annotate corners for QA
    ann = after.copy()
    for i, (x, y) in enumerate(corners):
        cv2.circle(ann, (int(x), int(y)), 8, (0, 255, 255), 2)
        cv2.putText(ann, str(i + 1), (int(x) + 10, int(y) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    cv2.imwrite(str(OUT_DIR / f"{name}-corners-qa.jpg"), ann, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
    return after


def main():
    # Open: wall/floor junctions; full carpet span (furniture gets overlay — honest)
    open_corners = [
        (8, 798),     # FL
        (1192, 798),  # FR
        (1192, 560),  # BR — right wall junction
        (8, 538),     # BL — left under-window junction
    ]
    # Bath: floor/baseboard only — planks low
    bath_corners = [
        (4, 899),     # FL
        (1196, 899),  # FR
        (1185, 732),  # BR
        (15, 732),    # BL
    ]

    export_job(
        "open",
        GALLERY / "before-open-carpet.jpg",
        TEXTURES / "warm-oak.jpg",
        open_corners,
        OUT_DIR / "open-warm-oak.png",
        OUT_DIR / "open-warm-oak.jpg",
    )
    export_job(
        "bath",
        GALLERY / "before-bath-checkered.jpg",
        TEXTURES / "medium-oak.jpg",
        bath_corners,
        OUT_DIR / "bath-medium-oak.png",
        OUT_DIR / "bath-medium-oak.jpg",
    )
    print("done")


if __name__ == "__main__":
    main()
