(function () {
  "use strict";

  var ACCOUNT_KEY = "von_trade_account";
  var DRAFT_KEY = "von_quote_draft";
  var LAST_SUMMARY_KEY = "von_quote_last_summary";
  var PRO_KEY = "vinylProPaid";
  var PRO_KEY_ALT = "von_pro_unlocked";
  var REPORT_KEY = "von_report_unlocked";
  var BLUEPRINT_KEY = "von_pro_blueprints";
  var RECEIPT_KEY = "von_pro_receipts";
  var PROFILE_KEY = "von_contractor_profile";
  var MAX_FILE_CHARS = 500000;

  var accountForm = document.getElementById("trade-account-form");
  var accountStatus = document.getElementById("account-status");
  var signoutBtn = document.getElementById("account-signout");
  var quoteForm = document.getElementById("quote-form");
  var inquiryType = document.getElementById("quote-inquiry-type");
  var unitsWrap = document.getElementById("units-wrap");
  var quoteResult = document.getElementById("quote-result");
  var quoteSummary = document.getElementById("quote-summary");
  var quoteMailto = document.getElementById("quote-mailto");
  var quoteCopy = document.getElementById("quote-copy");
  var quoteCopyStatus = document.getElementById("quote-copy-status");
  var loadDraftBtn = document.getElementById("quote-load-draft");

  function readJson(key) {
    try {
      var raw = localStorage.getItem(key);
      return raw ? JSON.parse(raw) : null;
    } catch (e) {
      return null;
    }
  }

  function writeJson(key, value) {
    try {
      localStorage.setItem(key, JSON.stringify(value));
    } catch (e) {
      throw e;
    }
  }

  function escapeHtml(s) {
    return String(s || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function roleLabel(role) {
    if (role === "pm") return "Property manager";
    if (role === "designer") return "Designer";
    return "Installer / flooring contractor";
  }

  function showAccountStatus(account) {
    if (!accountStatus) return;
    if (!account || !account.company) {
      accountStatus.classList.add("hidden");
      accountStatus.textContent = "";
      return;
    }
    accountStatus.classList.remove("hidden");
    accountStatus.innerHTML =
      "You're signed in as <strong>" +
      escapeHtml(account.company) +
      "</strong>" +
      (account.email ? " · " + escapeHtml(account.email) : "") +
      " · " +
      escapeHtml(roleLabel(account.role)) +
      ' <span class="hint">(this browser only)</span>';
  }

  function fillAccountForm(account) {
    if (!account || !accountForm) return;
    accountForm.role.value = account.role || "installer";
    accountForm.company.value = account.company || "";
    accountForm.email.value = account.email || "";
    accountForm.phone.value = account.phone || "";
    accountForm.zip.value = account.zip || "";
    accountForm.retailerNotes.value = account.retailerNotes || "";
  }

  function prefillQuoteFromAccount(account) {
    if (!account || !quoteForm) return;
    if (account.company && !quoteForm.company.value) quoteForm.company.value = account.company;
    if (account.email && !quoteForm.email.value) quoteForm.email.value = account.email;
    if (account.phone && !quoteForm.phone.value) quoteForm.phone.value = account.phone;
    if (account.zip && !quoteForm.site.value) quoteForm.site.value = account.zip;
    if (account.role === "pm") inquiryType.value = "bulk";
    else if (account.role === "designer") inquiryType.value = "design";
    else inquiryType.value = "installer";
    toggleUnits();
  }

  function toggleUnits() {
    if (!unitsWrap || !inquiryType) return;
    unitsWrap.classList.toggle("hidden", inquiryType.value !== "bulk");
  }

  function collectQuote() {
    return {
      inquiryType: quoteForm.inquiryType.value,
      company: quoteForm.company.value.trim(),
      contact: quoteForm.contact.value.trim(),
      email: quoteForm.email.value.trim(),
      phone: quoteForm.phone.value.trim(),
      site: quoteForm.site.value.trim(),
      units: quoteForm.units.value.trim(),
      property: quoteForm.property.value.trim(),
      sqft: quoteForm.sqft.value.trim(),
      flooring: quoteForm.flooring.value,
      timeline: quoteForm.timeline.value.trim(),
      photos: quoteForm.photos.value.trim(),
      notes: quoteForm.notes.value.trim(),
      savedAt: new Date().toISOString()
    };
  }

  function fillQuoteForm(data) {
    if (!data || !quoteForm) return;
    quoteForm.inquiryType.value = data.inquiryType || "installer";
    quoteForm.company.value = data.company || "";
    quoteForm.contact.value = data.contact || "";
    quoteForm.email.value = data.email || "";
    quoteForm.phone.value = data.phone || "";
    quoteForm.site.value = data.site || "";
    quoteForm.units.value = data.units || "";
    quoteForm.property.value = data.property || "";
    quoteForm.sqft.value = data.sqft || "";
    quoteForm.flooring.value = data.flooring || "LVP";
    quoteForm.timeline.value = data.timeline || "";
    quoteForm.photos.value = data.photos || "";
    quoteForm.notes.value = data.notes || "";
    toggleUnits();
  }

  function formatSummary(data) {
    var typeLabel =
      data.inquiryType === "bulk"
        ? "Property manager / bulk units"
        : data.inquiryType === "design"
          ? "Designer / presentation project"
          : "Installer / single job";
    var lines = [
      "Vinyl or Not — pro project inquiry",
      "================================",
      "Type: " + typeLabel,
      "Company: " + data.company,
      "Contact: " + data.contact,
      "Email: " + data.email,
      "Phone: " + (data.phone || "(none)"),
      "Job site city/ZIP: " + (data.site || "(none)"),
      "Property / project: " + (data.property || "(none)")
    ];
    if (data.inquiryType === "bulk") {
      lines.push("Unit / door count: " + (data.units || "(none)"));
    }
    lines.push(
      "Approx sq ft: " + (data.sqft || "(none)"),
      "Flooring interest: " + data.flooring,
      "Timeline: " + (data.timeline || "(none)"),
      "Optional photo count: " + (data.photos || "(none)"),
      "Notes:",
      data.notes || "(none)",
      "",
      "(Generated in-browser only — not sent automatically.)"
    );
    return lines.join("\n");
  }

  function mailtoHref(data, summary) {
    var subject = encodeURIComponent(
      "Vinyl or Not inquiry — " + data.company + (data.property ? " / " + data.property : "")
    );
    var body = encodeURIComponent(summary);
    var to = encodeURIComponent(data.email || "");
    return "mailto:" + to + "?subject=" + subject + "&body=" + body;
  }

  if (accountForm) {
    accountForm.addEventListener("submit", function (e) {
      e.preventDefault();
      var account = {
        role: accountForm.role.value,
        company: accountForm.company.value.trim(),
        email: accountForm.email.value.trim(),
        phone: accountForm.phone.value.trim(),
        zip: accountForm.zip.value.trim(),
        retailerNotes: accountForm.retailerNotes.value.trim(),
        savedAt: new Date().toISOString()
      };
      try {
        writeJson(ACCOUNT_KEY, account);
      } catch (err) {}
      showAccountStatus(account);
      prefillQuoteFromAccount(account);
    });
  }

  if (signoutBtn) {
    signoutBtn.addEventListener("click", function () {
      try {
        localStorage.removeItem(ACCOUNT_KEY);
      } catch (e) {}
      if (accountForm) accountForm.reset();
      showAccountStatus(null);
    });
  }

  if (inquiryType) inquiryType.addEventListener("change", toggleUnits);

  if (quoteForm) {
    quoteForm.addEventListener("submit", function (e) {
      e.preventDefault();
      var data = collectQuote();
      try {
        writeJson(DRAFT_KEY, data);
      } catch (err) {}
      var summary = formatSummary(data);
      try {
        writeJson(LAST_SUMMARY_KEY, { summary: summary, data: data });
      } catch (err2) {}
      quoteSummary.textContent = summary;
      quoteMailto.href = mailtoHref(data, summary);
      quoteResult.classList.remove("hidden");
      quoteCopyStatus.textContent =
        "Saved draft in this browser. Open email or copy — nothing was sent.";
      quoteResult.scrollIntoView({ behavior: "smooth", block: "nearest" });
    });
  }

  if (quoteCopy) {
    quoteCopy.addEventListener("click", function () {
      var text = quoteSummary.textContent || "";
      if (!text) return;
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(
          function () {
            quoteCopyStatus.textContent = "Copied to clipboard.";
          },
          function () {
            quoteCopyStatus.textContent = "Copy failed — select the summary and copy manually.";
          }
        );
      } else {
        quoteCopyStatus.textContent = "Clipboard not available — select the summary and copy manually.";
      }
    });
  }

  if (loadDraftBtn) {
    loadDraftBtn.addEventListener("click", function () {
      var draft = readJson(DRAFT_KEY);
      if (!draft) {
        quoteCopyStatus.textContent = "No saved draft in this browser yet.";
        if (quoteResult) quoteResult.classList.remove("hidden");
        return;
      }
      fillQuoteForm(draft);
      quoteCopyStatus.textContent = "Loaded last quote draft.";
    });
  }

  // ---- Paid unlock ----
  function hasProUnlock() {
    try {
      if (sessionStorage.getItem(PRO_KEY) === "1") return true;
      if (sessionStorage.getItem(PRO_KEY_ALT) === "1") return true;
      if (sessionStorage.getItem(REPORT_KEY) === "1") return true;
    } catch (e) {}
    var params = new URLSearchParams(window.location.search);
    if (params.get("pro") === "1" || params.get("report") === "1") {
      markProUnlocked();
      return true;
    }
    return false;
  }

  function markProUnlocked() {
    try {
      sessionStorage.setItem(PRO_KEY, "1");
      sessionStorage.setItem(PRO_KEY_ALT, "1");
    } catch (e) {}
  }

  function applyProUi(unlocked) {
    var lockBanner = document.getElementById("pro-unlock-banner");
    var okBanner = document.getElementById("pro-unlocked-banner");
    if (lockBanner) lockBanner.classList.toggle("hidden", unlocked);
    if (okBanner) okBanner.classList.toggle("hidden", !unlocked);
    ["tool-blueprints", "tool-receipts", "tool-profile"].forEach(function (id) {
      var card = document.getElementById(id);
      if (!card) return;
      card.setAttribute("data-locked", unlocked ? "0" : "1");
      var overlay = card.querySelector(".lock-overlay");
      if (overlay) overlay.hidden = unlocked;
      card.querySelectorAll(".locked-only-msg").forEach(function (el) {
        el.classList.toggle("hidden", unlocked);
      });
      card.querySelectorAll(".unlocked-only").forEach(function (el) {
        el.classList.toggle("hidden", !unlocked);
      });
    });
  }

  function stripeCfg() {
    return window.VINYL_OR_NOT_STRIPE || {};
  }

  function setupCheckout() {
    var cfg = stripeCfg();
    var priceLabel = document.getElementById("pro-price-label");
    var priceBand = document.getElementById("pro-price-band");
    if (priceLabel && cfg.priceLabel) priceLabel.textContent = cfg.priceLabel;
    if (priceBand && cfg.priceBand) priceBand.textContent = cfg.priceBand;
    var btn = document.getElementById("pro-checkout-btn");
    var hint = document.getElementById("pro-unlock-hint");
    if (!btn) return;
    if (cfg.checkoutUrl) {
      btn.href = cfg.checkoutUrl;
      btn.textContent = "Pay with Stripe (test) — " + (cfg.priceLabel || "$12");
      if (hint) hint.textContent = "After payment, return with ?pro=1 (or ?report=1) to unlock.";
    } else {
      btn.href = "pros.html?pro=1";
      btn.textContent = "Continue (demo unlock)";
      if (hint) hint.textContent = "No Stripe Payment Link configured — demo unlock only.";
    }
  }

  var demoUnlock = document.getElementById("pro-demo-unlock");
  if (demoUnlock) {
    demoUnlock.addEventListener("click", function () {
      markProUnlocked();
      applyProUi(true);
      if (window.history && window.history.replaceState) {
        try {
          var u = new URL(window.location.href);
          u.searchParams.set("pro", "1");
          window.history.replaceState({}, "", u.toString());
        } catch (e) {}
      }
    });
  }

  function loadFileList(key) {
    var list = readJson(key);
    return Array.isArray(list) ? list : [];
  }

  function renderFileList(ulId, key) {
    var ul = document.getElementById(ulId);
    if (!ul) return;
    var list = loadFileList(key);
    if (!list.length) {
      ul.innerHTML = '<li class="hint">No files yet.</li>';
      return;
    }
    ul.innerHTML = list
      .map(function (f, i) {
        var open =
          f.dataUrl && String(f.dataUrl).indexOf("data:") === 0
            ? '<a href="' + f.dataUrl + '" target="_blank" rel="noopener">Open</a>'
            : "";
        return (
          "<li><span>" +
          escapeHtml(f.name || "file") +
          ' <span class="hint">(' +
          escapeHtml(f.type || "file") +
          ")</span></span> " +
          open +
          ' <button type="button" class="btn ghost file-remove" data-key="' +
          key +
          '" data-index="' +
          i +
          '">Remove</button></li>'
        );
      })
      .join("");
  }

  function bindFileInput(inputId, key, listId) {
    var input = document.getElementById(inputId);
    if (!input) return;
    input.addEventListener("change", function () {
      if (!hasProUnlock()) return;
      var files = Array.prototype.slice.call(input.files || [], 0);
      if (!files.length) return;
      var chain = Promise.resolve();
      files.forEach(function (file) {
        chain = chain.then(function () {
          return new Promise(function (resolve, reject) {
            var reader = new FileReader();
            reader.onload = function () {
              var dataUrl = String(reader.result || "");
              if (dataUrl.length > MAX_FILE_CHARS) {
                reject(new Error("File too large for demo storage: " + file.name));
                return;
              }
              var list = loadFileList(key);
              list.unshift({
                name: file.name,
                type: file.type || "file",
                dataUrl: dataUrl,
                savedAt: new Date().toISOString()
              });
              try {
                writeJson(key, list);
              } catch (err) {
                reject(new Error("Storage full — remove older files."));
                return;
              }
              resolve();
            };
            reader.onerror = function () {
              reject(new Error("Read failed"));
            };
            reader.readAsDataURL(file);
          });
        });
      });
      chain
        .then(function () {
          renderFileList(listId, key);
          input.value = "";
        })
        .catch(function (err) {
          alert(err.message || String(err));
          input.value = "";
        });
    });
  }

  document.addEventListener("click", function (e) {
    var t = e.target;
    if (!t || !t.classList || !t.classList.contains("file-remove")) return;
    var key = t.getAttribute("data-key");
    var idx = parseInt(t.getAttribute("data-index"), 10);
    var list = loadFileList(key);
    if (!isNaN(idx)) {
      list.splice(idx, 1);
      try {
        writeJson(key, list);
      } catch (err) {}
      if (key === BLUEPRINT_KEY) renderFileList("blueprint-list", BLUEPRINT_KEY);
      if (key === RECEIPT_KEY) renderFileList("receipt-list", RECEIPT_KEY);
    }
  });

  bindFileInput("blueprint-input", BLUEPRINT_KEY, "blueprint-list");
  bindFileInput("receipt-input", RECEIPT_KEY, "receipt-list");

  var profileForm = document.getElementById("profile-form");
  var profileStatus = document.getElementById("profile-status");

  function fillProfile(p) {
    if (!profileForm || !p) return;
    profileForm.businessName.value = p.businessName || "";
    profileForm.license.value = p.license || "";
    profileForm.serviceArea.value = p.serviceArea || "";
    profileForm.years.value = p.years != null ? p.years : "";
    profileForm.bio.value = p.bio || "";
    profileForm.portfolio.value = p.portfolio || "";
  }

  if (profileForm) {
    profileForm.addEventListener("submit", function (e) {
      e.preventDefault();
      if (!hasProUnlock()) return;
      var profile = {
        businessName: profileForm.businessName.value.trim(),
        license: profileForm.license.value.trim(),
        serviceArea: profileForm.serviceArea.value.trim(),
        years: profileForm.years.value.trim(),
        bio: profileForm.bio.value.trim(),
        portfolio: profileForm.portfolio.value.trim(),
        savedAt: new Date().toISOString()
      };
      try {
        writeJson(PROFILE_KEY, profile);
      } catch (err) {
        if (profileStatus) profileStatus.textContent = "Could not save profile (storage).";
        return;
      }
      var acct = readJson(ACCOUNT_KEY);
      if (acct && profile.businessName) {
        acct.company = profile.businessName;
        try {
          writeJson(ACCOUNT_KEY, acct);
        } catch (e2) {}
        showAccountStatus(acct);
      }
      if (profileStatus) {
        profileStatus.textContent =
          "Profile saved on this device. Featured gallery cards can show your business name.";
      }
    });
  }

  // Init trade account + quote
  var existing = readJson(ACCOUNT_KEY);
  if (existing) {
    fillAccountForm(existing);
    showAccountStatus(existing);
    prefillQuoteFromAccount(existing);
  }
  toggleUnits();

  setupCheckout();
  fillProfile(readJson(PROFILE_KEY));
  renderFileList("blueprint-list", BLUEPRINT_KEY);
  renderFileList("receipt-list", RECEIPT_KEY);
  applyProUi(hasProUnlock());
})();
