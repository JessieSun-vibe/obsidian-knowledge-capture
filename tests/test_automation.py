from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "capture_automation", ROOT / "automation" / "xhs_auto_process.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)

PREFETCH_SPEC = importlib.util.spec_from_file_location(
    "prefetch_xhs_media", ROOT / "automation" / "prefetch_xhs_media.py"
)
PREFETCH = importlib.util.module_from_spec(PREFETCH_SPEC)
assert PREFETCH_SPEC and PREFETCH_SPEC.loader
PREFETCH_SPEC.loader.exec_module(PREFETCH)


class PlatformDetectionTests(unittest.TestCase):
    def test_xhs_image_extraction_ignores_feed_and_comment_images(self) -> None:
        text = """## 三、原始内容

![](https://sns-webpic-qc.xhscdn.com/feed/recommend.webp)

### 4.2 小红书图片 / 视频

![](https://sns-webpic-qc.xhscdn.com/note/page-1.webp)
![](https://sns-webpic-qc.xhscdn.com/note/page-1.webp)

### 4.3 小红书可见评论

![](https://sns-avatar-qc.xhscdn.com/avatar/user.webp)
![](https://sns-webpic-qc.xhscdn.com/comment/reply.webp)
"""
        self.assertEqual(
            PREFETCH.image_urls(text),
            ["https://sns-webpic-qc.xhscdn.com/note/page-1.webp"],
        )

    def test_supported_platforms(self) -> None:
        cases = {
            "https://x.com/example/status/1": "X",
            "https://mp.weixin.qq.com/s/abc": "微信公众号",
            "https://www.zhihu.com/question/1/answer/2": "知乎",
            "https://weibo.com/123/abc": "微博",
            "https://www.xiaohongshu.com/explore/abc": "小红书",
            "https://www.instagram.com/reel/abc/": "Instagram",
            "https://www.douyin.com/video/123": "抖音",
            "https://youtu.be/abc": "YouTube",
        }
        for url, expected in cases.items():
            with self.subTest(url=url):
                self.assertEqual(MODULE.detect_platform(url), expected)

    def test_content_type(self) -> None:
        self.assertEqual(MODULE.detect_content_type("https://youtu.be/abc", "body"), "video")
        self.assertEqual(
            MODULE.detect_content_type("https://www.instagram.com/reel/abc/", "body"), "video"
        )
        self.assertEqual(
            MODULE.detect_content_type("https://example.com/article", "article body"), "article"
        )

    def test_rejects_weibo_homepage_as_source(self) -> None:
        self.assertIsNotNone(MODULE.invalid_platform_source("https://weibo.com/"))
        self.assertIsNone(MODULE.invalid_platform_source("https://weibo.com/123/AbCdE"))

    def test_canonicalizes_douyin_modal_url(self) -> None:
        self.assertEqual(
            MODULE.canonicalize_source_url(
                "https://www.douyin.com/jingxuan?modal_id=7659690963295626377"
            ),
            "https://www.douyin.com/video/7659690963295626377",
        )

    def test_normalize_unified_clip(self) -> None:
        text = """---
type: source-material
platform: auto
source: https://x.com/example/status/1
content-type: auto
process-status: 待处理
---

An English source body.
"""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "clip.md"
            path.write_text(text, encoding="utf-8")
            platform, content_type = MODULE.normalize_clip(path, text)
            updated = path.read_text(encoding="utf-8")
        self.assertEqual(platform, "X")
        self.assertEqual(content_type, "text-post")
        self.assertIn("platform: X", updated)
        self.assertIn("content-type: text-post", updated)

    def test_linked_card_accepts_quoted_source_url(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            vault = Path(directory)
            clip = vault / "Clippings" / "raw.md"
            card = vault / "06 - Sources" / "素材" / "投资" / "card.md"
            clip.parent.mkdir(parents=True)
            card.parent.mkdir(parents=True)
            clip.write_text(
                "---\nprocess-status: 已沉淀\nknowledge-note: \"[[card]]\"\n---\n",
                encoding="utf-8",
            )
            card.write_text(
                '---\nstatus: 已沉淀\nsource: "https://x.com/example/status/1"\n---\n',
                encoding="utf-8",
            )
            original_vault = MODULE.VAULT
            MODULE.VAULT = vault
            try:
                self.assertEqual(MODULE.linked_card(clip), card)
            finally:
                MODULE.VAULT = original_vault

    def test_linked_card_accepts_vault_relative_wikilink(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            vault = Path(directory)
            clip = vault / "Clippings" / "raw.md"
            card = vault / "06 - Sources" / "001-input" / "个人成长" / "card.md"
            clip.parent.mkdir(parents=True)
            card.parent.mkdir(parents=True)
            clip.write_text(
                '---\nprocess-status: 已沉淀\nknowledge-note: "[[06 - Sources/001-input/个人成长/card]]"\n---\n',
                encoding="utf-8",
            )
            card.write_text(
                '---\nstatus: 已沉淀\nsource: "https://example.com/source"\n---\n',
                encoding="utf-8",
            )
            original_vault = MODULE.VAULT
            original_output = MODULE.OUTPUT_ROOT
            MODULE.VAULT = vault
            MODULE.OUTPUT_ROOT = vault / "06 - Sources" / "001-input"
            try:
                self.assertEqual(MODULE.linked_card(clip), card)
            finally:
                MODULE.VAULT = original_vault
                MODULE.OUTPUT_ROOT = original_output

    def test_cleanup_temporary_xhs_media(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory) / ".automation"
            media = state / "media" / "6a1c44c2000000003502e864"
            media.mkdir(parents=True)
            (media / "source.mp4").write_bytes(b"video")
            original_state = MODULE.STATE
            MODULE.STATE = state
            try:
                MODULE.cleanup_temporary_media(
                    "source-original: https://www.xiaohongshu.com/explore/6a1c44c2000000003502e864?token=x\n"
                )
                self.assertFalse(media.exists())
            finally:
                MODULE.STATE = original_state

    def test_normalize_card_image_width_preserves_original_asset(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            vault = Path(directory)
            card = vault / "card.md"
            card.write_text(
                "![[Renamed Sources/assets/social/note/01.webp]]\n"
                "![[Renamed Sources/assets/social/note/02.webp|1200]]\n"
                "![[unrelated/image.webp]]\n",
                encoding="utf-8",
            )
            original_sources_rel = MODULE.SOURCES_ROOT_REL
            MODULE.SOURCES_ROOT_REL = "Renamed Sources"
            try:
                MODULE.normalize_card_image_width(card)
            finally:
                MODULE.SOURCES_ROOT_REL = original_sources_rel
            updated = card.read_text(encoding="utf-8")
            self.assertIn(
                "![[Renamed Sources/assets/social/note/01.webp|700]]", updated
            )
            self.assertIn(
                "![[Renamed Sources/assets/social/note/02.webp|700]]", updated
            )
            self.assertIn("![[unrelated/image.webp]]", updated)

    def test_default_output_root(self) -> None:
        self.assertEqual(MODULE.OUTPUT_ROOT_REL, "06 - Sources/001-input")

    def test_output_root_follows_marker_after_rename(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            vault = Path(directory)
            renamed = vault / "06 - Sources" / "my-renamed-input"
            renamed.mkdir(parents=True)
            (renamed / MODULE.OUTPUT_MARKER).write_text("marker\n", encoding="utf-8")
            self.assertEqual(
                MODULE.discover_output_root(vault), "06 - Sources/my-renamed-input"
            )

    def test_sources_root_follows_marker_after_rename(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            vault = Path(directory)
            renamed = vault / "09-知识来源"
            renamed.mkdir(parents=True)
            (renamed / MODULE.SOURCES_MARKER).write_text("marker\n", encoding="utf-8")
            self.assertEqual(MODULE.discover_sources_root(vault), renamed)

    def test_topic_folder_follows_marker_after_rename(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "006-素材"
            renamed = output / "人工智能"
            renamed.mkdir(parents=True)
            (renamed / MODULE.TOPIC_MARKER).write_text("ai\n", encoding="utf-8")
            topics = MODULE.discover_topic_folders(output)
            self.assertEqual(topics["ai"], "人工智能")
            self.assertEqual(topics["investing"], "投资")


if __name__ == "__main__":
    unittest.main()
