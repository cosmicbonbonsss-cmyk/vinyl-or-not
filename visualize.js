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
const shareTitle = document.getElementById("share-title");
const refLengthFt = document.getElementById("ref-length-ft");
const plankLenIn = document.getElementById("plank-len-in");
const plankWidIn = document.getElementById("plank-wid-in");
const priceSqft = document.getElementById("price-sqft");
const wastePct = document.getElementById("waste-pct");
const downloadPngBtn = document.getElementById("download-png");
const saveGalleryBtn = document.getElementById("save-gallery");
const copyShareBtn = document.getElementById("copy-share");
const webShareBtn = document.getElementById("web-share");

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
  if (workBlock) workBlock.classList.toggle("hidden", !on);
}

function updateSteps() {
  if (!stepList) return;
  const photo = !!photoMesh;
  const cornersDone = corners.length === 4;
  let current = "photo";
  if (photo && !lookTouched && corners.length === 0) current = "look";
  else if (photo && !cornersDone) current = "corners";
  else if (photo && cornersDone) current = "save";
  const order = ["photo", "look", "corners", "save"];
  const currentIdx = order.indexOf(current);
  stepList.querySelectorAll("li").forEach((li) => {
    const idx = order.indexOf(li.dataset.step);
    li.classList.toggle("is-current", idx === currentIdx);
    li.classList.toggle("is-done", idx > -1 && idx < currentIdx);
  });
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
  if (corners.length < 4) {
    hintEl.textContent = "Tap corner " + CORNER_LABELS[corners.length];
  } else {
    hintEl.textContent = "Floor quad set — pick a texture or drag corners (reset to re-tap)";
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

/**
 * Build a subdivided quad with bilinear corner warp + tiled UVs.
 * Subdivision improves texture sampling across a trapezoid (prototype perspective approx).
 */
function rebuildFloor() {
  if (floorMesh) {
    scene.remove(floorMesh);
    floorMesh.geometry.dispose();
    if (floorMesh.material.map && floorMesh.material.map !== activeFloorTex) {
      /* keep cached */
    }
    floorMesh.material.dispose();
    floorMesh = null;
  }
  if (corners.length !== 4 || !activeFloorTex) return;

  const seg = 48;
  const [fl, fr, br, bl] = corners;
  const positions = [];
  const uvs = [];
  const indices = [];

  const scale = parseFloat(tileScale.value) || 6;
  // width variant: narrow/wide adjust V vs U slightly via selectedTex
  const texMeta = TEXTURES.find((t) => t.id === selectedTexId) || TEXTURES[0];
  const baseU = (texMeta.repeat[0] / 6) * scale;
  const baseV = (texMeta.repeat[1] / 6) * scale;

  for (let j = 0; j <= seg; j++) {
    const ty = j / seg;
    for (let i = 0; i <= seg; i++) {
      const tx = i / seg;
      // bilinear: bottom edge FL->FR (ty=0), top BL->BR (ty=1) in image "depth"
      // corners order: 0 FL, 1 FR, 2 BR, 3 BL
      const bottom = new THREE.Vector2().lerpVectors(fl, fr, tx);
      const top = new THREE.Vector2().lerpVectors(bl, br, tx);
      const p = new THREE.Vector2().lerpVectors(bottom, top, ty);
      positions.push(p.x, p.y, 0.5);
      uvs.push(tx * baseU, ty * baseV);
    }
  }

  for (let j = 0; j < seg; j++) {
    for (let i = 0; i < seg; i++) {
      const a = j * (seg + 1) + i;
      const b = a + 1;
      const c = a + (seg + 1);
      const d = c + 1;
      // CCW as seen from the camera (+Z). The previous order was clockwise,
      // so the default front-face cull dropped the whole quad and the photo
      // showed through even after the texture loaded.
      indices.push(a, b, c, b, d, c);
    }
  }

  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  geo.setAttribute("uv", new THREE.Float32BufferAttribute(uvs, 2));
  geo.setIndex(indices);

  activeFloorTex.wrapS = THREE.RepeatWrapping;
  activeFloorTex.wrapT = THREE.RepeatWrapping;
  activeFloorTex.colorSpace = THREE.SRGBColorSpace;
  activeFloorTex.anisotropy = Math.min(8, renderer.capabilities.getMaxAnisotropy());
  activeFloorTex.needsUpdate = true;

  const mat = new THREE.MeshBasicMaterial({
    map: activeFloorTex,
    transparent: true,
    opacity: 0.92,
    depthWrite: false,
    depthTest: false,
    side: THREE.DoubleSide
  });

  floorMesh = new THREE.Mesh(geo, mat);
  floorMesh.renderOrder = 2;
  scene.add(floorMesh);
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

function setPhotoFromFile(file) {
  if (photoUrl) URL.revokeObjectURL(photoUrl);
  clearScenePhoto();
  photoOriginalDataUrl = null;
  lastShareId = null;
  setShareButtons(null);
  if (shareStatus) shareStatus.textContent = "";

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
    setStatus(lookTouched
      ? "Step 3: tap four floor corners — front-left, front-right, back-right, back-left."
      : "Step 2: pick a flooring look, then tap the four floor corners.");
    updateHint();
    updateSteps();
    updateMeasureUI();
    render();
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
  lastShareId = null;
  setShareButtons(null);
  if (shareStatus) shareStatus.textContent = "";
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
  fitCamera();
  setStatus("Step 1: take or upload a photo with a clear view of the floor.");
  updateSteps();
  updateMeasureUI();
  render();
}

function resetCorners() {
  corners = [];
  if (floorMesh) {
    scene.remove(floorMesh);
    floorMesh.geometry.dispose();
    floorMesh.material.dispose();
    floorMesh = null;
  }
  rebuildMarkers();
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

function canvasSnapshotDataUrl() {
  render();
  return canvas.toDataURL("image/png");
}

function shareUrlFor(id) {
  const base = window.location.href.replace(/[^/]*$/, "");
  return base + "projects.html?id=" + encodeURIComponent(id);
}

function setShareButtons(id) {
  lastShareId = id || null;
  // Projects live in this browser only, so a copied link would not open for anyone else.
  if (copyShareBtn) {
    copyShareBtn.classList.add("hidden");
    copyShareBtn.disabled = true;
  }
  if (webShareBtn) webShareBtn.classList.add("hidden");
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

function render() {
  renderer.render(scene, camera);
}

function loop() {
  render();
  requestAnimationFrame(loop);
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


[refLengthFt, plankLenIn, plankWidIn, priceSqft, wastePct].forEach((el) => {
  if (el) el.addEventListener("input", updateMeasureUI);
});

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

if (downloadPngBtn) {
  downloadPngBtn.addEventListener("click", () => {
    if (!photoMesh || corners.length !== 4) {
      if (shareStatus) shareStatus.textContent = "Set photo, corners, and texture first.";
      return;
    }
    const a = document.createElement("a");
    a.href = withHiddenMarkers(() => canvasSnapshotDataUrl());
    a.download = "vinyl-or-not-visualize.png";
    a.click();
    if (shareStatus) shareStatus.textContent = "PNG downloaded.";
  });
}

if (saveGalleryBtn) {
  saveGalleryBtn.addEventListener("click", async () => {
    if (!photoMesh || corners.length !== 4 || !activeFloorTex) {
      if (shareStatus) shareStatus.textContent = "Set photo, four corners, and a texture first.";
      return;
    }
    if (shareStatus) {
      shareStatus.textContent = "Saving on this device…";
    }
    saveGalleryBtn.disabled = true;
    try {
      const afterPng = withHiddenMarkers(() => canvasSnapshotDataUrl());
      const afterJpeg = await compressDataUrl(afterPng, 1400, 0.78);
      let beforeSrc = photoOriginalDataUrl;
      if (!beforeSrc && photoUrl) {
        // fallback: snapshot without floor is hard; use current canvas photo mesh only
        beforeSrc = afterJpeg;
      }
      const beforeComp = beforeSrc ? await compressDataUrl(beforeSrc, 1400, 0.72) : afterJpeg;
      const texMeta = TEXTURES.find((t) => t.id === selectedTexId);
      const title =
        (shareTitle && shareTitle.value.trim()) ||
        ("Visualize preview — " + ((texMeta && texMeta.label) || "LVP"));
      const saved = await addProject({
        title,
        location: "",
        flooring: "LVP",
        role: "customer",
        notes: "Preview saved from Visualize.",
        before: [{ src: beforeComp, label: "Before" }],
        after: [{ src: afterJpeg, label: "After (visualize)" }],
        source: "visualize"
      });
      const url = shareUrlFor(saved.id);
      setShareButtons(saved.id);
      if (shareStatus) {
        shareStatus.innerHTML =
          'Saved on this device. <a href="' + url + '">Open it in Projects</a>. It will not show on someone else’s phone.';
      }
    } catch (err) {
      if (shareStatus) shareStatus.textContent = err.message || String(err);
    } finally {
      saveGalleryBtn.disabled = false;
    }
  });
}

if (copyShareBtn) {
  copyShareBtn.addEventListener("click", async () => {
    if (!lastShareId) return;
    const url = shareUrlFor(lastShareId);
    try {
      await navigator.clipboard.writeText(url);
      if (shareStatus) shareStatus.textContent = "Share link copied.";
    } catch (e) {
      if (shareStatus) shareStatus.textContent = "Copy failed — select the link manually.";
    }
  });
}

if (webShareBtn) {
  webShareBtn.addEventListener("click", async () => {
    if (!lastShareId || typeof navigator.share !== "function") return;
    const url = shareUrlFor(lastShareId);
    try {
      await navigator.share({
        title: (shareTitle && shareTitle.value) || "Vinyl or Not project",
        text: "Before & after flooring preview",
        url
      });
    } catch (e) {
      /* user cancelled */
    }
  });
}

buildPicker();
fitCamera();
setEmptyState(true);
showWork(false);
setStatus("Step 1: take or upload a photo with a clear view of the floor.");
updateHint();
updateSteps();
updateMeasureUI();
loop();

// Prefetch default texture into cache (optional)
loadFloorTexture(TEXTURES[0].id).catch(() => {});
