/* Click-to-load YouTube facade. Without JS the thumbnail stays a plain link to YouTube. */
(function () {
  "use strict";
  function upgrade(frame) {
    var id = frame.getAttribute("data-yt-id");
    var title = frame.getAttribute("data-yt-title") || "YouTube video";
    var link = frame.querySelector("a.video-facade");
    if (!id || !/^[A-Za-z0-9_-]{11}$/.test(id) || !link) return;
    var btn = document.createElement("button");
    btn.type = "button";
    btn.className = "video-facade";
    btn.setAttribute("aria-label", "Play video: " + title);
    while (link.firstChild) btn.appendChild(link.firstChild);
    link.parentNode.replaceChild(btn, link);
    btn.addEventListener("click", function () {
      var iframe = document.createElement("iframe");
      iframe.src = "https://www.youtube-nocookie.com/embed/" + id + "?autoplay=1&rel=0";
      iframe.title = title;
      iframe.allow = "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share";
      iframe.setAttribute("allowfullscreen", "");
      iframe.referrerPolicy = "strict-origin-when-cross-origin";
      frame.replaceChild(iframe, btn);
      iframe.focus();
    });
  }
  function init() {
    var frames = document.querySelectorAll(".video-frame[data-yt-id]");
    for (var i = 0; i < frames.length; i++) upgrade(frames[i]);
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
