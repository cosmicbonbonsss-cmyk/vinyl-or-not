/* Build retailer links from the public config without requiring an affiliate ID. */
(function () {
  "use strict";

  var defaults = {
    amazon: "https://www.amazon.com/s?k=luxury+vinyl+plank+flooring",
    homeDepot: "https://www.homedepot.com/b/Flooring-Vinyl-Flooring-Vinyl-Plank-Flooring/N-5yc1vZbzjz",
    lowes: "https://www.lowes.com/pl/vinyl-flooring/vinyl-plank/4294608591",
    floorAndDecor: "https://www.flooranddecor.com/luxury-vinyl-plank-and-tile"
  };

  function config() {
    return window.VINYL_OR_NOT_AFFILIATE || {};
  }

  function buildAffiliateHref(retailer) {
    var cfg = config();
    var url = (cfg.links && cfg.links[retailer]) || defaults[retailer];
    if (!url) return "#";

    var tag = (cfg.enabled !== false && retailer === "amazon" && cfg.amazonTag || "").trim();
    if (!tag) return url;

    try {
      var parsed = new URL(url, window.location.href);
      parsed.searchParams.set("tag", tag);
      return parsed.toString();
    } catch (error) {
      return url;
    }
  }

  function wireAffiliateLinks() {
    document.querySelectorAll("[data-affiliate-retailer]").forEach(function (link) {
      var retailer = link.getAttribute("data-affiliate-retailer");
      link.href = buildAffiliateHref(retailer);
      link.target = "_blank";
      link.rel = "noopener sponsored";
    });
  }

  window.VinylOrNotAffiliate = {
    buildHref: buildAffiliateHref,
    wire: wireAffiliateLinks
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", wireAffiliateLinks);
  } else {
    wireAffiliateLinks();
  }
}());
