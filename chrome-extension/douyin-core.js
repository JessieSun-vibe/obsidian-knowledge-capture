(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  root.DouyinCaptureCore = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";

  function videoIdFromUrl(value) {
    try {
      const url = new URL(value);
      const modalId = url.searchParams.get("modal_id");
      if (/^\d+$/.test(modalId || "")) return modalId;
      const match = url.pathname.match(/\/video\/(\d+)/);
      return match ? match[1] : "";
    } catch (_) {
      return "";
    }
  }

  function canonicalUrl(videoId) {
    return /^\d+$/.test(videoId || "")
      ? `https://www.douyin.com/video/${videoId}`
      : "";
  }

  function usableMediaUrl(value, videoId) {
    if (!/^https?:\/\//.test(value || "")) return "";
    try {
      const url = new URL(value);
      if (!/video|mime_type=video|__vid=/.test(url.href)) return "";
      if (videoId && url.searchParams.get("__vid") && url.searchParams.get("__vid") !== videoId) {
        return "";
      }
      return url.href;
    } catch (_) {
      return "";
    }
  }

  return { videoIdFromUrl, canonicalUrl, usableMediaUrl };
});
