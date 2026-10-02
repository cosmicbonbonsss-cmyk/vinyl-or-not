(function () {
  "use strict";

  var MAX_PHOTOS = 3;
  var photos = [];
  var answers = null;
  var cameraCtl = null;

  var sections = ["landing", "photos", "checklist", "report"];

  var LOOKS = {
    "white-oak": "White oak",
    "natural-oak": "Natural oak",
    "medium-oak": "Medium oak",
    "warm-oak": "Warm oak",
    "honey-oak": "Honey oak",
    "golden-oak": "Golden oak",
    "maple": "Maple",
    "hickory": "Hickory",
    "acacia": "Acacia",
    "cherry": "Cherry",
    "walnut": "Walnut",
    "walnut-plank": "Walnut plank",
    "dark-walnut": "Dark walnut",
    "espresso": "Espresso",
    "pine-natural": "Natural pine",
    "gray-oak": "Gray oak",
    "gray-wash": "Gray wash",
    "narrow-plank": "Narrow plank",
    "wide-plank": "Wide plank",
    "unsure": "Not sure yet"
  };

  function $(id) { return document.getElementById(id); }

  function show(id) {
    if (cameraCtl && id !== "photos") cameraCtl.stop();
    sections.forEach(function (s) {
      var el = $(s);
      if (el) el.classList.toggle("hidden", s !== id);
    });
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function scoreAnswers(a) {
    var score = { lvp: 0, tile: 0, hardwood: 0, laminate: 0 };

    if (a.seams === "tight-click") { score.lvp += 2; score.laminate += 1; }
    if (a.seams === "grout") score.tile += 3;
    if (a.seams === "wide-wood") score.hardwood += 2;

    if (a.texture === "embossed") { score.lvp += 2; score.laminate += 1; }
    if (a.texture === "smooth-hard") score.tile += 2;
    if (a.texture === "real-wood") score.hardwood += 3;

    if (a.underlay === "foam-gray") { score.lvp += 2; score.laminate += 1; }
    if (a.underlay === "concrete") { score.tile += 1; score.lvp += 1; }
    if (a.underlay === "wood-sub") { score.hardwood += 1; score.laminate += 1; }

    if (a.edges === "click") { score.lvp += 2; score.laminate += 1; }
    if (a.edges === "glued") { score.tile += 1; score.lvp += 1; }
    if (a.edges === "nailed") score.hardwood += 3;

    var best = "lvp";
    var bestScore = -1;
    Object.keys(score).forEach(function (k) {
      if (score[k] > bestScore) { bestScore = score[k]; best = k; }
    });
    return best;
  }

  function guessFromAnswers(a) {
    var labels = {
      lvp: "Likely click-lock LVP (luxury vinyl plank)",
      laminate: "Likely laminate with a photographic wear layer",
      tile: "Likely ceramic or porcelain tile",
      hardwood: "Likely solid or engineered hardwood"
    };
    var wearNote = "";
    if (a.wear === "peaking") wearNote = " — peaking or lifted edges noted";
    else if (a.wear === "heavy") wearNote = " — heavy wear or damage noted";
    else wearNote = " — surface wear looks light from your answers";
    return labels[scoreAnswers(a)] + wearNote + ".";
  }

  function reportCopy(a) {
    var kind = scoreAnswers(a);
    var typeName = {
      lvp: "click-lock LVP (luxury vinyl plank)",
      laminate: "laminate",
      tile: "ceramic or porcelain tile",
      hardwood: "solid or engineered hardwood"
    }[kind];

    var condition = "Light scuffs; the surface looks mostly intact from what you marked.";
    var plan = "You can usually clean and live with light wear. Replace when the wear layer is cut through or planks are loose.";
    if (a.wear === "peaking") {
      condition = "Edge peaking, cupping, or lifted seams — that often means moisture, a flatness problem, or a joint that never locked.";
      plan = "Don’t refinish over peaking. Find the cause (moisture or subfloor) before you cover it with a new floor.";
    } else if (a.wear === "heavy") {
      condition = "Deep wear-through, cracks, or missing pieces.";
      plan = "Plan on replacement in the worn area. A surface coating will not bring back a worn vinyl print or a cracked tile.";
    }

    var refinish = {
      lvp: "Replace rather than refinish. LVP has a printed wear layer — it cannot be sanded like hardwood.",
      laminate: "Replace rather than refinish. The photo layer is thin and is not meant to be sanded.",
      tile: "Regrout or replace cracked pieces. Glaze is not refinished like wood.",
      hardwood: "Solid hardwood can sometimes be screened or refinished if the wear is only in the finish and the boards are thick enough. Engineered boards may only allow a light screen — check the wear layer."
    }[kind];

    var cost = {
      lvp: "A common DIY LVP material band is roughly $2–$5 per sq ft before waste, transitions, and any leveling. Installed quotes often land higher.",
      laminate: "Laminate material often sits in a similar band to LVP, sometimes a bit less. Add waste, transitions, and underlayment if the planks don’t include a pad.",
      tile: "Tile material varies widely. Budget extra for thinset, grout, and a flat substrate — labor is usually the larger share if you hire it out.",
      hardwood: "Hardwood material is usually more than vinyl plank. Refinishing an existing floor can cost less than a full replacement if the boards are sound."
    }[kind];

    var subfloor = "Nothing in your answers flags a specific subfloor. Still check flatness and moisture before new flooring goes down.";
    if (a.underlay === "concrete") {
      subfloor = "You noted concrete or thinset. Test slab moisture and confirm the new product is approved over that slab before you buy.";
    } else if (a.underlay === "wood-sub") {
      subfloor = "You noted a plywood or OSB subfloor. Check for squeaks, soft spots, and flatness. Fasten loose panels before a floating floor.";
    } else if (a.underlay === "foam-gray") {
      subfloor = "A foam pad or gray/black core fits a floating vinyl or laminate plank. Don’t stack a second thick pad unless the new product says to.";
    }

    var steps = [
      "Measure each room and add waste before you order — use the Measure tool.",
      "Confirm flatness. High and low spots telegraph through thin planks and tile.",
      "Read the product’s moisture limit and underlayment rules.",
      "Plan transitions at doorways and keep one spare box for later repairs."
    ];
    if (a.wear === "peaking" || a.underlay === "concrete") {
      steps.unshift("Pause if you suspect moisture. A new floor over a wet slab fails even when the plank is labeled waterproof.");
    }

    var lookId = a.look || "unsure";
    var lookName = LOOKS[lookId] || "Not sure yet";
    var lookLine = lookId === "unsure"
      ? "You weren’t sure which look to compare. Visualize has oak, walnut, maple, hickory, acacia, gray wash, and wide plank you can preview on a room photo."
      : "Look to compare: " + lookName + ". Open Visualize and choose that same name to preview it on a room photo.";

    return {
      summary: guessFromAnswers(a),
      typeName: typeName,
      condition: condition,
      refinish: refinish,
      cost: cost,
      subfloor: subfloor,
      steps: steps,
      lookLine: lookLine,
      lookId: lookId
    };
  }

  function fillReport(a) {
    var body = $("report-body");
    var r = reportCopy(a);
    body.innerHTML = "";

    var summary = document.createElement("p");
    summary.className = "report-lead";
    summary.textContent = r.summary;
    body.appendChild(summary);

    var look = document.createElement("p");
    look.textContent = r.lookLine;
    body.appendChild(look);

    var list = document.createElement("ul");
    [
      ["Type", r.typeName],
      ["Condition", r.condition],
      ["Refinish vs replace", r.refinish],
      ["Cost band", r.cost],
      ["Subfloor", r.subfloor]
    ].forEach(function (pair) {
      var li = document.createElement("li");
      var strong = document.createElement("strong");
      strong.textContent = pair[0] + ": ";
      li.appendChild(strong);
      li.appendChild(document.createTextNode(pair[1]));
      list.appendChild(li);
    });
    var stepsLi = document.createElement("li");
    var stepsLabel = document.createElement("strong");
    stepsLabel.textContent = "Next steps: ";
    stepsLi.appendChild(stepsLabel);
    var ol = document.createElement("ol");
    r.steps.forEach(function (step) {
      var li = document.createElement("li");
      li.textContent = step;
      ol.appendChild(li);
    });
    stepsLi.appendChild(ol);
    list.appendChild(stepsLi);
    body.appendChild(list);

    if (r.lookId && r.lookId !== "unsure") {
      var link = document.createElement("p");
      var aEl = document.createElement("a");
      aEl.href = "visualize.html?look=" + encodeURIComponent(r.lookId);
      aEl.textContent = "Preview " + (LOOKS[r.lookId] || "this look") + " in Visualize";
      link.appendChild(aEl);
      body.appendChild(link);
    }
  }

  function renderThumbs() {
    var box = $("thumbnails");
    box.innerHTML = "";
    photos.forEach(function (p) {
      var div = document.createElement("div");
      div.className = "thumb";
      var img = document.createElement("img");
      img.src = p.url;
      img.alt = "Flooring preview";
      var rm = document.createElement("button");
      rm.type = "button";
      rm.className = "remove";
      rm.setAttribute("aria-label", "Remove photo");
      rm.textContent = "×";
      rm.addEventListener("click", function () {
        URL.revokeObjectURL(p.url);
        photos = photos.filter(function (x) { return x.id !== p.id; });
        renderThumbs();
        updatePhotoUi();
      });
      div.appendChild(img);
      div.appendChild(rm);
      box.appendChild(div);
    });
    updatePhotoUi();
  }

  function updatePhotoUi() {
    var n = photos.length;
    $("photo-count").textContent = n
      ? n + " of " + MAX_PHOTOS + " photo" + (n === 1 ? "" : "s") + " ready"
      : "Add at least one photo to continue.";
    $("to-checklist").disabled = n < 1;
  }

  function readFiles(fileList) {
    var incoming = Array.prototype.slice.call(fileList || []);
    incoming.forEach(function (file) {
      if (!file.type || file.type.indexOf("image/") !== 0) return;
      if (photos.length >= MAX_PHOTOS) return;
      var url = URL.createObjectURL(file);
      photos.push({ id: String(Date.now()) + Math.random(), file: file, url: url });
    });
    renderThumbs();
  }

  function showLibraryCheck(result) {
    var el = $("library-check");
    if (!el || !window.VonPhotoCheck) return;
    window.VonPhotoCheck.paintCheck(el, result);
  }

  $("start-btn").addEventListener("click", function () { show("photos"); });
  var secondary = $("start-btn-secondary");
  if (secondary) secondary.addEventListener("click", function () { show("photos"); });

  document.querySelectorAll("[data-goto]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      show(btn.getAttribute("data-goto"));
    });
  });

  $("photo-input").addEventListener("change", function (e) {
    var files = Array.prototype.slice.call(e.target.files || []);
    readFiles(files);
    e.target.value = "";
    if (files[0] && window.VonPhotoCheck) {
      window.VonPhotoCheck.analyzeFile(files[0]).then(showLibraryCheck);
    }
  });

  $("to-checklist").addEventListener("click", function () {
    if (photos.length >= 1) show("checklist");
  });

  $("checklist-form").addEventListener("submit", function (e) {
    e.preventDefault();
    var fd = new FormData(e.target);
    answers = {
      seams: fd.get("seams"),
      texture: fd.get("texture"),
      underlay: fd.get("underlay"),
      edges: fd.get("edges"),
      wear: fd.get("wear"),
      look: fd.get("look")
    };
    fillReport(answers);
    show("report");
  });

  $("start-over").addEventListener("click", function () {
    photos.forEach(function (p) { URL.revokeObjectURL(p.url); });
    photos = [];
    answers = null;
    renderThumbs();
    $("checklist-form").reset();
    var check = $("library-check");
    if (check) {
      check.textContent = "";
      check.classList.add("hidden");
    }
    if (window.history && window.history.replaceState) {
      window.history.replaceState({}, "", window.location.pathname);
    }
    show("landing");
  });

  if (window.VonPhotoCheck && $("open-camera")) {
    cameraCtl = window.VonPhotoCheck.attachCamera({
      openBtn: $("open-camera"),
      panel: $("camera-panel"),
      video: $("camera-video"),
      shutter: $("camera-shutter"),
      cancel: $("camera-cancel"),
      review: $("shot-review"),
      preview: $("shot-preview"),
      checkEl: $("shot-check"),
      accept: $("shot-accept"),
      retake: $("shot-retake"),
      onStatus: function (msg) {
        var el = $("camera-status");
        if (el) el.textContent = msg || "";
      },
      onAccept: function (file, result) {
        readFiles([file]);
        showLibraryCheck(result);
      }
    });
  }

  updatePhotoUi();
  show("landing");
})();
