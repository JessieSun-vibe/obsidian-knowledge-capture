const assert = require("assert");
const core = require("../chrome-extension/douyin-core.js");

assert.strictEqual(
  core.videoIdFromUrl("https://www.douyin.com/jingxuan?modal_id=7630838709557923123"),
  "7630838709557923123"
);
assert.strictEqual(
  core.videoIdFromUrl("https://www.douyin.com/video/7630838709557923123"),
  "7630838709557923123"
);
assert.strictEqual(
  core.canonicalUrl("7630838709557923123"),
  "https://www.douyin.com/video/7630838709557923123"
);
assert.strictEqual(core.usableMediaUrl("blob:https://www.douyin.com/abc", "7630838709557923123"), "");
assert.strictEqual(
  core.usableMediaUrl("https://v3-dy-o.zjcdn.com/path?mime_type=video_mp4&__vid=7630838709557923123", "7630838709557923123"),
  "https://v3-dy-o.zjcdn.com/path?mime_type=video_mp4&__vid=7630838709557923123"
);
assert.strictEqual(
  core.usableMediaUrl("https://v3-dy-o.zjcdn.com/path?mime_type=video_mp4&__vid=1", "7630838709557923123"),
  ""
);

console.log("Douyin extension tests passed");
