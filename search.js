/* Vinyl or Not — on-site search.
   Loads search-index.json (built by scripts/build_search_index.py) the first
   time the box is used and shows matching pages in a dropdown.
   Keyboard: "/" focuses the box, Up/Down move, Enter opens, Escape closes. */
(function () {
  "use strict";

  var script = document.currentScript;
  var root = new URL(".", script ? script.src : location.href);
  var box = document.querySelector("[data-site-search]");
  if (!box) return;

  var input = box.querySelector("input");
  var list = box.querySelector("[role='listbox']");
  var status = box.querySelector("[data-search-status]");
  var form = box.closest("form") || box;
  var index = null;
  var loading = null;
  var results = [];
  var active = -1;
  var MAX = 8;

  var STOP = { a: 1, an: 1, the: 1, for: 1, in: 1, of: 1, to: 1, is: 1, my: 1, and: 1, or: 1, with: 1, on: 1, do: 1, i: 1, it: 1, can: 1, how: 1, what: 1, does: 1, by: 1 };
  var ALIAS = { grey: "gray", bath: "bathroom", baths: "bathroom", dog: "dogs", pet: "pets", lvt: "lvp", sqft: "square", diy: "diy" };

  function norm(s) {
    return String(s || "").toLowerCase().replace(/&/g, " and ").replace(/[’']/g, "").replace(/[^a-z0-9]+/g, " ").trim();
  }

  function tokens(q) {
    var all = norm(q).split(" ").filter(Boolean).map(function (w) { return ALIAS[w] || w; });
    var kept = all.filter(function (w) { return !STOP[w]; });
    return kept.length ? kept : all;
  }

  function load() {
    if (index) return Promise.resolve(index);
    if (!loading) {
      loading = fetch(new URL("search-index.json?v=20261007a", root).href)
        .then(function (r) {
          if (!r.ok) throw new Error("HTTP " + r.status);
          return r.json();
        })
        .then(function (data) {
          index = data.map(function (e) {
            return {
              e: e,
              title: norm(e.t).split(" "),
              kw: norm(e.k).split(" "),
              url: norm(e.u).split(" "),
              desc: norm(e.d).split(" "),
              titleStr: " " + norm(e.t) + " "
            };
          });
          return index;
        })
        .catch(function () {
          loading = null;
          return null;
        });
    }
    return loading;
  }

  function hit(words, t) {
    var best = 0;
    for (var i = 0; i < words.length; i++) {
      var w = words[i];
      if (w === t) return 2;
      if (t.length > 1 && w.indexOf(t) === 0) best = 1;
    }
    return best;
  }

  function score(item, toks, phrase) {
    var total = 0;
    for (var i = 0; i < toks.length; i++) {
      var t = toks[i];
      var s = 0;
      var h = hit(item.title, t);
      if (h) s = Math.max(s, h === 2 ? 12 : 9);
      h = hit(item.kw, t);
      if (h) s = Math.max(s, h === 2 ? 7 : 5);
      h = hit(item.url, t);
      if (h) s = Math.max(s, 4);
      h = hit(item.desc, t);
      if (h) s = Math.max(s, h === 2 ? 3 : 2);
      if (!s) return 0;
      total += s;
    }
    if (phrase.length > 2 && item.titleStr.indexOf(" " + phrase) !== -1) total += 10;
    if (item.e.s === "Floor look") total -= 1;
    return total;
  }

  function search(q) {
    var toks = tokens(q);
    if (!toks.length || !index) return [];
    var phrase = toks.join(" ");
    var out = [];
    for (var i = 0; i < index.length; i++) {
      var s = score(index[i], toks, phrase);
      if (s > 0) out.push({ s: s, e: index[i].e });
    }
    out.sort(function (a, b) { return b.s - a.s || a.e.t.length - b.e.t.length; });
    return out.slice(0, MAX).map(function (r) { return r.e; });
  }

  function href(e) {
    return new URL(e.u, root).href;
  }

  function trim(s, n) {
    s = String(s || "");
    return s.length > n ? s.slice(0, n - 1).replace(/\s+\S*$/, "").replace(/[.,;:\s]+$/, "") + "…" : s;
  }

  function setActive(i) {
    var opts = list.querySelectorAll("[role='option'][data-i]");
    if (!opts.length) { active = -1; input.removeAttribute("aria-activedescendant"); return; }
    if (i < 0) i = opts.length - 1;
    if (i >= opts.length) i = 0;
    active = i;
    for (var k = 0; k < opts.length; k++) {
      var on = k === i;
      opts[k].setAttribute("aria-selected", on ? "true" : "false");
      opts[k].classList.toggle("is-active", on);
    }
    input.setAttribute("aria-activedescendant", opts[i].id);
    opts[i].scrollIntoView({ block: "nearest" });
  }

  function open() {
    list.hidden = false;
    input.setAttribute("aria-expanded", "true");
    box.classList.add("is-open");
  }

  function close() {
    list.hidden = true;
    input.setAttribute("aria-expanded", "false");
    input.removeAttribute("aria-activedescendant");
    box.classList.remove("is-open");
    active = -1;
  }

  function render(q) {
    list.innerHTML = "";
    active = -1;
    input.removeAttribute("aria-activedescendant");
    if (!q.trim()) { close(); status.textContent = ""; return; }
    if (!index) {
      var li0 = document.createElement("li");
      li0.className = "site-search-empty";
      li0.setAttribute("role", "presentation");
      li0.textContent = "Search is unavailable right now. Try the Guide or Floor looks links.";
      list.appendChild(li0);
      open();
      return;
    }
    results = search(q);
    if (!results.length) {
      var li = document.createElement("li");
      li.className = "site-search-empty";
      li.setAttribute("role", "presentation");
      li.textContent = "No pages match \u201c" + q.trim() + "\u201d. Try \u201cwalnut kitchen\u201d or \u201cwear layer\u201d.";
      list.appendChild(li);
      status.textContent = "No results.";
      open();
      return;
    }
    results.forEach(function (e, i) {
      var li = document.createElement("li");
      li.id = "site-search-opt-" + i;
      li.setAttribute("role", "option");
      li.setAttribute("aria-selected", "false");
      li.setAttribute("data-i", String(i));
      var a = document.createElement("a");
      a.href = href(e);
      a.tabIndex = -1;
      var kind = document.createElement("span");
      kind.className = "site-search-kind";
      kind.textContent = e.s;
      var t = document.createElement("span");
      t.className = "site-search-title";
      t.textContent = e.t;
      var d = document.createElement("span");
      d.className = "site-search-desc";
      d.textContent = trim(e.d, 110);
      a.appendChild(kind);
      a.appendChild(t);
      a.appendChild(d);
      li.appendChild(a);
      li.addEventListener("mousemove", function () { if (active !== i) setActive(i); });
      list.appendChild(li);
    });
    status.textContent = results.length + (results.length === 1 ? " result." : " results.") + " Use up and down arrows to choose.";
    open();
  }

  var pending = 0;
  function update() {
    var q = input.value;
    var my = ++pending;
    load().then(function () { if (my === pending) render(q); });
  }

  input.addEventListener("input", update);
  input.addEventListener("focus", function () {
    load();
    if (input.value.trim()) update();
  });

  input.addEventListener("keydown", function (ev) {
    var k = ev.key;
    if (k === "ArrowDown" || k === "Down") {
      ev.preventDefault();
      if (list.hidden && input.value.trim()) { update(); return; }
      setActive(active + 1);
    } else if (k === "ArrowUp" || k === "Up") {
      ev.preventDefault();
      setActive(active - 1);
    } else if (k === "Enter") {
      ev.preventDefault();
      var pick = active >= 0 ? results[active] : results[0];
      if (!list.hidden && pick) location.href = href(pick);
    } else if (k === "Escape" || k === "Esc") {
      if (!list.hidden) { ev.preventDefault(); close(); }
      else if (input.value) { ev.preventDefault(); input.value = ""; status.textContent = ""; }
    } else if (k === "Tab") {
      close();
    }
  });

  if (form.tagName === "FORM") {
    form.addEventListener("submit", function (ev) { ev.preventDefault(); });
  }

  document.addEventListener("click", function (ev) {
    if (!box.contains(ev.target)) close();
  });

  document.addEventListener("keydown", function (ev) {
    if (ev.key !== "/" || ev.ctrlKey || ev.metaKey || ev.altKey) return;
    var el = document.activeElement;
    var tag = el && el.tagName;
    if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT" || (el && el.isContentEditable)) return;
    ev.preventDefault();
    input.focus();
  });
})();
