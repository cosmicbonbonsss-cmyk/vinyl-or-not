(function () {
  "use strict";

  var LOCAL_KEY = "von_gallery_local";
  var ACCOUNT_KEY = "von_trade_account";
  var PROFILE_KEY = "von_contractor_profile";
  var MAX_DATA_URL_CHARS = 450000; // soft limit per image for localStorage safety

  var grid = document.getElementById("gallery-grid");
  var countEl = document.getElementById("gallery-count");
  var form = document.getElementById("project-form");
  var formStatus = document.getElementById("project-form-status");
  var ieStatus = document.getElementById("ie-status");

  function hasProUnlock() {
    try {
      if (sessionStorage.getItem("vinylProPaid") === "1") return true;
      if (sessionStorage.getItem("von_pro_unlocked") === "1") return true;
      if (sessionStorage.getItem("von_report_unlocked") === "1") return true;
    } catch (e) {}
    var params = new URLSearchParams(window.location.search);
    if (params.get("pro") === "1" || params.get("report") === "1") {
      try {
        sessionStorage.setItem("vinylProPaid", "1");
        sessionStorage.setItem("von_pro_unlocked", "1");
      } catch (e2) {}
      return true;
    }
    return false;
  }

  function readJson(key) {
    try {
      var raw = localStorage.getItem(key);
      return raw ? JSON.parse(raw) : null;
    } catch (e) {
      return null;
    }
  }

  function writeJson(key, value) {
    localStorage.setItem(key, JSON.stringify(value));
  }

  function escapeHtml(s) {
    return String(s || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  /** Seeded demos — public for everyone; use texture JPGs as after shots */
  function seedProjects() {
    return [
      {
        id: "seed-1",
        seed: true,
        featured: true,
        title: "Living room — warm oak LVP (featured pro)",
        location: "Austin, TX",
        flooring: "LVP",
        role: "contractor",
        notes: "Click-lock warm oak over leveled slab. Seeded featured demo from a paid-contractor style profile.",
        before: [{ label: "Before", css: "demo-before-a" }],
        after: [{ src: "textures/warm-oak.jpg", label: "After" }],
        company: "Demo Ridge Flooring",
        profileId: "seed-ridge",
        createdAt: "2026-01-12T12:00:00.000Z"
      },
      {
        id: "seed-2",
        seed: true,
        featured: false,
        title: "Guest bath — gray oak refresh",
        location: "Denver, CO",
        flooring: "LVP",
        role: "customer",
        notes: "Homeowner upload demo. Old sheet vinyl out; gray oak planks in.",
        before: [{ label: "Before", css: "demo-before-b" }],
        after: [{ src: "textures/gray-oak.jpg", label: "After" }],
        createdAt: "2026-02-03T15:00:00.000Z"
      },
      {
        id: "seed-3",
        seed: true,
        featured: false,
        title: "Open plan — wide plank walnut look",
        location: "Seattle, WA",
        flooring: "LVP",
        role: "designer",
        notes: "Designer mood-board style demo using a wide-plank texture preview.",
        before: [{ label: "Before", css: "demo-before-c" }],
        after: [{ src: "textures/wide-plank-oak.jpg", label: "After" }],
        createdAt: "2026-03-20T18:00:00.000Z"
      }
    ];
  }

  function localProjects() {
    var list = readJson(LOCAL_KEY);
    return Array.isArray(list) ? list : [];
  }

  function saveLocal(list) {
    writeJson(LOCAL_KEY, list);
  }

  function allProjects() {
    return seedProjects().concat(localProjects());
  }

  function sortProjects(list) {
    return list.slice().sort(function (a, b) {
      if (!!a.featured !== !!b.featured) return a.featured ? -1 : 1;
      return String(b.createdAt || "").localeCompare(String(a.createdAt || ""));
    });
  }

  function roleLabel(role) {
    if (role === "contractor") return "Contractor";
    if (role === "pm") return "Property manager";
    if (role === "designer") return "Designer";
    return "Customer";
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
          " (demo)</figcaption></figure>"
        );
      })
      .join("");
  }

  function profileSnippet(p) {
    if (!p.featured) return "";
    var profile = readJson(PROFILE_KEY);
    var name = (p.company || (profile && profile.businessName) || "").trim();
    if (!name && !p.profileId) return "";
    var bits = [];
    if (name) bits.push("<strong>" + escapeHtml(name) + "</strong>");
    if (profile && profile.serviceArea && p.featured && !p.seed) {
      bits.push("Service area: " + escapeHtml(profile.serviceArea));
    }
    if (p.seed && p.company) {
      bits.push('Featured pro · <a href="pros.html#pro-tools">Pro profile tools</a>');
    } else if (p.featured) {
      bits.push('<a href="pros.html#pro-profile">View pro profile tools</a>');
    }
    return '<p class="featured-profile">' + bits.join(" · ") + "</p>";
  }

  function cardHtml(p) {
    var badges = [];
    if (p.featured) badges.push('<span class="badge success">Featured</span>');
    if (p.seed) badges.push('<span class="badge">Seeded demo</span>');
    else badges.push('<span class="badge">On this device</span>');
    badges.push('<span class="badge">' + escapeHtml(roleLabel(p.role)) + "</span>");

    return (
      '<article class="gallery-card' +
      (p.featured ? " featured" : "") +
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
      profileSnippet(p) +
      "</article>"
    );
  }

  function render() {
    if (!grid) return;
    var list = sortProjects(allProjects());
    var featuredCount = list.filter(function (p) {
      return p.featured;
    }).length;
    var localCount = localProjects().length;
    if (countEl) {
      countEl.textContent =
        list.length +
        " project(s) · " +
        featuredCount +
        " featured · " +
        localCount +
        " saved on this device. Featured pro jobs sort to the top.";
    }

    var featured = list.filter(function (p) {
      return p.featured;
    });
    var rest = list.filter(function (p) {
      return !p.featured;
    });

    var html = "";
    if (featured.length) {
      html += '<h3 class="gallery-section-title">Featured pro jobs</h3>';
      html += '<div class="gallery-section">' + featured.map(cardHtml).join("") + "</div>";
    }
    html += '<h3 class="gallery-section-title">All projects</h3>';
    html +=
      '<div class="gallery-section">' +
      (rest.length ? rest.map(cardHtml).join("") : '<p class="hint">No non-featured projects yet.</p>') +
      "</div>";
    grid.innerHTML = html;
  }

  function readFilesAsDataUrls(fileList, maxFiles) {
    var files = Array.prototype.slice.call(fileList || [], 0, maxFiles || 3);
    return Promise.all(
      files.map(function (file) {
        return new Promise(function (resolve, reject) {
          var reader = new FileReader();
          reader.onload = function () {
            var url = String(reader.result || "");
            if (url.length > MAX_DATA_URL_CHARS) {
              reject(new Error("Image too large for demo storage — try a smaller photo."));
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
      var beforeInput = document.getElementById("proj-before");
      var afterInput = document.getElementById("proj-after");
      var role = form.role.value;
      var paidContractor = hasProUnlock() && role === "contractor";
      var account = readJson(ACCOUNT_KEY);
      var profile = readJson(PROFILE_KEY);

      Promise.all([
        readFilesAsDataUrls(beforeInput.files, 3),
        readFilesAsDataUrls(afterInput.files, 3)
      ])
        .then(function (pair) {
          var before = pair[0];
          var after = pair[1];
          if (!before.length && !after.length) {
            throw new Error("Add at least one before or after photo.");
          }
          if (!before.length) {
            before = [{ label: "Before", css: "demo-before-a" }];
          }
          if (!after.length) {
            after = [{ label: "After", css: "demo-before-c" }];
          }
          var entry = {
            id: "local-" + Date.now(),
            seed: false,
            featured: !!paidContractor,
            title: form.title.value.trim(),
            location: form.location.value.trim(),
            flooring: form.flooring.value,
            role: role,
            notes: form.notes.value.trim(),
            before: before,
            after: after,
            company:
              (profile && profile.businessName) ||
              (account && account.company) ||
              "",
            createdAt: new Date().toISOString()
          };
          var list = localProjects();
          list.unshift(entry);
          try {
            saveLocal(list);
          } catch (err) {
            throw new Error(
              "Could not save (storage full?). Try fewer/smaller photos or clear local projects."
            );
          }
          form.reset();
          formStatus.textContent = paidContractor
            ? "Added as a Featured pro job (paid contractor unlock detected)."
            : "Added to gallery on this device" +
              (role === "contractor"
                ? " (contractor uploads are featured when Pro tools are unlocked — try ?pro=1)."
                : ".");
          render();
          document.getElementById("gallery").scrollIntoView({ behavior: "smooth" });
        })
        .catch(function (err) {
          formStatus.textContent = err.message || String(err);
        });
    });
  }

  var exportBtn = document.getElementById("export-json");
  var importInput = document.getElementById("import-json");
  var clearBtn = document.getElementById("clear-local");

  if (exportBtn) {
    exportBtn.addEventListener("click", function () {
      var payload = {
        type: "vinyl-or-not-gallery",
        version: 1,
        exportedAt: new Date().toISOString(),
        projects: localProjects()
      };
      var blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
      var a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = "vinyl-or-not-projects.json";
      a.click();
      URL.revokeObjectURL(a.href);
      ieStatus.textContent = "Exported " + payload.projects.length + " local project(s).";
    });
  }

  if (importInput) {
    importInput.addEventListener("change", function () {
      var file = importInput.files && importInput.files[0];
      if (!file) return;
      var reader = new FileReader();
      reader.onload = function () {
        try {
          var data = JSON.parse(String(reader.result || ""));
          var incoming = (data && data.projects) || data;
          if (!Array.isArray(incoming)) throw new Error("JSON must contain a projects array.");
          var merged = localProjects().concat(
            incoming.map(function (p, i) {
              p.id = p.id || "import-" + Date.now() + "-" + i;
              p.seed = false;
              return p;
            })
          );
          saveLocal(merged);
          ieStatus.textContent = "Imported " + incoming.length + " project(s).";
          render();
        } catch (err) {
          ieStatus.textContent = "Import failed: " + (err.message || err);
        }
        importInput.value = "";
      };
      reader.readAsText(file);
    });
  }

  if (clearBtn) {
    clearBtn.addEventListener("click", function () {
      try {
        localStorage.removeItem(LOCAL_KEY);
      } catch (e) {}
      ieStatus.textContent = "Cleared local projects (seeded demos remain).";
      render();
    });
  }

  // Honor ?pro=1 on this page for featured uploads
  hasProUnlock();
  render();
})();
