import * as THREE from "three";
import { addProject } from "./gallery-store.js";

const TEXTURES = [
  { id: "white-oak", label: "White oak", file: "textures/white-oak.jpg", repeat: [6, 6] },
  { id: "natural-oak", label: "Natural oak", file: "textures/natural-oak.jpg", repeat: [7, 7] },
  { id: "medium-oak", label: "Medium oak", file: "textures/medium-oak.jpg", repeat: [6, 6] },
  { id: "warm-oak", label: "Warm oak", file: "textures/warm-oak.jpg", repeat: [6, 6] },
  { id: "honey-oak", label: "Honey oak", file: "textures/honey-oak.jpg", repeat: [5, 5] },
  { id: "golden-oak", label: "Golden oak", file: "textures/golden-oak.jpg", repeat: [6, 6] },
  { id: "maple", label: "Maple", file: "textures/maple.jpg", repeat: [7, 7] },
  { id: "hickory", label: "Hickory", file: "textures/hickory.jpg", repeat: [5, 5] },
  { id: "acacia", label: "Acacia", file: "textures/acacia.jpg", repeat: [5, 5] },
  { id: "cherry", label: "Cherry", file: "textures/cherry.jpg", repeat: [6, 6] },
  { id: "walnut", label: "Walnut", file: "textures/walnut.jpg", repeat: [5, 5] },
  { id: "walnut-plank", label: "Walnut plank", file: "textures/walnut-plank.jpg", repeat: [5, 5] },
  { id: "dark-walnut", label: "Dark walnut", file: "textures/dark-walnut.jpg", repeat: [5, 5] },
  { id: "espresso", label: "Espresso", file: "textures/espresso.jpg", repeat: [5, 5] },
  { id: "pine-natural", label: "Natural pine", file: "textures/pine-natural.jpg", repeat: [5, 5] },
  { id: "gray-oak", label: "Gray oak", file: "textures/gray-oak.jpg", repeat: [6, 6] },
  { id: "gray-wash", label: "Gray wash", file: "textures/weathered-gray.jpg", repeat: [7, 7] },
  { id: "narrow-plank", label: "Narrow plank", file: "textures/narrow-plank.jpg", repeat: [8, 8] },
  { id: "wide-plank", label: "Wide plank", file: "textures/wide-plank.jpg", repeat: [4, 4] }
];

const CORNER_LABELS = [
  "1 · front-left",
  "2 · front-right",
  "3 · back-right",
  "4 · back-left"
];

/**
 * Sample rooms. corners are normalized image coords, origin top-left,
 * y down, each in 0..1. Order matches manual taps: front-left, front-right,
 * back-right, back-left. Converted to world units (origin center, y up)
 * once the photo is fitted to the stage.
 */
const SAMPLE_ROOMS = [
  {
    id: "living",
    label: "Living room",
    file: "gallery/before-living-empty.jpg",
    corners: [
      [0.013, 0.988],
      [0.987, 0.988],
      [0.987, 0.785],
      [0.013, 0.679]
    ]
  },
  {
    id: "open",
    label: "Open plan",
    file: "gallery/before-open-carpet.jpg",
    corners: [
      [0.01, 0.985],
      [0.99, 0.985],
      [0.683, 0.588],
      [0.012, 0.688]
    ]
  },
  {
    id: "bath",
    label: "Bathroom",
    file: "gallery/before-bath-checkered.jpg",
    corners: [
      [0.013, 0.989],
      [0.987, 0.989],
      [0.987, 0.843],
      [0.013, 0.843]
    ]
  }
];

const stage = document.getElementById("stage");
const canvas = document.getElementById("c");
const statusEl = document.getElementById("status");
const hintEl = document.getElementById("corner-hint");
const photoInput = document.getElementById("photo-input");
const resetBtn = document.getElementById("reset-corners");
const clearBtn = document.getElementById("clear-photo");
const picker = document.getElementById("texture-picker");
const tileScale = document.getElementById("tile-scale");
const tileScaleVal = document.getElementById("tile-scale-val");
const measurePanel = document.getElementById("measure-panel");
const measureResults = document.getElementById("measure-results");
const sharePanel = document.getElementById("share-panel");
const shareStatus = document.getElementById("share-status");
const saveGalleryBtn = document.getElementById("save-gallery");
const downloadBtn = document.getElementById("download-result");
const rotateBtn = document.getElementById("rotate-planks");
const comparePanel = document.getElementById("compare-panel");
const compareWipe = document.getElementById("compare-wipe");
const refLengthFt = document.getElementById("ref-length-ft");
const plankLenIn = document.getElementById("plank-len-in");
const plankWidIn = document.getElementById("plank-wid-in");
const priceSqft = document.getElementById("price-sqft");
const wastePct = document.getElementById("waste-pct");

const renderer = new THREE.WebGLRenderer({
  canvas,
  antialias: true,
  alpha: false,
  preserveDrawingBuffer: true
});
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
renderer.setClearColor(0xf3e6c8, 1);

const scene = new THREE.Scene();
const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0.1, 10);
camera.position.z = 5;

const loader = new THREE.TextureLoader();
loader.crossOrigin = "anonymous";

/** @type {THREE.Mesh|null} */
let photoMesh = null;
/** @type {THREE.Mesh|null} */
let floorMesh = null;
/** @type {THREE.Group} */
const markers = new THREE.Group();
scene.add(markers);

/** Image size in world units (= CSS pixels of stage content box after fit) */
let viewW = 1;
let viewH = 1;
/** Natural photo pixels */
let imgW = 0;
let imgH = 0;
/** @type {string|null} */
let photoUrl = null;
/** @type {string|null} */
let photoOriginalDataUrl = null;
/** @type {string|null} */
let lastShareId = null;
/** Corners in world coords (origin center, y up) — order FL, FR, BR, BL */
/** @type {THREE.Vector2[]} */
let corners = [];
/** @type {string} */
let selectedTexId = TEXTURES[0].id;
let lookTouched = false;
/** 0..3, quarter turns of the plank texture. */
let plankRotation = 0;
/** @type {string|null} */
let activeSampleId = null;
/** Normalized corners for the active sample, or null once the user re-taps. */
let sampleNormCorners = null;
let sampleLoadToken = 0;
const captureBlock = document.getElementById("capture-block");
const workBlock = document.getElementById("work-block");
const stepList = document.getElementById("viz-steps");

(function applyLookFromQuery() {
  const id = new URLSearchParams(window.location.search).get("look");
  if (id && TEXTURES.some((tex) => tex.id === id)) {
    selectedTexId = id;
    lookTouched = true;
  }
})();
/** @type {THREE.Texture|null} */
let activeFloorTex = null;
const texCache = new Map();

function setStatus(msg) {
  statusEl.textContent = msg;
}

function showWork(on) {
  if (captureBlock) captureBlock.classList.toggle("hidden", on);
  const photoTools = document.getElementById("photo-tools");
  const changeRoom = document.getElementById("change-room");
  if (photoTools) photoTools.classList.toggle("hidden", !on);
  if (changeRoom) changeRoom.classList.toggle("hidden", !on);
}

function updateSteps() {
  if (!stepList) return;
  const photo = !!photoMesh;
  const cornersDone = corners.length === 4;
  const premarked = !!(sampleNormCorners && cornersDone);
  let current = "photo";
  if (photo && premarked && !lookTouched) current = "look";
  else if (photo && premarked && lookTouched) current = "save";
  else if (photo && !lookTouched && corners.length === 0) current = "look";
  else if (photo && !cornersDone) current = "corners";
  else if (photo && cornersDone) current = "save";
  const order = ["photo", "look", "corners", "save"];
  const currentIdx = order.indexOf(current);
  stepList.querySelectorAll("li").forEach((li) => {
    const idx = order.indexOf(li.dataset.step);
    const earlier = idx > -1 && idx < currentIdx;
    const preDone = premarked && (li.dataset.step === "photo" || li.dataset.step === "corners");
    li.classList.toggle("is-current", idx === currentIdx);
    li.classList.toggle("is-done", (earlier || preDone) && idx !== currentIdx);
  });
}

function highlightSample() {
  document.querySelectorAll("[data-sample]").forEach((btn) => {
    const on = btn.dataset.sample === activeSampleId;
    btn.classList.toggle("is-selected", on);
    btn.setAttribute("aria-pressed", on ? "true" : "false");
  });
}

function normToWorld(u, v) {
  return new THREE.Vector2((u - 0.5) * viewW, (0.5 - v) * viewH);
}

function applySampleCorners() {
  if (!sampleNormCorners || !viewW || !viewH) return;
  corners = sampleNormCorners.map(([u, v]) => normToWorld(u, v));
}

function currentLookLabel() {
  const meta = TEXTURES.find((tex) => tex.id === selectedTexId);
  return (meta && meta.label) || "White oak";
}

function showPhotoCheck(result) {
  const el = document.getElementById("photo-check-live");
  if (el && window.VonPhotoCheck && result) window.VonPhotoCheck.paintCheck(el, result);
}

const vizEmpty = document.getElementById("viz-empty");

function setEmptyState(show) {
  if (!vizEmpty) return;
  vizEmpty.classList.toggle("hidden", !show);
  vizEmpty.setAttribute("aria-hidden", show ? "false" : "true");
  if (stage) stage.classList.toggle("has-photo", !show);
}

function updateHint() {
  if (!photoMesh) {
    hintEl.classList.add("hidden");
    return;
  }
  hintEl.classList.remove("hidden");
  if (sampleNormCorners && corners.length === 4) {
    hintEl.textContent = "Sample room — the floor is already marked. Pick a look to swap the planks.";
  } else if (corners.length < 4) {
    hintEl.textContent = "Tap corner " + CORNER_LABELS[corners.length];
  } else {
    hintEl.textContent = "Floor quad set — pick a look, or reset corners to tap again";
  }
}

function fitCamera() {
  const rect = stage.getBoundingClientRect();
  const cssW = Math.max(1, rect.width);
  const cssH = Math.max(1, rect.height);
  renderer.setSize(cssW, cssH, false);

  if (!imgW || !imgH) {
    viewW = cssW;
    viewH = cssH;
    camera.left = -viewW / 2;
    camera.right = viewW / 2;
    camera.top = viewH / 2;
    camera.bottom = -viewH / 2;
    camera.updateProjectionMatrix();
    return;
  }

  const scale = Math.min(cssW / imgW, cssH / imgH);
  viewW = imgW * scale;
  viewH = imgH * scale;

  camera.left = -cssW / 2;
  camera.right = cssW / 2;
  camera.top = cssH / 2;
  camera.bottom = -cssH / 2;
  camera.updateProjectionMatrix();

  if (photoMesh) {
    photoMesh.scale.set(viewW, viewH, 1);
  }
  if (sampleNormCorners) applySampleCorners();
  rebuildFloor();
  rebuildMarkers();
}

function clearMarkers() {
  while (markers.children.length) {
    const m = markers.children.pop();
    m.geometry.dispose();
    m.material.dispose();
  }
}

function rebuildMarkers() {
  clearMarkers();
  if (sampleNormCorners) return;
  corners.forEach((c, i) => {
    const g = new THREE.CircleGeometry(Math.max(6, Math.min(viewW, viewH) * 0.012), 24);
    const mat = new THREE.MeshBasicMaterial({
      color: i === corners.length - 1 && corners.length < 4 ? 0xf0c040 : 0x2f5d50,
      depthTest: false
    });
    const mesh = new THREE.Mesh(g, mat);
    mesh.position.set(c.x, c.y, 1.5);
    mesh.renderOrder = 10;
    markers.add(mesh);

    // small ring
    const ring = new THREE.RingGeometry(
      Math.max(7, Math.min(viewW, viewH) * 0.014),
      Math.max(9, Math.min(viewW, viewH) * 0.018),
      24
    );
    const ringMat = new THREE.MeshBasicMaterial({ color: 0xffffff, depthTest: false });
    const ringMesh = new THREE.Mesh(ring, ringMat);
    ringMesh.position.set(c.x, c.y, 1.4);
    ringMesh.renderOrder = 9;
    markers.add(ringMesh);
  });

  // outline when complete
  if (corners.length === 4) {
    const pts = corners.concat([corners[0]]).map((c) => new THREE.Vector3(c.x, c.y, 1.2));
    const geo = new THREE.BufferGeometry().setFromPoints(pts);
    const line = new THREE.Line(
      geo,
      new THREE.LineBasicMaterial({ color: 0xffffff, depthTest: false })
    );
    line.renderOrder = 8;
    markers.add(line);
  }
}


function lineIntersect(a, b, c, d) {
  const rx = b.x - a.x;
  const ry = b.y - a.y;
  const sx = d.x - c.x;
  const sy = d.y - c.y;
  const den = rx * sy - ry * sx;
  if (Math.abs(den) < 1e-6) return null;
  const t = ((c.x - a.x) * sy - (c.y - a.y) * sx) / den;
  return { x: a.x + t * rx, y: a.y + t * ry };
}

function mul3(A, B) {
  const C = new Array(9);
  for (let r = 0; r < 3; r++) {
    for (let c = 0; c < 3; c++) {
      C[r * 3 + c] = A[r * 3] * B[c] + A[r * 3 + 1] * B[3 + c] + A[r * 3 + 2] * B[6 + c];
    }
  }
  return C;
}

function inv3(M) {
  const a = M[0], b = M[1], c = M[2];
  const d = M[3], e = M[4], f = M[5];
  const g = M[6], h = M[7], i = M[8];
  const A = e * i - f * h;
  const B = c * h - b * i;
  const C = b * f - c * e;
  const D = f * g - d * i;
  const E = a * i - c * g;
  const F = c * d - a * f;
  const G = d * h - e * g;
  const H = b * g - a * h;
  const I = a * e - b * d;
  const det = a * A + b * D + c * G;
  if (Math.abs(det) < 1e-10) return null;
  const s = 1 / det;
  return [A * s, B * s, C * s, D * s, E * s, F * s, G * s, H * s, I * s];
}

function smallestEigenvector(S) {
  const n = 9;
  const A = S.map((row) => row.slice());
  const V = Array.from({ length: n }, (_, i) => Array.from({ length: n }, (_, j) => (i === j ? 1 : 0)));
  for (let iter = 0; iter < 48; iter++) {
    let p = 0;
    let q = 1;
    let max = 0;
    for (let i = 0; i < n; i++) {
      for (let j = i + 1; j < n; j++) {
        const v = Math.abs(A[i][j]);
        if (v > max) {
          max = v;
          p = i;
          q = j;
        }
      }
    }
    if (max < 1e-12) break;
    const app = A[p][p];
    const aqq = A[q][q];
    const apq = A[p][q];
    const tau = (aqq - app) / (2 * apq);
    const t = Math.sign(tau || 1) / (Math.abs(tau) + Math.sqrt(1 + tau * tau));
    const c = 1 / Math.sqrt(1 + t * t);
    const s = t * c;
    A[p][p] = app - t * apq;
    A[q][q] = aqq + t * apq;
    A[p][q] = 0;
    A[q][p] = 0;
    for (let k = 0; k < n; k++) {
      if (k === p || k === q) continue;
      const aik = A[k][p];
      const aiq = A[k][q];
      const np = c * aik - s * aiq;
      const nq = s * aik + c * aiq;
      A[k][p] = np;
      A[p][k] = np;
      A[k][q] = nq;
      A[q][k] = nq;
    }
    for (let k = 0; k < n; k++) {
      const vip = V[k][p];
      const viq = V[k][q];
      V[k][p] = c * vip - s * viq;
      V[k][q] = s * vip + c * viq;
    }
  }
  let minI = 0;
  let minV = Infinity;
  for (let i = 0; i < n; i++) {
    if (A[i][i] < minV) {
      minV = A[i][i];
      minI = i;
    }
  }
  const h = [];
  for (let k = 0; k < n; k++) h.push(V[k][minI]);
  return h;
}

function normPoints(pts) {
  let cx = 0;
  let cy = 0;
  pts.forEach((p) => {
    cx += p.x;
    cy += p.y;
  });
  cx /= pts.length;
  cy /= pts.length;
  let acc = 0;
  pts.forEach((p) => {
    acc += Math.hypot(p.x - cx, p.y - cy);
  });
  const s = (Math.SQRT2 * pts.length) / Math.max(acc, 1e-8);
  return {
    pts: pts.map((p) => ({ x: s * (p.x - cx), y: s * (p.y - cy) })),
    T: [s, 0, -s * cx, 0, s, -s * cy, 0, 0, 1]
  };
}

function homography(src, dst) {
  const S = normPoints(src);
  const D = normPoints(dst);
  const rows = [];
  for (let i = 0; i < 4; i++) {
    const x = S.pts[i].x;
    const y = S.pts[i].y;
    const u = D.pts[i].x;
    const v = D.pts[i].y;
    rows.push([-x, -y, -1, 0, 0, 0, u * x, u * y, u]);
    rows.push([0, 0, 0, -x, -y, -1, v * x, v * y, v]);
  }
  const M = Array.from({ length: 9 }, () => Array(9).fill(0));
  rows.forEach((row) => {
    for (let i = 0; i < 9; i++) {
      for (let j = 0; j < 9; j++) M[i][j] += row[i] * row[j];
    }
  });
  const h = smallestEigenvector(M);
  const TdInv = inv3(D.T);
  if (!TdInv) return null;
  return mul3(mul3(TdInv, h), S.T);
}

function applyH(H, x, y) {
  const u = H[0] * x + H[1] * y + H[2];
  const v = H[3] * x + H[4] * y + H[5];
  const w = H[6] * x + H[7] * y + H[8];
  if (Math.abs(w) < 1e-8) return null;
  return { x: u / w, y: v / w };
}

function focalPx(fl, fr, br, bl) {
  const vpD = lineIntersect(fl, bl, fr, br);
  const vpW = lineIntersect(fl, fr, bl, br);
  if (vpD && vpW) {
    const f2 = -(vpD.x * vpW.x + vpD.y * vpW.y);
    if (f2 > 80 * 80) return Math.sqrt(f2);
  }
  return Math.max(viewW, viewH) * 1.15;
}

function estimateDepthInches(fl, fr, br, bl, widthIn) {
  const front = Math.max(1, dist2(fl, fr));
  const back = Math.max(1, dist2(bl, br));
  const side = (dist2(fl, bl) + dist2(fr, br)) / 2;
  const topDown = widthIn * (side / front);
  const f = focalPx(fl, fr, br, bl);
  let depth = f * widthIn * Math.abs(1 / Math.min(front, back) - 1 / Math.max(front, back));
  if (!Number.isFinite(depth) || depth < widthIn * 0.35 || depth > widthIn * 4) {
    depth = Math.min(widthIn * 3.5, Math.max(widthIn * 0.45, topDown));
  }
  return depth;
}

const FLOOR_VERT = [
  "attribute vec2 photoUv;",
  "attribute float edgeAmt;",
  "varying vec2 vUv;",
  "varying vec2 vPhotoUv;",
  "varying float vEdge;",
  "void main() {",
  "  vUv = uv;",
  "  vPhotoUv = photoUv;",
  "  vEdge = edgeAmt;",
  "  gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);",
  "}"
].join("\n");

const FLOOR_FRAG = [
  "precision highp float;",
  "uniform sampler2D woodMap;",
  "uniform sampler2D photoMap;",
  "uniform float wipe;",
  "uniform vec2 resolution;",
  "varying vec2 vUv;",
  "varying vec2 vPhotoUv;",
  "varying float vEdge;",
  "void main() {",
  "  if (gl_FragCoord.x < wipe * resolution.x) discard;",
  "  vec3 wood = texture2D(woodMap, vUv).rgb;",
  "  float luma = dot(wood, vec3(0.2126, 0.7152, 0.0722));",
  "  vec3 detail = wood - vec3(luma);",
  "  float base = clamp((luma - 0.5) * 1.35 + 0.5, 0.0, 1.0);",
  "  wood = clamp(vec3(base) + detail * 1.7, 0.0, 1.0);",
  "  vec3 photo = texture2D(photoMap, clamp(vPhotoUv, 0.0, 1.0)).rgb;",
  "  float room = dot(photo, vec3(0.2126, 0.7152, 0.0722));",
  "  float shade = clamp(0.36 + room * 1.2, 0.2, 1.5);",
  "  vec3 color = wood * shade;",
  "  color = mix(color, wood * (photo + vec3(0.06)), 0.3);",
  "  float edge = smoothstep(0.0, 0.02, vEdge);",
  "  gl_FragColor = vec4(color, edge);",
  "  #include <colorspace_fragment>",
  "}"
].join("\n");

/**
 * Build a subdivided quad with bilinear corner warp + tiled UVs.
 * Subdivision improves texture sampling across a trapezoid (prototype perspective approx).
 */
function rebuildFloor() {
  if (floorMesh) {
    scene.remove(floorMesh);
    floorMesh.geometry.dispose();
    floorMesh.material.dispose();
    floorMesh = null;
  }
  if (corners.length !== 4 || !activeFloorTex || !photoMesh) return;

  const [fl, fr, br, bl] = corners;
  const widthIn = Math.max(24, (parseFloat(refLengthFt && refLengthFt.value) || 12) * 12);
  const depthIn = estimateDepthInches(fl, fr, br, bl, widthIn);
  const plankW = Math.max(3, parseFloat(plankWidIn && plankWidIn.value) || 7);
  const scale = parseFloat(tileScale && tileScale.value) || 6;
  // The source image is a square scan of many planks, about 16 boards across.
  // Scale 6 keeps those boards near the plank-width control (7 in by default)
  // without stretching one photo into a single postage-stamp tile.
  const tileIn = 16 * plankW;
  const repeatsU = (widthIn / tileIn) * (scale / 6);
  const repeatsV = (depthIn / tileIn) * (scale / 6);

  const src = [
    { x: 0, y: 0 },
    { x: widthIn, y: 0 },
    { x: widthIn, y: depthIn },
    { x: 0, y: depthIn }
  ];
  const dst = [fl, fr, br, bl].map((p) => ({ x: p.x, y: p.y }));
  const H = homography(src, dst);

  const seg = 32;
  const positions = [];
  const uvs = [];
  const photoUvs = [];
  const edges = [];
  const indices = [];

  for (let j = 0; j <= seg; j++) {
    const qy = j / seg;
    for (let i = 0; i <= seg; i++) {
      const qx = i / seg;
      const fx = qx * widthIn;
      const fy = qy * depthIn;
      let p = H ? applyH(H, fx, fy) : null;
      if (!p) {
        const bottom = { x: fl.x + (fr.x - fl.x) * qx, y: fl.y + (fr.y - fl.y) * qx };
        const top = { x: bl.x + (br.x - bl.x) * qx, y: bl.y + (br.y - bl.y) * qx };
        p = { x: bottom.x + (top.x - bottom.x) * qy, y: bottom.y + (top.y - bottom.y) * qy };
      }
      positions.push(p.x, p.y, 0.5);
      const uv = rotatedPlankUv(qx, qy, repeatsU, repeatsV, plankRotation);
      uvs.push(uv[0], uv[1]);
      photoUvs.push(p.x / viewW + 0.5, p.y / viewH + 0.5);
      edges.push(Math.min(qx, 1 - qx, qy, 1 - qy));
    }
  }

  for (let j = 0; j < seg; j++) {
    for (let i = 0; i < seg; i++) {
      const a = j * (seg + 1) + i;
      const b = a + 1;
      const c = a + (seg + 1);
      const d = c + 1;
      indices.push(a, b, c, b, d, c);
    }
  }

  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  geo.setAttribute("uv", new THREE.Float32BufferAttribute(uvs, 2));
  geo.setAttribute("photoUv", new THREE.Float32BufferAttribute(photoUvs, 2));
  geo.setAttribute("edgeAmt", new THREE.Float32BufferAttribute(edges, 1));
  geo.setIndex(indices);

  activeFloorTex.wrapS = THREE.RepeatWrapping;
  activeFloorTex.wrapT = THREE.RepeatWrapping;
  activeFloorTex.colorSpace = THREE.SRGBColorSpace;
  activeFloorTex.anisotropy = Math.min(8, renderer.capabilities.getMaxAnisotropy());
  activeFloorTex.needsUpdate = true;

  const photoMap = photoMesh.material.map;
  const mat = new THREE.ShaderMaterial({
    uniforms: {
      woodMap: { value: activeFloorTex },
      photoMap: { value: photoMap },
      wipe: { value: currentWipe() },
      resolution: { value: renderer.getDrawingBufferSize(new THREE.Vector2()) }
    },
    vertexShader: FLOOR_VERT,
    fragmentShader: FLOOR_FRAG,
    transparent: true,
    depthWrite: false,
    depthTest: false,
    side: THREE.DoubleSide
  });

  floorMesh = new THREE.Mesh(geo, mat);
  floorMesh.frustumCulled = false;
  floorMesh.renderOrder = 2;
  scene.add(floorMesh);
}

function rotatedPlankUv(qx, qy, repeatsU, repeatsV, rot) {
  const u = qx * repeatsU;
  const v = qy * repeatsV;
  if (rot === 1) return [qy * repeatsV, (1 - qx) * repeatsU];
  if (rot === 2) return [(1 - qx) * repeatsU, (1 - qy) * repeatsV];
  if (rot === 3) return [(1 - qy) * repeatsV, qx * repeatsU];
  return [u, v];
}

function loadFloorTexture(id) {
  const meta = TEXTURES.find((t) => t.id === id);
  if (!meta) return Promise.reject(new Error("unknown texture"));
  selectedTexId = id;
  [...picker.querySelectorAll(".tex-opt")].forEach((btn) => {
    btn.classList.toggle("selected", btn.dataset.id === id);
  });

  if (texCache.has(id)) {
    activeFloorTex = texCache.get(id);
    rebuildFloor();
    return Promise.resolve(activeFloorTex);
  }

  return new Promise((resolve, reject) => {
    loader.load(
      meta.file,
      (tex) => {
        tex.colorSpace = THREE.SRGBColorSpace;
        tex.wrapS = THREE.RepeatWrapping;
        tex.wrapT = THREE.RepeatWrapping;
        texCache.set(id, tex);
        activeFloorTex = tex;
        rebuildFloor();
        resolve(tex);
      },
      undefined,
      reject
    );
  });
}

function setPhotoFromFile(file, sampleRoom) {
  if (photoUrl) URL.revokeObjectURL(photoUrl);
  clearScenePhoto();
  photoOriginalDataUrl = null;
  resetSavePrompt();
  if (compareWipe) compareWipe.value = "100";
  activeSampleId = sampleRoom ? sampleRoom.id : null;
  sampleNormCorners = sampleRoom ? sampleRoom.corners.map((pair) => pair.slice()) : null;

  photoUrl = URL.createObjectURL(file);
  fileToDataUrl(file)
    .then((url) => compressDataUrl(url, 1600, 0.75))
    .then((url) => {
      photoOriginalDataUrl = url;
    })
    .catch(() => {
      photoOriginalDataUrl = null;
    });

  const img = new Image();
  img.onload = () => {
    imgW = img.naturalWidth;
    imgH = img.naturalHeight;
    const tex = new THREE.Texture(img);
    tex.colorSpace = THREE.SRGBColorSpace;
    tex.needsUpdate = true;

    const geo = new THREE.PlaneGeometry(1, 1);
    const mat = new THREE.MeshBasicMaterial({ map: tex });
    photoMesh = new THREE.Mesh(geo, mat);
    photoMesh.position.z = 0;
    scene.add(photoMesh);

    corners = [];
    resetBtn.disabled = false;
    clearBtn.disabled = false;
    setPickerEnabled(true);
    setEmptyState(false);
    showWork(true);
    fitCamera();
    const finish = () => {
      updateHint();
      updateSteps();
      updateMeasureUI();
      highlightSample();
      render();
    };
    if (sampleRoom) {
      const roomName = sampleRoom.label.toLowerCase();
      loadFloorTexture(selectedTexId).then(() => {
        setStatus(currentLookLabel() + " is on the " + roomName + ". Pick a look to swap it, then compare or download.");
        finish();
      }).catch(() => {
        setStatus("The " + roomName + " loaded, but that look didn’t. Try another look.");
        finish();
      });
    } else {
      setStatus(lookTouched
        ? "Step 3: tap four floor corners — front-left, front-right, back-right, back-left."
        : "Step 2: pick a wood look, then tap the four floor corners.");
      finish();
    }
  };
  img.onerror = () => setStatus("Could not load that image. Try another photo.");
  img.src = photoUrl;
}

function clearScenePhoto() {
  if (photoMesh) {
    scene.remove(photoMesh);
    if (photoMesh.material.map) photoMesh.material.map.dispose();
    photoMesh.material.dispose();
    photoMesh.geometry.dispose();
    photoMesh = null;
  }
  if (floorMesh) {
    scene.remove(floorMesh);
    floorMesh.geometry.dispose();
    floorMesh.material.dispose();
    floorMesh = null;
  }
  corners = [];
  clearMarkers();
  imgW = imgH = 0;
  updateHint();
}

function clearPhoto() {
  if (photoUrl) URL.revokeObjectURL(photoUrl);
  photoUrl = null;
  photoOriginalDataUrl = null;
  resetSavePrompt();
  if (compareWipe) compareWipe.value = "100";
  photoInput.value = "";
  clearScenePhoto();
  resetBtn.disabled = true;
  clearBtn.disabled = true;
  setPickerEnabled(false);
  setEmptyState(true);
  showWork(false);
  const liveCheck = document.getElementById("photo-check-live");
  if (liveCheck) {
    liveCheck.textContent = "";
    liveCheck.classList.add("hidden");
  }
  activeSampleId = null;
  sampleNormCorners = null;
  highlightSample();
  fitCamera();
  setStatus("Try a sample room, or take or upload a photo with a clear view of the floor.");
  updateSteps();
  updateMeasureUI();
  render();
}

function resetCorners() {
  if (sampleNormCorners) lookTouched = true;
  sampleNormCorners = null;
  corners = [];
  if (floorMesh) {
    scene.remove(floorMesh);
    floorMesh.geometry.dispose();
    floorMesh.material.dispose();
    floorMesh = null;
  }
  rebuildMarkers();
  resetSavePrompt();
  if (compareWipe) compareWipe.value = "100";
  setStatus("Corners cleared — tap four floor corners again.");
  updateHint();
  updateSteps();
  updateMeasureUI();
  render();
}


function shoelaceArea(pts) {
  // pts: array of {x,y}; absolute area
  let sum = 0;
  const n = pts.length;
  for (let i = 0; i < n; i++) {
    const j = (i + 1) % n;
    sum += pts[i].x * pts[j].y - pts[j].x * pts[i].y;
  }
  return Math.abs(sum) / 2;
}

function dist2(a, b) {
  const dx = b.x - a.x;
  const dy = b.y - a.y;
  return Math.hypot(dx, dy);
}

/** Rough estimate from photo quad + one reference length on front edge (1→2). */
function computeEstimate() {
  if (corners.length !== 4) return null;
  const refFt = parseFloat(refLengthFt && refLengthFt.value) || 0;
  if (refFt <= 0) return null;
  const [fl, fr, br, bl] = corners;
  const areaWorld = shoelaceArea([fl, fr, br, bl]);
  const edgeWorld = dist2(fl, fr); // front edge corners 1→2
  if (edgeWorld < 1e-6) return null;
  const ftPerWorld = refFt / edgeWorld;
  const areaSqFt = areaWorld * ftPerWorld * ftPerWorld;
  const pLen = parseFloat(plankLenIn.value) || 48;
  const pWid = parseFloat(plankWidIn.value) || 7;
  const price = parseFloat(priceSqft.value) || 0;
  const waste = parseFloat(wastePct.value) || 0;
  const plankSqFt = (pLen * pWid) / 144;
  const areaWithWaste = areaSqFt * (1 + waste / 100);
  const plankCount = plankSqFt > 0 ? Math.ceil(areaWithWaste / plankSqFt) : 0;
  const cost = areaWithWaste * price;
  return { areaSqFt, areaWithWaste, plankCount, cost, plankSqFt, refFt, edgeWorld };
}

function formatMoney(n) {
  return "$" + (Math.round(n * 100) / 100).toFixed(2);
}

function updateMeasureUI() {
  const ready = corners.length === 4 && !!activeFloorTex && !!photoMesh;
  if (measurePanel) measurePanel.classList.toggle("hidden", !ready);
  if (sharePanel) sharePanel.classList.toggle("hidden", !ready);
  if (comparePanel) comparePanel.classList.toggle("hidden", !ready);
  if (!ready || !measureResults) return;

  const est = computeEstimate();
  if (!est) {
    measureResults.innerHTML = "<p>Enter a positive reference length (feet) for the front edge.</p>";
    return;
  }
  measureResults.innerHTML =
    "<dl>" +
    "<dt>Estimated floor area</dt><dd>" + est.areaSqFt.toFixed(1) + " sq ft</dd>" +
    "<dt>Area with waste</dt><dd>" + est.areaWithWaste.toFixed(1) + " sq ft</dd>" +
    "<dt>Plank count (ceil)</dt><dd>" + est.plankCount + "</dd>" +
    "<dt>Rough material cost</dt><dd>" + formatMoney(est.cost) + "</dd>" +
    "</dl>" +
    '<p class="hint" style="margin:0.65rem 0 0">Based on a ' +
    est.refFt +
    " ft front edge (corners 1→2) and a flat-floor assumption. Perspective and camera angle can skew this.</p>";
}

function compressDataUrl(dataUrl, maxW, quality) {
  return new Promise((resolve) => {
    if (!dataUrl || !dataUrl.startsWith("data:")) {
      resolve(dataUrl);
      return;
    }
    const img = new Image();
    img.onload = () => {
      const scale = Math.min(1, (maxW || 1280) / img.naturalWidth);
      const w = Math.max(1, Math.round(img.naturalWidth * scale));
      const h = Math.max(1, Math.round(img.naturalHeight * scale));
      const c = document.createElement("canvas");
      c.width = w;
      c.height = h;
      const ctx = c.getContext("2d");
      ctx.drawImage(img, 0, 0, w, h);
      resolve(c.toDataURL("image/jpeg", quality || 0.72));
    };
    img.onerror = () => resolve(dataUrl);
    img.src = dataUrl;
  });
}

function fileToDataUrl(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result || ""));
    reader.onerror = () => reject(new Error("Could not read photo"));
    reader.readAsDataURL(file);
  });
}

function downloadResult() {
  if (!photoMesh || corners.length !== 4 || !activeFloorTex) return;
  const slug = selectedTexId || "floor";
  const url = withHiddenMarkers(() => canvasSnapshotDataUrl());
  const a = document.createElement("a");
  a.href = url;
  a.download = "vinyl-or-not-" + slug + ".png";
  document.body.appendChild(a);
  a.click();
  a.remove();
}

function canvasSnapshotDataUrl() {
  let prev = null;
  const uniforms = floorMesh && floorMesh.material && floorMesh.material.uniforms;
  if (uniforms && uniforms.wipe) {
    prev = uniforms.wipe.value;
    uniforms.wipe.value = 0;
  }
  renderer.render(scene, camera);
  const url = canvas.toDataURL("image/png");
  if (uniforms && uniforms.wipe && prev != null) uniforms.wipe.value = prev;
  return url;
}

function shareUrlFor(id) {
  const base = window.location.href.replace(/[^/]*$/, "");
  return base + "projects.html?id=" + encodeURIComponent(id);
}

function escHtml(s) {
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function resetSavePrompt() {
  lastShareId = null;
  if (saveGalleryBtn) {
    saveGalleryBtn.hidden = false;
    saveGalleryBtn.disabled = false;
  }
  if (shareStatus) shareStatus.textContent = "";
}

function setPickerEnabled(on) {
  [...picker.querySelectorAll(".tex-opt")].forEach((btn) => {
    btn.disabled = !on;
  });
}

function buildPicker() {
  picker.innerHTML = "";
  TEXTURES.forEach((t, idx) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "tex-opt" + (t.id === selectedTexId ? " selected" : "");
    btn.dataset.id = t.id;
    btn.setAttribute("role", "option");
    btn.setAttribute("aria-selected", t.id === selectedTexId ? "true" : "false");
    btn.disabled = !photoMesh;
    btn.innerHTML = `<img src="${t.file}" alt="" loading="lazy" /><span>${t.label}</span>`;
    btn.addEventListener("click", () => {
      lookTouched = true;
      resetSavePrompt();
      const apply = () => {
        if (corners.length !== 4) {
          setStatus("“" + t.label + "” selected. Now tap the four floor corners.");
          updateSteps();
          return;
        }
        setStatus("Applied “" + t.label + "”. Adjust plank scale if the planks look too large or small.");
        updateMeasureUI();
        updateSteps();
        render();
      };
      loadFloorTexture(t.id).then(apply).catch(() => setStatus("That look didn’t load. Try another."));
    });
    picker.appendChild(btn);
  });
}

function eventToWorld(e) {
  const rect = canvas.getBoundingClientRect();
  const px = ((e.clientX - rect.left) / rect.width) * 2 - 1;
  const py = -(((e.clientY - rect.top) / rect.height) * 2 - 1);
  const x = (px * rect.width) / 2;
  const y = (py * rect.height) / 2;
  return new THREE.Vector2(x, y);
}

function onPointer(e) {
  if (!photoMesh) return;
  e.preventDefault();
  const p = eventToWorld(e);

  // Only accept clicks roughly on the photo bounds
  const halfW = viewW / 2;
  const halfH = viewH / 2;
  if (Math.abs(p.x) > halfW * 1.02 || Math.abs(p.y) > halfH * 1.02) {
    setStatus("Tap inside the photo to set a floor corner.");
    return;
  }

  if (corners.length < 4) {
    corners.push(p);
    rebuildMarkers();
    updateHint();
    if (corners.length === 4) {
      lookTouched = true;
      setStatus("Floor marked — “" + ((TEXTURES.find((tex) => tex.id === selectedTexId) || {}).label || "look") + "” is on the photo.");
      loadFloorTexture(selectedTexId).then(() => {
        updateMeasureUI();
        updateSteps();
        render();
      });
    } else {
      lookTouched = true;
      setStatus("Corner " + corners.length + "/4 set — next: " + CORNER_LABELS[corners.length]);
      updateSteps();
    }
    render();
  }
}

function currentWipe() {
  const v = compareWipe ? parseFloat(compareWipe.value) : 100;
  const shown = Number.isFinite(v) ? Math.min(100, Math.max(0, v)) : 100;
  return 1 - shown / 100;
}

function render() {
  if (floorMesh && floorMesh.material && floorMesh.material.uniforms && floorMesh.material.uniforms.wipe) {
    floorMesh.material.uniforms.wipe.value = currentWipe();
    const buf = renderer.getDrawingBufferSize(new THREE.Vector2());
    floorMesh.material.uniforms.resolution.value.copy(buf);
  }
  renderer.render(scene, camera);
}

function loop() {
  render();
  requestAnimationFrame(loop);
}

function loadSampleRoom(id) {
  const room = SAMPLE_ROOMS.find((item) => item.id === id);
  if (!room) return;
  const token = ++sampleLoadToken;
  setStatus("Loading the " + room.label.toLowerCase() + "…");
  fetch(room.file)
    .then((res) => {
      if (!res.ok) throw new Error("missing photo");
      return res.blob();
    })
    .then((blob) => {
      if (token !== sampleLoadToken) return;
      const file = new File([blob], room.id + ".jpg", { type: blob.type || "image/jpeg" });
      setPhotoFromFile(file, room);
    })
    .catch(() => {
      if (token !== sampleLoadToken) return;
      setStatus("Couldn’t load that sample room. Try another, or upload a photo.");
    });
}

// Events
photoInput.addEventListener("change", (e) => {
  const f = e.target.files && e.target.files[0];
  e.target.value = "";
  if (!f) return;
  if (window.VonPhotoCheck) {
    window.VonPhotoCheck.analyzeFile(f).then(showPhotoCheck);
  }
  setPhotoFromFile(f);
});

if (window.VonPhotoCheck && document.getElementById("open-camera")) {
  window.VonPhotoCheck.attachCamera({
    openBtn: document.getElementById("open-camera"),
    panel: document.getElementById("camera-panel"),
    video: document.getElementById("camera-video"),
    shutter: document.getElementById("camera-shutter"),
    cancel: document.getElementById("camera-cancel"),
    review: document.getElementById("shot-review"),
    preview: document.getElementById("shot-preview"),
    checkEl: document.getElementById("shot-check"),
    accept: document.getElementById("shot-accept"),
    retake: document.getElementById("shot-retake"),
    onStatus: (msg) => {
      const el = document.getElementById("camera-status");
      if (el) el.textContent = msg || "";
    },
    onAccept: (file, result) => {
      showPhotoCheck(result);
      setPhotoFromFile(file);
    }
  });
}
resetBtn.addEventListener("click", resetCorners);
clearBtn.addEventListener("click", clearPhoto);
document.querySelectorAll("[data-sample]").forEach((btn) => {
  btn.addEventListener("click", () => loadSampleRoom(btn.dataset.sample));
});
if (downloadBtn) downloadBtn.addEventListener("click", downloadResult);
if (rotateBtn) {
  rotateBtn.addEventListener("click", () => {
    plankRotation = (plankRotation + 1) % 4;
    resetSavePrompt();
    if (corners.length === 4 && activeFloorTex) {
      rebuildFloor();
      render();
    }
    const turns = plankRotation === 0 ? "back to the start" : plankRotation * 90 + "°";
    setStatus("Planks rotated " + turns + ".");
  });
}
tileScale.addEventListener("input", () => {
  tileScaleVal.textContent = tileScale.value;
  if (corners.length === 4) {
    rebuildFloor();
    render();
  }
});

canvas.addEventListener("pointerdown", onPointer);

window.addEventListener("resize", () => {
  fitCamera();
  render();
});


[refLengthFt, plankLenIn, plankWidIn].forEach((el) => {
  if (!el) return;
  el.addEventListener("input", () => {
    if (corners.length === 4 && activeFloorTex) {
      rebuildFloor();
      render();
    }
    updateMeasureUI();
  });
});
[priceSqft, wastePct].forEach((el) => {
  if (el) el.addEventListener("input", updateMeasureUI);
});
if (compareWipe) {
  compareWipe.addEventListener("input", () => render());
}

function withHiddenMarkers(fn) {
  const prevVisible = markers.visible;
  markers.visible = false;
  try {
    return fn();
  } finally {
    markers.visible = prevVisible;
    render();
  }
}

if (saveGalleryBtn) {
  saveGalleryBtn.addEventListener("click", async () => {
    if (!photoMesh || corners.length !== 4 || !activeFloorTex) return;
    if (shareStatus) shareStatus.textContent = "Saving on this device…";
    saveGalleryBtn.disabled = true;
    try {
      const afterPng = withHiddenMarkers(() => canvasSnapshotDataUrl());
      const afterJpeg = await compressDataUrl(afterPng, 1400, 0.78);
      const beforeSrc = photoOriginalDataUrl || afterJpeg;
      const beforeComp = await compressDataUrl(beforeSrc, 1400, 0.72);
      const texMeta = TEXTURES.find((t) => t.id === selectedTexId);
      const label = (texMeta && texMeta.label) || "Floor";
      const saved = await addProject({
        title: label + " preview",
        location: "",
        flooring: "LVP",
        role: "customer",
        notes: "Preview saved from Visualize.",
        before: [{ src: beforeComp, label: "Before" }],
        after: [{ src: afterJpeg, label: "After (visualize)" }],
        source: "visualize"
      });
      lastShareId = saved.id;
      const url = shareUrlFor(saved.id);
      saveGalleryBtn.hidden = true;
      if (shareStatus) {
        shareStatus.innerHTML =
          'Saved on this device. <a href="' + escHtml(url) + '">Open in Projects</a>.';
      }
    } catch (err) {
      saveGalleryBtn.disabled = false;
      if (shareStatus) shareStatus.textContent = err.message || String(err);
    }
  });
}

buildPicker();
fitCamera();
setEmptyState(true);
showWork(false);
setStatus("Try a sample room, or take or upload a photo with a clear view of the floor.");
highlightSample();
updateHint();
updateSteps();
updateMeasureUI();
loop();

// Prefetch default texture into cache (optional)
loadFloorTexture(selectedTexId).catch(() => {});
