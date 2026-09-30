import * as THREE from "three";

const TEXTURES = [
  { id: "light-oak", label: "Light oak", file: "textures/light-oak.jpg", repeat: [6, 6] },
  { id: "medium-oak", label: "Medium oak", file: "textures/medium-oak.jpg", repeat: [6, 6] },
  { id: "warm-oak", label: "Warm oak", file: "textures/warm-oak.jpg", repeat: [6, 6] },
  { id: "honey-oak", label: "Honey oak", file: "textures/honey-oak.jpg", repeat: [5, 5] },
  { id: "gray-oak", label: "Gray oak", file: "textures/gray-oak.jpg", repeat: [6, 6] },
  { id: "ash-gray", label: "Ash gray", file: "textures/ash-gray.jpg", repeat: [6, 6] },
  { id: "whitewash", label: "Whitewash", file: "textures/whitewash.jpg", repeat: [6, 6] },
  { id: "bleached-oak", label: "Bleached oak", file: "textures/bleached-oak.jpg", repeat: [6, 6] },
  { id: "walnut", label: "Walnut", file: "textures/walnut.jpg", repeat: [5, 5] },
  { id: "dark-walnut", label: "Dark walnut", file: "textures/dark-walnut.jpg", repeat: [5, 5] },
  { id: "narrow-oak", label: "Narrow oak", file: "textures/narrow-oak.jpg", repeat: [8, 8] },
  { id: "wide-plank-oak", label: "Wide plank", file: "textures/wide-plank-oak.jpg", repeat: [4, 4] }
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

const renderer = new THREE.WebGLRenderer({
  canvas,
  antialias: true,
  alpha: false,
  preserveDrawingBuffer: true
});
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
renderer.setClearColor(0x1c1a17, 1);

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
/** Corners in world coords (origin center, y up) — order FL, FR, BR, BL */
/** @type {THREE.Vector2[]} */
let corners = [];
/** @type {string} */
let selectedTexId = TEXTURES[0].id;
/** @type {THREE.Texture|null} */
let activeFloorTex = null;
const texCache = new Map();

function setStatus(msg) {
  statusEl.textContent = msg;
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
      indices.push(a, c, b, b, c, d);
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
    depthWrite: false
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

  photoUrl = URL.createObjectURL(file);
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
    fitCamera();
    setStatus("Step 2: tap four floor corners — front-left, front-right, back-right, back-left.");
    updateHint();
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
  photoInput.value = "";
  clearScenePhoto();
  resetBtn.disabled = true;
  clearBtn.disabled = true;
  setPickerEnabled(false);
  fitCamera();
  setStatus("Step 1: upload a photo of a room with a visible floor.");
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
  render();
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
    btn.className = "tex-opt" + (idx === 0 ? " selected" : "");
    btn.dataset.id = t.id;
    btn.setAttribute("role", "option");
    btn.disabled = true;
    btn.innerHTML = `<img src="${t.file}" alt="" loading="lazy" /><span>${t.label}</span>`;
    btn.addEventListener("click", () => {
      if (corners.length !== 4) {
        setStatus("Set all four corners before applying a texture.");
        return;
      }
      loadFloorTexture(t.id)
        .then(() => {
          setStatus("Applied “" + t.label + "”. Adjust tile scale if planks look too large/small.");
          render();
        })
        .catch(() => setStatus("Texture failed to load."));
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
      setStatus("Quad complete — choose a plank texture below.");
      loadFloorTexture(selectedTexId).then(() => render());
    } else {
      setStatus("Corner " + corners.length + "/4 set — next: " + CORNER_LABELS[corners.length]);
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
  if (f) setPhotoFromFile(f);
});
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

buildPicker();
fitCamera();
setStatus("Step 1: upload a photo of a room with a visible floor.");
updateHint();
loop();

// Prefetch default texture into cache (optional)
loadFloorTexture(TEXTURES[0].id).catch(() => {});
