import {
  listProjects,
  addProject,
  listLocalBackup,
  replaceLocalBackup,
  clearLocalBackup,
  MAX_DATA_URL_CHARS
} from "./gallery-store.js";

const grid = document.getElementById("gallery-grid");
const countEl = document.getElementById("gallery-count");
const form = document.getElementById("project-form");
const formStatus = document.getElementById("project-form-status");
const ieStatus = document.getElementById("ie-status");
const sharedNotice = document.getElementById("shared-mode-notice");
const submitBtn = document.getElementById("proj-submit");

function escapeHtml(s) {
  return String(s || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function sortProjects(list) {
  return list.slice().sort(function (a, b) {
    return String(b.createdAt || "").localeCompare(String(a.createdAt || ""));
  });
}

function roleLabel(role) {
  if (role === "friend") return "Helping a friend";
  if (role === "other") return "Other";
  return "Homeowner / DIY";
}

function queryId() {
  try {
    return new URLSearchParams(window.location.search).get("id");
  } catch (e) {
    return null;
  }
}

function renderMedia(items, kind) {
  var photos = (items || []).filter(function (m) {
    return m && m.src;
  });
  if (!photos.length) {
    return '<div class="gallery-ph">No ' + escapeHtml(String(kind).toLowerCase()) + " photo</div>";
  }
  return photos
    .map(function (m) {
      return (
        '<figure class="gallery-shot"><img src="' +
        escapeHtml(m.src) +
        '" alt="' +
        escapeHtml(m.label || kind) +
        '" loading="lazy" /><figcaption>' +
        escapeHtml(m.label || kind) +
        "</figcaption></figure>"
      );
    })
    .join("");
}

function cardHtml(p, highlightId) {
  const badges = ['<span class="badge">' + escapeHtml(roleLabel(p.role)) + "</span>"];

  const featured = highlightId && p.id === highlightId ? " featured" : "";

  return (
    '<article class="gallery-card' +
    featured +
    '" id="project-' +
    escapeHtml(p.id) +
    '" data-id="' +
    escapeHtml(p.id) +
    '">' +
    '<div class="gallery-badges">' +
    badges.join(" ") +
    "</div>" +
    "<h3>" +
    escapeHtml(p.title) +
    "</h3>" +
    '<p class="hint">' +
    escapeHtml(p.flooring) +
    (p.location ? " · " + escapeHtml(p.location) : "") +
    "</p>" +
    '<div class="ba-row">' +
    '<div class="ba-col"><h4>Before</h4>' +
    renderMedia(p.before, "Before") +
    "</div>" +
    '<div class="ba-col"><h4>After</h4>' +
    renderMedia(p.after, "After") +
    "</div>" +
    "</div>" +
    (p.notes ? "<p>" + escapeHtml(p.notes) + "</p>" : "") +
    "</article>"
  );
}

function updateSharedNotice() {
  // Keep config/status banners hidden from visitors.
  if (sharedNotice) {
    sharedNotice.hidden = true;
    sharedNotice.textContent = "";
  }
  if (submitBtn) submitBtn.textContent = "Save on this device";
}

const SEED_IDS = { "seed-1": 1, "seed-2": 1, "seed-3": 1 };

function isSeedProject(p) {
  if (!p) return false;
  if (p.seed || p.source === "seed") return true;
  if (SEED_IDS[p.id]) return true;
  const media = [].concat(p.before || [], p.after || []);
  return media.some(function (m) {
    const src = String((m && m.src) || "");
    return (
      src.indexOf("gallery/before-living-empty") !== -1 ||
      src.indexOf("gallery/after-living-warm-oak") !== -1 ||
      src.indexOf("gallery/before-bath-checkered") !== -1 ||
      src.indexOf("gallery/after-bath-medium-oak") !== -1 ||
      src.indexOf("gallery/before-open-carpet") !== -1 ||
      src.indexOf("gallery/after-open-warm-oak") !== -1
    );
  });
}

function purgeSeedProjectsFromLocal() {
  try {
    const list = listLocalBackup();
    const kept = list.filter(function (p) {
      return !isSeedProject(p);
    });
    if (kept.length !== list.length) replaceLocalBackup(kept);
  } catch (e) {}
}

async function render() {
  if (!grid) return;
  updateSharedNotice();
  purgeSeedProjectsFromLocal();
  const highlightId = queryId();
  let remote = [];
  try {
    remote = await listProjects();
  } catch (e) {
    if (countEl) countEl.textContent = "Could not load projects right now.";
    remote = [];
  }
  const list = sortProjects(remote.filter(function (p) {
    return !isSeedProject(p);
  }));
  if (countEl) {
    countEl.textContent = list.length
      ? (list.length === 1 ? "1 project on this device" : list.length + " projects on this device")
      : "No projects yet. Add one below, or save a preview from Visualize.";
  }
  grid.innerHTML =
    '<div class="gallery-section">' +
    (list.length ? list.map(function (p) {
      return cardHtml(p, highlightId);
    }).join("") : '<p class="hint">Nothing here yet. Use the form under this list, or open <a href="visualize.html">Visualize</a>, mark a floor, and choose Save to gallery.</p>') +
    "</div>";

  if (highlightId) {
    const el = document.getElementById("project-" + highlightId);
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "center" });
    } else if (countEl) {
      countEl.textContent += " That link doesn’t match a project saved in this browser.";
    }
  }
}

function readFilesAsDataUrls(fileList, maxFiles) {
  const files = Array.prototype.slice.call(fileList || [], 0, maxFiles || 3);
  return Promise.all(
    files.map(function (file) {
      return new Promise(function (resolve, reject) {
        const reader = new FileReader();
        reader.onload = function () {
          const url = String(reader.result || "");
          if (url.length > MAX_DATA_URL_CHARS) {
            reject(new Error("Image too large — try a smaller photo."));
            return;
          }
          resolve({ src: url, label: file.name });
        };
        reader.onerror = function () {
          reject(new Error("Could not read " + file.name));
        };
        reader.readAsDataURL(file);
      });
    })
  );
}

if (form) {
  form.addEventListener("submit", function (e) {
    e.preventDefault();
    formStatus.textContent = "Reading photos…";
    const beforeInput = document.getElementById("proj-before");
    const afterInput = document.getElementById("proj-after");

    Promise.all([
      readFilesAsDataUrls(beforeInput.files, 3),
      readFilesAsDataUrls(afterInput.files, 3)
    ])
      .then(function (pair) {
        const before = pair[0];
        const after = pair[1];
        if (!before.length && !after.length) {
          throw new Error("Add at least one before or after photo.");
        }
        formStatus.textContent = "Saving on this device…";
        return addProject({
          title: form.title.value.trim(),
          location: form.location.value.trim(),
          flooring: form.flooring.value,
          role: form.role.value,
          notes: form.notes.value.trim(),
          before: before,
          after: after,
          source: "form"
        });
      })
      .then(function (saved) {
        form.reset();
        const share = "projects.html?id=" + encodeURIComponent(saved.id);
        formStatus.innerHTML =
          'Saved on this device. <a href="' +
          escapeHtml(share) +
          '">Show it in the list</a>. It stays in this browser only.';
        return render();
      })
      .catch(function (err) {
        formStatus.textContent = err.message || String(err);
      });
  });
}

const exportBtn = document.getElementById("export-json");
const importInput = document.getElementById("import-json");
const clearBtn = document.getElementById("clear-local");

if (exportBtn) {
  exportBtn.addEventListener("click", function () {
    const payload = {
      type: "vinyl-or-not-gallery",
      version: 1,
      exportedAt: new Date().toISOString(),
      projects: listLocalBackup()
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "vinyl-or-not-projects.json";
    a.click();
    URL.revokeObjectURL(a.href);
    if (ieStatus)
      ieStatus.textContent =
        "Downloaded a copy of " + payload.projects.length + " project(s) from this browser.";
  });
}

if (importInput) {
  importInput.addEventListener("change", function () {
    const file = importInput.files && importInput.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = function () {
      try {
        const data = JSON.parse(String(reader.result || ""));
        const incoming = (data && data.projects) || data;
        if (!Array.isArray(incoming)) throw new Error("JSON must contain a projects array.");
        const merged = listLocalBackup().concat(
          incoming.map(function (p, i) {
            p.id = p.id || "import-" + Date.now() + "-" + i;
            p.seed = false;
            return p;
          })
        );
        replaceLocalBackup(merged);
        if (ieStatus) ieStatus.textContent = "Restored " + incoming.length + " project(s) on this device.";
        render();
      } catch (err) {
        if (ieStatus) ieStatus.textContent = "Import failed: " + (err.message || err);
      }
      importInput.value = "";
    };
    reader.readAsText(file);
  });
}

if (clearBtn) {
  clearBtn.addEventListener("click", function () {
    var existing = listLocalBackup();
    if (!existing.length) {
      if (ieStatus) ieStatus.textContent = "There are no saved projects on this device.";
      return;
    }
    var ok = window.confirm("Delete every project saved in this browser? This cannot be undone.");
    if (!ok) return;
    clearLocalBackup();
    if (ieStatus) ieStatus.textContent = "Deleted the projects saved on this device.";
    render();
  });
}

render();
