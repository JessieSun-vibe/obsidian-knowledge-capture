(function () {
  "use strict";

  const core = globalThis.DouyinCaptureCore;
  if (!core) return;

  const MEDIA_META = "obsidian-knowledge-media-url";
  const SOURCE_META = "obsidian-knowledge-canonical-url";
  const STATUS_META = "obsidian-knowledge-media-status";
  let lastLocation = "";
  let generation = 0;

  function setMeta(name, content) {
    let element = document.head && document.head.querySelector(`meta[name="${name}"]`);
    if (!document.head) return;
    if (!element) {
      element = document.createElement("meta");
      element.name = name;
      document.head.appendChild(element);
    }
    element.content = content || "";
  }

  function visibleVideoUrl(doc, videoId) {
    const videos = Array.from(doc.querySelectorAll("video"));
    for (const video of videos) {
      const candidates = [
        video.currentSrc,
        video.getAttribute("src"),
        ...Array.from(video.querySelectorAll("source")).map((source) => source.src || source.getAttribute("src")),
      ];
      for (const candidate of candidates) {
        const usable = core.usableMediaUrl(candidate, videoId);
        if (usable) return usable;
      }
    }
    return "";
  }

  function waitForMedia(doc, videoId, timeoutMs) {
    return new Promise((resolve) => {
      const started = Date.now();
      const check = () => {
        const mediaUrl = visibleVideoUrl(doc, videoId);
        if (mediaUrl) return resolve(mediaUrl);
        if (Date.now() - started >= timeoutMs) return resolve("");
        setTimeout(check, 250);
      };
      check();
    });
  }

  async function captureFromDetailFrame(videoId, run) {
    const frame = document.createElement("iframe");
    frame.setAttribute("aria-hidden", "true");
    frame.tabIndex = -1;
    frame.src = core.canonicalUrl(videoId);
    Object.assign(frame.style, {
      position: "fixed",
      width: "2px",
      height: "2px",
      left: "-10000px",
      top: "0",
      opacity: "0",
      pointerEvents: "none",
      border: "0",
    });
    document.documentElement.appendChild(frame);

    try {
      await new Promise((resolve) => {
        const timer = setTimeout(resolve, 15000);
        frame.addEventListener("load", () => {
          clearTimeout(timer);
          resolve();
        }, { once: true });
      });
      if (run !== generation) return "";
      const frameDocument = frame.contentDocument;
      return frameDocument ? await waitForMedia(frameDocument, videoId, 20000) : "";
    } catch (_) {
      return "";
    } finally {
      frame.remove();
    }
  }

  async function refresh() {
    const locationKey = location.href;
    if (locationKey === lastLocation) return;
    lastLocation = locationKey;
    const run = ++generation;
    const videoId = core.videoIdFromUrl(locationKey);
    if (!videoId) return;

    setMeta(SOURCE_META, core.canonicalUrl(videoId));
    setMeta(MEDIA_META, "");
    setMeta(STATUS_META, "loading");

    let mediaUrl = await waitForMedia(document, videoId, 5000);
    if (!mediaUrl && window.top === window && location.search.includes("modal_id=")) {
      mediaUrl = await captureFromDetailFrame(videoId, run);
    }
    if (run !== generation) return;
    setMeta(MEDIA_META, mediaUrl);
    setMeta(STATUS_META, mediaUrl ? "ready" : "unavailable");
  }

  refresh();
  setInterval(refresh, 1000);
})();
