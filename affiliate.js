/* Builds Amazon links from data attributes.
 * <a data-amazon-search="keywords">  -> amazon.com search
 * <a data-amazon-asin="B0XXXXXXX">   -> amazon.com product page
 * The tracking tag comes from affiliate-config.js (window.VINYL_AMAZON_TAG).
 */
(function () {
  function init() {
    var tag = (window.VINYL_AMAZON_TAG || "").trim();
    var tagParam = encodeURIComponent(tag);

    function finish(a, href) {
      a.href = href;
      a.rel = "nofollow sponsored noopener";
      a.target = "_blank";
    }

    document.querySelectorAll("a[data-amazon-search]").forEach(function (a) {
      var keyword = a.getAttribute("data-amazon-search") || "";
      finish(a, "https://www.amazon.com/s?k=" + encodeURIComponent(keyword) +
        (tag ? "&tag=" + tagParam : ""));
    });

    document.querySelectorAll("a[data-amazon-asin]").forEach(function (a) {
      var asin = (a.getAttribute("data-amazon-asin") || "").trim();
      if (!asin) return;
      finish(a, "https://www.amazon.com/dp/" + encodeURIComponent(asin) +
        (tag ? "?tag=" + tagParam : ""));
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
