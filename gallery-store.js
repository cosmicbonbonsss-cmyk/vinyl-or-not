/**
 * Shared gallery store — Firestore when configured, else localStorage fallback.
 * Exports: listProjects(), addProject(project), isSharedConfigured(), getMode()
 */
const LOCAL_KEY = "von_gallery_local";
const MAX_DATA_URL_CHARS = 450000;
const FB_VERSION = "10.14.1";

function cfg() {
  return window.VON_GALLERY || {};
}

function firebaseReady() {
  const f = cfg().firebase || {};
  return Boolean(
    f.apiKey &&
      f.authDomain &&
      f.projectId &&
      f.appId &&
      String(f.apiKey).trim() &&
      String(f.projectId).trim()
  );
}

export function isSharedConfigured() {
  const provider = cfg().provider || "firebase";
  if (provider === "local-fallback") return false;
  return firebaseReady();
}

export function getMode() {
  return isSharedConfigured() ? "firebase" : "local-fallback";
}

function readLocal() {
  try {
    const raw = localStorage.getItem(LOCAL_KEY);
    const list = raw ? JSON.parse(raw) : [];
    return Array.isArray(list) ? list : [];
  } catch (e) {
    return [];
  }
}

function writeLocal(list) {
  localStorage.setItem(LOCAL_KEY, JSON.stringify(list));
}

function uid() {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return "p-" + Date.now().toString(36) + "-" + Math.random().toString(36).slice(2, 9);
}

function normalizeProject(p, fallbackId) {
  if (!p || typeof p !== "object") return null;
  return {
    id: p.id || fallbackId || uid(),
    seed: Boolean(p.seed),
    title: String(p.title || "Untitled project"),
    location: String(p.location || ""),
    flooring: String(p.flooring || "LVP"),
    role: String(p.role || "customer"),
    notes: String(p.notes || ""),
    before: Array.isArray(p.before) ? p.before : [],
    after: Array.isArray(p.after) ? p.after : [],
    createdAt: p.createdAt || new Date().toISOString(),
    source: p.source || (p.seed ? "seed" : "user")
  };
}

let fbApp = null;
let fbDb = null;
let fbStorage = null;
let fbMods = null;

async function loadFirebase() {
  if (fbMods) return fbMods;
  const [appMod, fsMod, stMod] = await Promise.all([
    import(`https://www.gstatic.com/firebasejs/${FB_VERSION}/firebase-app.js`),
    import(`https://www.gstatic.com/firebasejs/${FB_VERSION}/firebase-firestore.js`),
    import(`https://www.gstatic.com/firebasejs/${FB_VERSION}/firebase-storage.js`)
  ]);
  fbMods = { appMod, fsMod, stMod };
  return fbMods;
}

async function ensureFirebase() {
  if (!firebaseReady()) throw new Error("Firebase is not configured.");
  if (fbDb) return { db: fbDb, storage: fbStorage, mods: fbMods };
  const mods = await loadFirebase();
  const f = cfg().firebase;
  fbApp = mods.appMod.initializeApp({
    apiKey: f.apiKey,
    authDomain: f.authDomain,
    projectId: f.projectId,
    storageBucket: f.storageBucket || undefined,
    messagingSenderId: f.messagingSenderId || undefined,
    appId: f.appId
  });
  fbDb = mods.fsMod.getFirestore(fbApp);
  if (f.storageBucket && String(f.storageBucket).trim()) {
    try {
      fbStorage = mods.stMod.getStorage(fbApp);
    } catch (e) {
      fbStorage = null;
    }
  }
  return { db: fbDb, storage: fbStorage, mods };
}

async function maybeUploadDataUrl(storage, mods, projectId, kind, index, src) {
  if (!storage || !src || typeof src !== "string") return src;
  if (!src.startsWith("data:")) return src;
  const path = `projects/${projectId}/${kind}-${index}.jpg`;
  const storageRef = mods.stMod.ref(storage, path);
  await mods.stMod.uploadString(storageRef, src, "data_url");
  return mods.stMod.getDownloadURL(storageRef);
}

async function hydrateMedia(storage, mods, projectId, items, kind) {
  if (!items || !items.length) return items || [];
  const out = [];
  for (let i = 0; i < items.length; i++) {
    const m = Object.assign({}, items[i]);
    if (m.src && m.src.startsWith("data:")) {
      if (storage) {
        try {
          m.src = await maybeUploadDataUrl(storage, mods, projectId, kind, i, m.src);
        } catch (e) {
          if (String(m.src).length > MAX_DATA_URL_CHARS) {
            throw new Error(
              "Photo too large for Firestore fallback — enable Storage or use a smaller image."
            );
          }
        }
      } else if (String(m.src).length > MAX_DATA_URL_CHARS) {
        throw new Error("Image too large for demo storage — try a smaller photo.");
      }
    }
    out.push(m);
  }
  return out;
}

async function listFromFirebase() {
  const { db, mods } = await ensureFirebase();
  const colName = cfg().collection || "projects";
  const colRef = mods.fsMod.collection(db, colName);
  let snap;
  try {
    const q = mods.fsMod.query(colRef, mods.fsMod.orderBy("createdAt", "desc"));
    snap = await mods.fsMod.getDocs(q);
  } catch (e) {
    snap = await mods.fsMod.getDocs(colRef);
  }
  const list = [];
  snap.forEach((doc) => {
    const data = doc.data() || {};
    list.push(normalizeProject(Object.assign({}, data, { id: doc.id }), doc.id));
  });
  return list;
}

async function addToFirebase(project) {
  const { db, storage, mods } = await ensureFirebase();
  const colName = cfg().collection || "projects";
  const id = project.id || uid();
  const before = await hydrateMedia(storage, mods, id, project.before, "before");
  const after = await hydrateMedia(storage, mods, id, project.after, "after");
  const payload = normalizeProject(
    Object.assign({}, project, {
      id,
      before,
      after,
      createdAt: project.createdAt || new Date().toISOString(),
      seed: false,
      source: project.source || "user"
    }),
    id
  );
  // Firestore doc id = project id for shareable ?id=
  const rest = Object.assign({}, payload);
  delete rest.id;
  await mods.fsMod.setDoc(mods.fsMod.doc(db, colName, id), rest);
  return payload;
}

/**
 * List user/shared projects.
 */
export async function listProjects() {
  if (isSharedConfigured()) {
    try {
      return await listFromFirebase();
    } catch (e) {
      console.warn("[gallery-store] Firebase list failed, using local fallback:", e);
      return readLocal();
    }
  }
  return readLocal();
}

/**
 * Add a project. Returns the saved project (with id).
 */
export async function addProject(project) {
  const entry = normalizeProject(project, project && project.id);
  entry.seed = false;
  entry.createdAt = entry.createdAt || new Date().toISOString();

  if (isSharedConfigured()) {
    try {
      return await addToFirebase(entry);
    } catch (e) {
      console.warn("[gallery-store] Firebase add failed:", e);
      throw e;
    }
  }

  // Local fallback
  const before = entry.before || [];
  const after = entry.after || [];
  for (const m of before.concat(after)) {
    if (m && m.src && String(m.src).length > MAX_DATA_URL_CHARS) {
      throw new Error("Image too large for demo storage — try a smaller photo.");
    }
  }
  const list = readLocal();
  list.unshift(entry);
  try {
    writeLocal(list);
  } catch (err) {
    throw new Error(
      "Could not save (storage full?). Try fewer/smaller photos or clear local backup."
    );
  }
  return entry;
}

/** Optional backup helpers for import/export UI */
export function listLocalBackup() {
  return readLocal();
}

export function replaceLocalBackup(list) {
  writeLocal(Array.isArray(list) ? list : []);
}

export function clearLocalBackup() {
  try {
    localStorage.removeItem(LOCAL_KEY);
  } catch (e) {}
}

export { MAX_DATA_URL_CHARS, LOCAL_KEY };
