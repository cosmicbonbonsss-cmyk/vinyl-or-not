(function () {
  "use strict";

  var extraRoot = document.getElementById("extra-areas");
  var addBtn = document.getElementById("add-area");
  var out = document.getElementById("measure-out");
  var wasteEl = document.getElementById("waste-pct");
  var boxEl = document.getElementById("box-coverage");
  var lenEl = document.getElementById("plank-len");
  var widEl = document.getElementById("plank-wid");
  var main = document.querySelector("[data-area='main']");
  var extraCount = 0;

  function num(el) {
    var n = parseFloat(el && el.value);
    return isFinite(n) ? n : 0;
  }

  function feetFrom(root, prefix) {
    var ft = num(root.querySelector("." + prefix + "-ft"));
    var inches = num(root.querySelector("." + prefix + "-in"));
    if (ft < 0) ft = 0;
    if (inches < 0) inches = 0;
    return ft + inches / 12;
  }

  function areaOf(root) {
    var length = feetFrom(root, "len");
    var width = feetFrom(root, "wid");
    if (length <= 0 || width <= 0) return 0;
    return length * width;
  }

  function areaName(root, fallback) {
    var input = root.querySelector(".area-name");
    var name = input ? input.value.trim() : "";
    return name || fallback;
  }

  function addExtra(name) {
    extraCount += 1;
    var wrap = document.createElement("div");
    wrap.className = "area-block";
    wrap.innerHTML =
      '<div class="area-head">' +
        '<label class="area-name-label">Area name' +
          '<input type="text" class="area-name" value="' + (name || ("Extra area " + extraCount)) + '" />' +
        "</label>" +
        '<button type="button" class="btn ghost remove-area">Remove</button>' +
      "</div>" +
      '<div class="dim-grid">' +
        dimFields("len", "Length") +
        dimFields("wid", "Width") +
      "</div>";
    wrap.querySelector(".remove-area").addEventListener("click", function () {
      wrap.remove();
      render();
    });
    wrap.querySelectorAll("input").forEach(function (input) {
      input.addEventListener("input", render);
    });
    extraRoot.appendChild(wrap);
    render();
  }

  function dimFields(prefix, label) {
    return (
      '<fieldset class="dim-set">' +
        "<legend>" + label + "</legend>" +
        '<div class="dim-inputs">' +
          '<label>Feet<input type="number" class="' + prefix + '-ft" min="0" max="200" step="1" inputmode="numeric" value="0" /></label>' +
          '<label>Inches<input type="number" class="' + prefix + '-in" min="0" max="11.99" step="0.25" inputmode="decimal" value="0" /></label>' +
        "</div>" +
      "</fieldset>"
    );
  }

  function render() {
    var parts = [];
    var net = 0;
    var mainSq = areaOf(main);
    if (mainSq > 0) {
      parts.push({ name: "Main area", sq: mainSq });
      net += mainSq;
    }
    extraRoot.querySelectorAll(".area-block").forEach(function (block, i) {
      var sq = areaOf(block);
      if (sq <= 0) return;
      parts.push({ name: areaName(block, "Extra area " + (i + 1)), sq: sq });
      net += sq;
    });

    var waste = num(wasteEl);
    if (waste < 0) waste = 0;
    if (waste > 40) waste = 40;
    var coverage = num(boxEl);
    var plankLen = num(lenEl);
    var plankWid = num(widEl);
    var plankSq = plankLen > 0 && plankWid > 0 ? (plankLen * plankWid) / 144 : 0;
    var order = net * (1 + waste / 100);
    var boxes = coverage > 0 ? Math.ceil(order / coverage - 1e-9) : 0;
    var planks = plankSq > 0 ? Math.ceil(order / plankSq - 1e-9) : 0;

    if (net <= 0) {
      out.innerHTML = "<p>Enter a length and width to see square footage, waste, boxes, and planks.</p>";
      return;
    }

    var rows = parts.map(function (p) {
      return "<dt>" + escapeHtml(p.name) + "</dt><dd>" + p.sq.toFixed(1) + " sq ft</dd>";
    }).join("");

    out.innerHTML =
      "<dl>" +
      rows +
      "<dt>Net area</dt><dd>" + net.toFixed(1) + " sq ft</dd>" +
      "<dt>Waste (" + waste + "%)</dt><dd>" + (order - net).toFixed(1) + " sq ft</dd>" +
      "<dt>Order quantity</dt><dd>" + order.toFixed(1) + " sq ft</dd>" +
      "<dt>Boxes to buy</dt><dd>" + boxes + "</dd>" +
      "<dt>Planks (estimate)</dt><dd>" + planks + "</dd>" +
      "</dl>" +
      '<p class="hint">Boxes use ' + coverage.toFixed(1) + " sq ft each. Planks assume " +
      plankWid + " in × " + plankLen + " in. Round up at the store, and keep a spare box if the color might be discontinued.</p>";
  }

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  main.querySelectorAll("input").forEach(function (input) {
    input.addEventListener("input", render);
  });
  [wasteEl, boxEl, lenEl, widEl].forEach(function (el) {
    if (el) el.addEventListener("input", render);
  });
  if (addBtn) addBtn.addEventListener("click", function () { addExtra(""); });

  render();
})();
