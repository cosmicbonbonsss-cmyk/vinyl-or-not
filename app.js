(function () {
  "use strict";

  var MAX_PHOTOS = 3;
  var photos = []; // { id, file, url }
  var answers = null;

  var sections = ["landing", "photos", "checklist", "teaser", "report"];

  function $(id) { return document.getElementById(id); }

  function show(id) {
    sections.forEach(function (s) {
      var el = $(s);
      if (el) el.classList.toggle("hidden", s !== id);
    });
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function hasReportUnlock() {
    try {
      if (sessionStorage.getItem("von_report_unlocked") === "1") return true;
    } catch (e) { /* ignore */ }
    var params = new URLSearchParams(window.location.search);
    return params.get("report") === "1";
  }

  function markUnlocked() {
    try { sessionStorage.setItem("von_report_unlocked", "1"); } catch (e) { /* ignore */ }
  }

  function guessFromAnswers(a) {
    // Simple rule table — guided checklist, not vision
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

    var labels = {
      lvp: "Likely click-lock LVP (luxury vinyl plank)",
      laminate: "Likely laminate with a photographic wear layer",
      tile: "Likely ceramic or porcelain tile",
      hardwood: "Likely solid or engineered hardwood"
    };

    var wearNote = "";
    if (a.wear === "peaking") wearNote = " — peaking/lifted edges noted";
    else if (a.wear === "heavy") wearNote = " — heavy wear or damage noted";
    else wearNote = " — surface wear looks light from your answers";

    return labels[best] + wearNote + ".";
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

  function wireCheckout() {
    var cfg = window.VINYL_OR_NOT_STRIPE || {};
    var btn = $("checkout-btn");
    var hint = $("checkout-hint");
    var url = (cfg.checkoutUrl || "").trim();
    var price = cfg.priceLabel || "$12";

    if (url) {
      btn.href = url;
      btn.target = "_blank";
      btn.textContent = "Pay " + price + " with Stripe (test)";
      hint.textContent = "Opens Stripe Test Payment Link. Success should redirect back with ?report=1.";
    } else {
      btn.href = "?report=1";
      btn.removeAttribute("target");
      btn.textContent = "Continue to demo unlock (" + price + " placeholder)";
      hint.textContent =
        "No Stripe Payment Link set yet — checkoutUrl is empty in stripe-config.js. " +
        "Demo unlock uses ?report=1. See README.";
    }
  }

  function openMapsSearch(query) {
    var q = encodeURIComponent("flooring stores near " + query);
    window.open("https://www.google.com/maps/search/?api=1&query=" + q, "_blank", "noopener");
  }

  function wireWhereToBuy(root) {
    if (!root || root.dataset.wired === "1") return;
    root.dataset.wired = "1";

    var input = root.querySelector(".local-zip");
    var searchBtn = root.querySelector(".local-search-btn");
    var geoBtn = root.querySelector(".geo-btn");
    var status = root.querySelector(".geo-status");

    function runSearch() {
      var v = (input && input.value || "").trim();
      if (!v) {
        if (status) status.textContent = "Enter a ZIP or city first.";
        return;
      }
      if (status) status.textContent = "";
      openMapsSearch(v);
    }

    if (searchBtn) searchBtn.addEventListener("click", runSearch);
    if (input) {
      input.addEventListener("keydown", function (e) {
        if (e.key === "Enter") {
          e.preventDefault();
          runSearch();
        }
      });
    }

    if (geoBtn) {
      geoBtn.addEventListener("click", function () {
        if (!navigator.geolocation) {
          if (status) status.textContent = "Geolocation not supported — enter a ZIP or city.";
          return;
        }
        if (status) status.textContent = "Getting location…";
        navigator.geolocation.getCurrentPosition(
          function (pos) {
            var lat = pos.coords.latitude.toFixed(5);
            var lng = pos.coords.longitude.toFixed(5);
            if (status) status.textContent = "Opening maps near you…";
            openMapsSearch(lat + "," + lng);
          },
          function () {
            if (status) status.textContent = "Location denied or unavailable — enter a ZIP or city.";
          },
          { enableHighAccuracy: false, timeout: 10000 }
        );
      });
    }
  }

  function wireAllWhereToBuy() {
    document.querySelectorAll(".where-to-buy").forEach(wireWhereToBuy);
  }

  // Events

  $("start-btn").addEventListener("click", function () { show("photos"); });

  document.querySelectorAll("[data-goto]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      show(btn.getAttribute("data-goto"));
    });
  });

  $("photo-input").addEventListener("change", function (e) {
    readFiles(e.target.files);
    e.target.value = "";
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
      wear: fd.get("wear")
    };
    $("teaser-guess").textContent = guessFromAnswers(answers);
    wireCheckout();
    wireAllWhereToBuy();
    if (hasReportUnlock()) {
      markUnlocked();
      show("report");
    } else {
      show("teaser");
    }
  });

  $("start-over").addEventListener("click", function () {
    photos.forEach(function (p) { URL.revokeObjectURL(p.url); });
    photos = [];
    answers = null;
    renderThumbs();
    $("checklist-form").reset();
    try { sessionStorage.removeItem("von_report_unlocked"); } catch (e) { /* ignore */ }
    // strip ?report=1 without reload if possible
    if (window.history && window.history.replaceState) {
      window.history.replaceState({}, "", window.location.pathname);
    }
    show("landing");
  });

  // Init
  wireAllWhereToBuy();
  wireCheckout();
  updatePhotoUi();

  if (hasReportUnlock()) {
    markUnlocked();
    // If unlocked via redirect, jump to report (sample text already in HTML)
    show("report");
  } else {
    show("landing");
  }
})();
