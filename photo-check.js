/* On-device photo check for room shots. No network, no model. */
(function (global) {
  "use strict";

  var MAX_EDGE = 180;

  function luminance(data, i) {
    return 0.2126 * data[i] + 0.7152 * data[i + 1] + 0.0722 * data[i + 2];
  }

  function analyzeImageData(imageData) {
    var data = imageData.data;
    var w = imageData.width;
    var h = imageData.height;
    var n = w * h;
    var sum = 0;
    var highlights = 0;
    var i;
    var L;
    for (i = 0; i < data.length; i += 4) {
      L = luminance(data, i);
      sum += L;
      if (L >= 245) highlights += 1;
    }
    var mean = n ? sum / n : 0;
    var highlightRatio = n ? highlights / n : 0;

    var lapSum = 0;
    var lapSq = 0;
    var count = 0;
    var y;
    var x;
    for (y = 1; y < h - 1; y += 1) {
      for (x = 1; x < w - 1; x += 1) {
        var c = luminance(data, (y * w + x) * 4);
        var up = luminance(data, ((y - 1) * w + x) * 4);
        var dn = luminance(data, ((y + 1) * w + x) * 4);
        var lf = luminance(data, (y * w + (x - 1)) * 4);
        var rt = luminance(data, (y * w + (x + 1)) * 4);
        var lap = up + dn + lf + rt - 4 * c;
        lapSum += lap;
        lapSq += lap * lap;
        count += 1;
      }
    }
    var variance = 0;
    if (count) {
      var lapMean = lapSum / count;
      variance = lapSq / count - lapMean * lapMean;
    }

    var tips = [];
    if (mean < 55) {
      tips.push("This looks too dark. Add a light or face a window, then try again.");
    } else if (mean > 215 || highlightRatio > 0.25) {
      tips.push("This looks blown out. Move out of glare or shade the windows, then try again.");
    }
    /* Tuned on downscaled (~180px) room photos: a strong blur lands under ~250. */
    if (variance < 250) {
      tips.push("This looks blurry. Hold still, tap the floor to focus, and keep the guide filled.");
    }

    var ok = tips.length === 0;
    var summary = ok
      ? "Photo check: lighting and sharpness look usable. You can still retake if the floor is cropped."
      : "Photo check: " + tips.join(" ");

    return {
      mean: mean,
      highlightRatio: highlightRatio,
      variance: variance,
      tips: tips,
      ok: ok,
      summary: summary
    };
  }

  function analyze(source, sw, sh) {
    var width = sw || source.videoWidth || source.naturalWidth || source.width;
    var height = sh || source.videoHeight || source.naturalHeight || source.height;
    if (!width || !height) {
      return {
        mean: 0,
        highlightRatio: 0,
        variance: 0,
        tips: [],
        ok: true,
        summary: "Photo check could not read that image. You can still continue."
      };
    }
    var scale = Math.min(1, MAX_EDGE / Math.max(width, height));
    var canvas = document.createElement("canvas");
    canvas.width = Math.max(8, Math.round(width * scale));
    canvas.height = Math.max(8, Math.round(height * scale));
    var ctx = canvas.getContext("2d", { willReadFrequently: true });
    ctx.drawImage(source, 0, 0, canvas.width, canvas.height);
    return analyzeImageData(ctx.getImageData(0, 0, canvas.width, canvas.height));
  }

  function analyzeFile(file) {
    return new Promise(function (resolve) {
      if (!file) {
        resolve(analyze(document.createElement("canvas")));
        return;
      }
      var url = URL.createObjectURL(file);
      var img = new Image();
      img.onload = function () {
        var result = analyze(img);
        URL.revokeObjectURL(url);
        resolve(result);
      };
      img.onerror = function () {
        URL.revokeObjectURL(url);
        resolve({
          mean: 0,
          highlightRatio: 0,
          variance: 0,
          tips: [],
          ok: true,
          summary: "Photo check could not read that image. You can still continue."
        });
      };
      img.src = url;
    });
  }

  function paintCheck(el, result) {
    if (!el || !result) return;
    el.textContent = result.summary;
    el.classList.remove("hidden", "is-ok", "is-warn");
    el.classList.add(result.ok ? "is-ok" : "is-warn");
  }

  /**
   * Live camera + review. onAccept(file, result) fires when the shot is kept.
   * Returns { stop } so the page can shut the camera when leaving the step.
   */
  function attachCamera(opts) {
    var stream = null;
    var pendingCanvas = null;

    function show(el, on) {
      if (!el) return;
      el.classList.toggle("hidden", !on);
    }

    function stop() {
      if (stream) {
        stream.getTracks().forEach(function (track) { track.stop(); });
        stream = null;
      }
      if (opts.video) opts.video.srcObject = null;
    }

    function open() {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        if (opts.onStatus) {
          opts.onStatus("This browser can't open the camera. Upload a photo from your library instead.");
        }
        return;
      }
      navigator.mediaDevices.getUserMedia({
        video: { facingMode: { ideal: "environment" } },
        audio: false
      }).then(function (next) {
        stop();
        stream = next;
        opts.video.srcObject = next;
        var play = opts.video.play();
        if (play && play.catch) play.catch(function () {});
        show(opts.panel, true);
        show(opts.review, false);
        if (opts.onStatus) opts.onStatus("Frame the floor inside the guide, hold steady, then take the photo.");
      }).catch(function () {
        if (opts.onStatus) {
          opts.onStatus("Camera isn't available here. Upload a photo from your library instead.");
        }
      });
    }

    if (opts.openBtn) opts.openBtn.addEventListener("click", open);

    if (opts.cancel) {
      opts.cancel.addEventListener("click", function () {
        stop();
        show(opts.panel, false);
        if (opts.onStatus) opts.onStatus("");
      });
    }

    if (opts.shutter) {
      opts.shutter.addEventListener("click", function () {
        var video = opts.video;
        if (!video || !video.videoWidth) {
          if (opts.onStatus) opts.onStatus("Camera is still starting. Wait a moment, then take the photo.");
          return;
        }
        var snap = document.createElement("canvas");
        snap.width = video.videoWidth;
        snap.height = video.videoHeight;
        snap.getContext("2d").drawImage(video, 0, 0);
        pendingCanvas = snap;
        var result = analyze(snap);
        if (opts.preview) opts.preview.src = snap.toDataURL("image/jpeg", 0.92);
        paintCheck(opts.checkEl, result);
        opts._lastResult = result;
        stop();
        show(opts.panel, false);
        show(opts.review, true);
        if (opts.onStatus) opts.onStatus("Check the photo, then use it or retake.");
      });
    }

    if (opts.retake) {
      opts.retake.addEventListener("click", function () {
        show(opts.review, false);
        open();
      });
    }

    if (opts.accept) {
      opts.accept.addEventListener("click", function () {
        if (!pendingCanvas) return;
        var result = opts._lastResult;
        pendingCanvas.toBlob(function (blob) {
          if (!blob) return;
          var file = new File([blob], "room-photo.jpg", { type: "image/jpeg" });
          show(opts.review, false);
          stop();
          if (opts.onAccept) opts.onAccept(file, result);
        }, "image/jpeg", 0.92);
      });
    }

    return { stop: stop, open: open };
  }

  global.VonPhotoCheck = {
    analyze: analyze,
    analyzeFile: analyzeFile,
    paintCheck: paintCheck,
    attachCamera: attachCamera
  };
})(window);
