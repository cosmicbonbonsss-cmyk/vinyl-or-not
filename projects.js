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

function seedProjects() {
  return [
    {
      id: "seed-1",
      seed: true,
      title: "Living room — warm oak LVP",
      location: "Austin, TX",
      flooring: "LVP",
      role: "customer",
      notes:
        "Example composite: warm oak plank look on the empty-room before photo (not a finished install photo).",
      before: [{ src: "gallery/before-living-empty.jpg?v=20260930b", label: "Before" }],
      after: [{ src: "gallery/after-living-warm-oak.jpg?v=20260930c", label: "After" }],
      createdAt: "2026-01-12T12:00:00.000Z"
    },
    {
      id: "seed-2",
      seed: true,
      title: "Guest bath — medium oak refresh",
      location: "Denver, CO",
      flooring: "LVP",
      role: "customer",
      notes:
        "Example composite: checkered bath floor visible in before; medium oak plank look in after (not a finished install photo).",
      before: [{ src: "gallery/before-bath-checkered.jpg?v=20260930b", label: "Before" }],
      after: [{ src: "gallery/after-bath-medium-oak.jpg?v=20260930b", label: "After" }],
      createdAt: "2026-02-03T15:00:00.000Z"
    },
    {
      id: "seed-3",
      seed: true,
      title: "Open plan — warm oak plank look",
      location: "Seattle, WA",
      flooring: "LVP",
      role: "customer",
      notes:
        "Example composite: warm oak plank look on the open-plan before photo (not a finished install photo).",
      before: [{ src: "gallery/before-open-carpet.jpg?v=20260930b", label: "Before" }],
      after: [{ src: "gallery/after-open-warm-oak.jpg?v=20260930c", label: "After" }],
      createdAt: "2026-03-20T18:00:00.000Z"
    }
  ];
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
  if (!items || !items.length) {
    return '<div class="gallery-ph">' + escapeHtml(kind) + " (none)</div>";
  }
  return items
    .map(function (m) {
      if (m.src) {
        return (
          '<figure class="gallery-shot"><img src="' +
          escapeHtml(m.src) +
          '" alt="' +
          escapeHtml(m.label || kind) +
          '" loading="lazy" /><figcaption>' +
          escapeHtml(m.label || kind) +
          "</figcaption></figure>"
        );
      }
      return (
        '<figure class="gallery-shot gallery-demo ' +
        escapeHtml(m.css || "") +
        '"><span>' +
        escapeHtml(m.label || kind) +
        "</span><figcaption>" +
        escapeHtml(m.label || kind) +
        "</figcaption></figure>"
      );
    })
    .join("");
}

function cardHtml(p, highlightId) {
  const badges = [];
  if (p.seed) badges.push('<span class="badge success">Example</span>');
  badges.push('<span class="badge">' + escapeHtml(roleLabel(p.role)) + "</span>");

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

async function render() {
  if (!grid) return;
  updateSharedNotice();
  const highlightId = queryId();
  let remote = [];
  try {
    remote = await listProjects();
  } catch (e) {
    if (countEl) countEl.textContent = "Could not load projects right now.";
    remote = [];
  }
  const list = sortProjects(seedProjects().concat(remote));
  if (countEl) {
    countEl.textContent =
      list.length === 1 ? "1 project" : list.length + " projects";
  }
  grid.innerHTML =
    '<div class="gallery-section">' +
    (list.length ? list.map(function (p) {
      return cardHtml(p, highlightId);
    }).join("") : '<p class="hint">No projects yet.</p>') +
    "</div>";

  if (highlightId) {
    const el = document.getElementById("project-" + highlightId);
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "center" });
    } else if (countEl) {
      countEl.textContent += " · Shared link id not found in current feed.";
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
        formStatus.textContent = "Saving to gallery…";
        return addProject({
          title: form.title.value.trim(),
          location: form.location.value.trim(),
          flooring: form.flooring.value,
          role: form.role.value,
          notes: form.notes.value.trim(),
          before: before.length ? before : [{ label: "Before", css: "demo-before-a" }],
          after: after.length ? after : [{ label: "After", css: "demo-before-c" }],
          source: "form"
        });
      })
      .then(function (saved) {
        form.reset();
        const share = "projects.html?id=" + encodeURIComponent(saved.id);
        formStatus.innerHTML =
          'Saved on this device. <a href="' +
          escapeHtml(share) +
          '">Open local link</a>';
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
        "Exported " + payload.projects.length + " local backup project(s).";
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
        if (ieStatus) ieStatus.textContent = "Imported " + incoming.length + " into local backup.";
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
    clearLocalBackup();
    if (ieStatus)
      ieStatus.textContent = "Cleared local backup.";
    render();
  });
}

render();
