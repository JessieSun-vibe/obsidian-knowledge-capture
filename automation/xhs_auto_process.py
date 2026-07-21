#!/usr/bin/env python3
"""Watch the Clippings inbox and ask Codex to process pending source notes."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import parse_qs, urlsplit


VAULT = Path(os.environ.get("OBSIDIAN_VAULT", Path.cwd())).expanduser().resolve()
INBOX = VAULT / "Clippings"
SOURCES_MARKER = ".obsidian-knowledge-sources"


def discover_sources_root(vault: Path) -> Path:
    override = os.environ.get("OBSIDIAN_KNOWLEDGE_SOURCES", "").strip("/")
    if override:
        return vault / override
    markers = list(vault.glob(f"*/{SOURCES_MARKER}"))
    if len(markers) == 1:
        return markers[0].parent
    return vault / "06 - Sources"


SOURCES_ROOT = discover_sources_root(VAULT)
SOURCES_ROOT_REL = str(SOURCES_ROOT.relative_to(VAULT))
STATE = SOURCES_ROOT / ".automation"
LOCK = STATE / "xhs-auto-process.lock"
LOG = STATE / "xhs-auto-process.log"
DEFAULT_CODEX = shutil.which("codex") or "/Applications/ChatGPT.app/Contents/Resources/codex"
CODEX = Path(os.environ.get("CODEX_BIN", DEFAULT_CODEX)).expanduser()
PREFETCH = SOURCES_ROOT / "Automation" / "prefetch_xhs_media.py"
PREFETCH_WEB = SOURCES_ROOT / "Automation" / "prefetch_web_media.py"
OUTPUT_MARKER = ".obsidian-knowledge-output"
TOPIC_MARKER = ".obsidian-knowledge-topic"
DEFAULT_TOPICS = {
    "ai": "AI",
    "creator": "自媒体",
    "food": "美食",
    "home": "家居",
    "investing": "投资",
    "product": "产品经理",
    "career": "职场成长",
    "growth": "个人成长",
    "main": "主账号",
    "unclassified": "待判断",
}


def discover_output_root(vault: Path, sources_root: Path | None = None) -> str:
    override = os.environ.get("OBSIDIAN_KNOWLEDGE_OUTPUT", "").strip("/")
    if override:
        return override
    sources = sources_root or discover_sources_root(vault)
    markers = list(sources.glob(f"*/{OUTPUT_MARKER}")) if sources.exists() else []
    if len(markers) == 1:
        return str(markers[0].parent.relative_to(vault))
    return str((sources / "001-input").relative_to(vault))


OUTPUT_ROOT_REL = discover_output_root(VAULT, SOURCES_ROOT)
OUTPUT_ROOT = VAULT / OUTPUT_ROOT_REL


def discover_topic_folders(output_root: Path) -> dict[str, str]:
    """Map stable topic IDs to user-renamable paths under the output root."""
    topics: dict[str, str] = {}
    if output_root.exists():
        for marker in output_root.rglob(TOPIC_MARKER):
            try:
                topic_id = marker.read_text(encoding="utf-8").strip()
                relative = str(marker.parent.relative_to(output_root))
            except (OSError, ValueError):
                continue
            if topic_id in DEFAULT_TOPICS and topic_id not in topics and relative != ".":
                topics[topic_id] = relative
    for topic_id, default_name in DEFAULT_TOPICS.items():
        topics.setdefault(topic_id, default_name)
    return topics


TOPIC_FOLDERS = discover_topic_folders(OUTPUT_ROOT)


def topic_routing_prompt() -> str:
    rows = "\n".join(f"  - {topic_id}: {path}" for topic_id, path in TOPIC_FOLDERS.items())
    return (
        "Choose one stable topic ID and save into its current mapped folder. "
        "Folder display names may have been renamed by the user; use this mapping exactly:\n" + rows
    )


def log(message: str) -> None:
    STATE.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with LOG.open("a", encoding="utf-8") as handle:
        handle.write(f"[{stamp}] {message}\n")


PLATFORM_HOSTS = (
    (("xiaohongshu.com", "xhslink.com"), "小红书"),
    (("douyin.com", "iesdouyin.com"), "抖音"),
    (("youtube.com", "youtu.be"), "YouTube"),
    (("x.com", "twitter.com"), "X"),
    (("mp.weixin.qq.com",), "微信公众号"),
    (("zhihu.com",), "知乎"),
    (("weibo.com", "weibo.cn"), "微博"),
    (("instagram.com",), "Instagram"),
)


def frontmatter_value(text: str, key: str) -> str | None:
    match = re.search(rf'^(?:"{re.escape(key)}"|{re.escape(key)}):\s*["\']?([^"\'\n]+)', text, re.M)
    return match.group(1).strip() if match else None


def detect_platform(url: str) -> str:
    host = (urlsplit(url).hostname or "").lower()
    host = host.removeprefix("www.").removeprefix("m.")
    for suffixes, platform in PLATFORM_HOSTS:
        if any(host == suffix or host.endswith(f".{suffix}") for suffix in suffixes):
            return platform
    return host or "网页"


def canonicalize_source_url(url: str) -> str:
    parsed = urlsplit(url)
    host = (parsed.hostname or "").lower()
    if host.endswith("douyin.com"):
        modal_id = (parse_qs(parsed.query).get("modal_id") or [""])[0]
        if modal_id.isdigit():
            return f"https://www.douyin.com/video/{modal_id}"
    return url


def detect_content_type(url: str, text: str) -> str:
    parsed = urlsplit(url)
    host = (parsed.hostname or "").lower()
    path = parsed.path.lower()
    if "youtu" in host or "douyin.com" in host or "/reel" in path or re.search(r'<video\b|blob:https?://', text, re.I):
        return "video"
    if re.search(r'!\[[^\]]*\]\(https?://|<img\b', text, re.I):
        return "image-post"
    if detect_platform(url) in {"X", "微博", "Instagram", "小红书"}:
        return "text-post"
    return "article"


def invalid_platform_source(url: str) -> str | None:
    """Return a user-facing reason when a platform URL is not a content URL."""
    parsed = urlsplit(url)
    host = (parsed.hostname or "").lower().removeprefix("www.").removeprefix("m.")
    path = parsed.path.rstrip("/")
    if host in {"weibo.com", "weibo.cn"} and not path:
        return "微博剪藏只保存了首页链接；请打开具体微博详情页后重新收藏。"
    return None


def set_frontmatter_value(text: str, key: str, value: str) -> str:
    pattern = rf'^((?:"{re.escape(key)}"|{re.escape(key)}):)\s*.*$'
    replacement = rf'\1 {value}'
    if re.search(pattern, text, re.M):
        return re.sub(pattern, replacement, text, count=1, flags=re.M)
    if text.startswith("---\n"):
        return text.replace("---\n", f"---\n{key}: {value}\n", 1)
    return f"---\n{key}: {value}\n---\n\n{text}"


def normalize_clip(path: Path, text: str) -> tuple[str, str]:
    url = frontmatter_value(text, "source") or ""
    canonical_url = canonicalize_source_url(url)
    platform = detect_platform(url)
    content_type = detect_content_type(url, text)
    updated = set_frontmatter_value(text, "platform", platform)
    updated = set_frontmatter_value(updated, "content-type", content_type)
    if canonical_url != url:
        updated = set_frontmatter_value(updated, "source-original", url)
        updated = set_frontmatter_value(updated, "source", canonical_url)
    if updated != text:
        path.write_text(updated, encoding="utf-8")
    return platform, content_type


def pending_clips() -> list[Path]:
    clips: list[Path] = []
    for path in INBOX.glob("*.md"):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        material_type = frontmatter_value(text, "type")
        is_pending = re.search(r'^(?:"process-status"|process-status):\s*["\']?待处理["\']?\s*$', text, re.M)
        if material_type in {"source-material", "web-material", "social-material"} and is_pending:
            if time.time() - path.stat().st_mtime >= 10:
                clips.append(path)
    return sorted(clips, key=lambda p: p.stat().st_mtime)


def linked_card(clip: Path) -> Path | None:
    if not clip.exists():
        return None
    text = clip.read_text(encoding="utf-8")
    status = re.search(r'^(?:"process-status"|process-status):\s*["\']?([^"\'\n]+)', text, re.M)
    link = re.search(r'^(?:"knowledge-note"|knowledge-note):\s*["\']?\[\[([^\]|]+)', text, re.M)
    done_statuses = {"已沉淀", "已沉澱"}
    if not status or status.group(1).strip() not in done_statuses or not link:
        return None
    name = link.group(1).strip()
    search_roots = [
        OUTPUT_ROOT,
        SOURCES_ROOT / "素材",
        SOURCES_ROOT / "Knowledge",
        VAULT / "06 - Sources" / "素材",
        VAULT / "06 - Sources" / "Knowledge",
    ]
    matches: list[Path] = []
    # Codex may write either a basename wikilink (`[[card]]`) or a
    # vault-relative wikilink (`[[06 - Sources/001-input/topic/card]]`).
    # Resolve the latter directly, but only when it remains inside a known
    # knowledge-card root.
    if "/" in name:
        direct = VAULT / (name if name.endswith(".md") else f"{name}.md")
        resolved = direct.resolve()
        if direct.exists() and any(
            root.exists() and resolved.is_relative_to(root.resolve())
            for root in search_roots
        ):
            matches.append(direct)
    for root in search_roots:
        if root.exists():
            basename = Path(name).name.removesuffix(".md")
            matches.extend(root.glob(f"**/{basename}.md"))
    matches = list({str(path.resolve()): path for path in matches}.values())
    if len(matches) != 1:
        return None
    card_text = matches[0].read_text(encoding="utf-8")
    if "status: 已沉淀" not in card_text and "status: 已沉澱" not in card_text:
        return None
    if not re.search(r'^(?:"source"|source):\s*["\']?https?://', card_text, re.M):
        return None
    return matches[0]


def cleanup_temporary_media(clip_text: str) -> None:
    """Remove verified temporary video/transcript data left by an older run."""
    url = frontmatter_value(clip_text, "source-original") or frontmatter_value(clip_text, "source") or ""
    match = re.search(r"/(?:explore|discovery/item)/([A-Za-z0-9_-]+)", url)
    if not match:
        return
    media_dir = (STATE / "media" / match.group(1)).resolve()
    allowed_root = (STATE / "media").resolve()
    if media_dir.is_relative_to(allowed_root):
        shutil.rmtree(media_dir, ignore_errors=True)


def normalize_card_image_width(card: Path, width: int = 700) -> None:
    """Keep original assets but cap embedded social images in Obsidian."""
    text = card.read_text(encoding="utf-8")
    sources_prefix = re.escape(SOURCES_ROOT_REL.rstrip("/"))
    pattern = rf'!\[\[({sources_prefix}/assets/social/[^\]|\n]+)(?:\|\d+)?\]\]'
    updated = re.sub(pattern, rf'![[\1|{width}]]', text)
    if updated != text:
        card.write_text(updated, encoding="utf-8")


def cleanup_verified_clips() -> None:
    """Delete completed raw clips left behind by an older verifier."""
    for clip in INBOX.glob("*.md"):
        try:
            card = linked_card(clip)
        except OSError:
            continue
        if card is None:
            continue
        clip_text = clip.read_text(encoding="utf-8")
        normalize_card_image_width(card)
        cleanup_temporary_media(clip_text)
        clip.unlink()
        log(f"cleanup: verified {card.relative_to(VAULT)}; deleted completed raw clip {clip.name}")


def process_xhs(clip: Path) -> bool:
    local_media = ""
    try:
        prepared = subprocess.run(
            [sys.executable, str(PREFETCH), str(clip)],
            cwd=VAULT,
            text=True,
            capture_output=True,
            timeout=7200,
        )
        if prepared.returncode == 0:
            local_media = prepared.stdout.strip()
            log(f"media prepared: {local_media}")
        else:
            log("media prefetch failed: " + (prepared.stderr or prepared.stdout)[-2000:].replace("\n", " | "))
    except Exception as exc:
        log(f"media prefetch exception: {exc}")

    prompt = f"""Use $xhs-knowledge-capture to process exactly this new Obsidian clipping:
{clip}

The trusted Obsidian prefetch step reported this local media result:
{local_media or "Media prefetch failed; record the failure and preserve the raw clip."}

This is an unattended automation run. Follow the skill completely.
- Save the final knowledge card under `{OUTPUT_ROOT_REL}/<primary-folder>/`. This configured output root overrides any older default path mentioned by the skill.
- {topic_routing_prompt()}
- For a video note, use the already-downloaded local video and transcript reported above. Do not attempt network access. Turn the complete transcript into a clean spoken script by removing filler words such as 嗯、啊、呃, false starts, and meaningless repetition while preserving meaning and factual details. Put both the cleaned spoken script and knowledge extraction in the knowledge card.
- For an image note, use every local image reported above. Do not attempt network access.
- Embed each retained local image as an Obsidian wikilink with a 700px display width, for example `![[path/to/image.webp|700]]`. Keep the original image file unchanged.
- If the actual video cannot be downloaded or transcribed, set process-status to 等待视频, explain the failure in the raw clipping, and do not set the knowledge card to 已沉淀.
- For image posts, inspect every retained image before completion.
- If the source body or transcript is predominantly English, preserve the English and add a faithful Chinese translation immediately after each semantic sentence or short paragraph. Do not put all English and all Chinese in separate distant sections.
- On complete success, set both the raw clip process-status and the knowledge card status to 已沉淀.
- The raw clipping will be deleted after verification. Do not keep a `source-clip` wikilink in the final knowledge card; retain the canonical `source` URL instead.
- Do not delete the raw clipping yourself. The deterministic watcher will delete it only after verification.
"""
    cmd = [
        str(CODEX), "exec", "--ephemeral", "--skip-git-repo-check",
        "--sandbox", "workspace-write", "--cd", str(VAULT), prompt,
    ]
    log(f"processing {clip.name}")
    result = subprocess.run(cmd, cwd=VAULT, text=True, capture_output=True, timeout=7200)
    if result.stdout:
        log("codex stdout: " + result.stdout[-4000:].replace("\n", " | "))
    if result.stderr:
        log("codex stderr: " + result.stderr[-2000:].replace("\n", " | "))
    if result.returncode != 0:
        log(f"codex failed ({result.returncode}); preserving {clip.name}")
        return False
    card = linked_card(clip)
    if card is None:
        log(f"verification incomplete; preserving {clip.name}")
        return False
    normalize_card_image_width(card)
    clip.unlink()
    try:
        media_info = json.loads(local_media) if local_media else {}
        if media_info.get("type") == "video" and media_info.get("directory"):
            media_dir = Path(media_info["directory"]).resolve()
            allowed_root = (STATE / "media").resolve()
            if media_dir.is_relative_to(allowed_root):
                shutil.rmtree(media_dir, ignore_errors=True)
    except Exception as exc:
        log(f"temporary media cleanup warning: {exc}")
    log(f"complete: {card.relative_to(VAULT)}; deleted raw clip and temporary video")
    return True


def process_web(clip: Path) -> bool:
    local_media = ""
    try:
        prepared = subprocess.run(
            [sys.executable, str(PREFETCH_WEB), str(clip)],
            cwd=VAULT,
            text=True,
            capture_output=True,
            timeout=7200,
        )
        if prepared.returncode == 0:
            local_media = prepared.stdout.strip()
            log(f"web media prepared: {local_media}")
        else:
            log("web media prefetch failed: " + (prepared.stderr or prepared.stdout)[-2000:].replace("\n", " | "))
    except Exception as exc:
        log(f"web media prefetch exception: {exc}")

    prompt = f"""Use $web-knowledge-capture to process exactly this new Obsidian Web Clipper note:
{clip}

The trusted Obsidian prefetch step reported this local media result:
{local_media or "Media prefetch did not provide additional content."}

This is an unattended automation run. Follow the skill completely.
- Save the final knowledge card under `{OUTPUT_ROOT_REL}/<primary-folder>/`. This configured output root overrides any older default path mentioned by the skill.
- {topic_routing_prompt()}
- Prefer the text captured in the raw clipping and any already-downloaded local transcript reported above.
- If an ordinary webpage or social post lacks enough body text and a `wigolo` MCP fetch tool is configured, use it once on the canonical `source` URL to recover page text and metadata. Do not use general web search. If Wigolo is unavailable or still returns insufficient content, preserve the clip with process-status 等待内容.
- Do not download external video inside Codex; video retrieval belongs to the trusted prefetch step.
- If this is a YouTube or spoken-video note and a local transcript is reported above, read the complete transcript file. Turn it into a clean spoken script by removing filler words, timestamp noise, duplicated subtitle fragments, and meaningless repetition while preserving meaning and factual details.
- If this is a YouTube or spoken-video note and the clipping itself contains transcript text, use the captured transcript.
- If this is an ordinary webpage or article, omit `## 五、清理后的口播稿`.
- If the source body or transcript is predominantly English, preserve the English and add a faithful Chinese translation immediately after each semantic sentence or short paragraph. Do not put all English and all Chinese in separate distant sections.
- If the clipping does not contain enough body text or transcript to support a knowledge card, set process-status to 等待内容, explain the failure in the raw clipping, and do not set the knowledge card to 已沉淀.
- On complete success, set both the raw clip process-status and the knowledge card status to 已沉淀.
- The raw clipping will be deleted after verification. Do not keep a `source-clip` wikilink in the final knowledge card; retain the canonical `source` URL instead.
- Do not delete the raw clipping yourself. The deterministic watcher will delete it only after verification.
"""
    cmd = [
        str(CODEX), "exec", "--ephemeral", "--skip-git-repo-check",
        "--sandbox", "workspace-write", "--cd", str(VAULT), prompt,
    ]
    log(f"processing web {clip.name}")
    result = subprocess.run(cmd, cwd=VAULT, text=True, capture_output=True, timeout=7200)
    if result.stdout:
        log("codex stdout: " + result.stdout[-4000:].replace("\n", " | "))
    if result.stderr:
        log("codex stderr: " + result.stderr[-2000:].replace("\n", " | "))
    if result.returncode != 0:
        log(f"codex failed ({result.returncode}); preserving {clip.name}")
        return False
    card = linked_card(clip)
    if card is None:
        log(f"verification incomplete; preserving {clip.name}")
        return False
    clip.unlink()
    try:
        media_info = json.loads(local_media) if local_media else {}
        if media_info.get("type") in {"video", "transcript"} and media_info.get("directory"):
            media_dir = Path(media_info["directory"]).resolve()
            allowed_root = (STATE / "media").resolve()
            if media_dir.is_relative_to(allowed_root):
                shutil.rmtree(media_dir, ignore_errors=True)
    except Exception as exc:
        log(f"temporary web media cleanup warning: {exc}")
    log(f"complete: {card.relative_to(VAULT)}; deleted raw web clip")
    return True


def main() -> int:
    if not CODEX.exists():
        log(f"Codex binary missing: {CODEX}")
        return 2
    STATE.mkdir(parents=True, exist_ok=True)
    try:
        LOCK.mkdir()
    except FileExistsError:
        # Recover a stale lock after two hours.
        if time.time() - LOCK.stat().st_mtime > 7200:
            shutil.rmtree(LOCK, ignore_errors=True)
            LOCK.mkdir()
        else:
            return 0
    try:
        for clip in pending_clips():
            text = clip.read_text(encoding="utf-8")
            platform, content_type = normalize_clip(clip, text)
            log(f"detected {platform}/{content_type}: {clip.name}")
            url = frontmatter_value(text, "source") or ""
            invalid_reason = invalid_platform_source(url)
            if invalid_reason:
                updated = set_frontmatter_value(clip.read_text(encoding="utf-8"), "process-status", "等待链接")
                updated += f"\n\n## 自动处理记录\n\n{invalid_reason}\n"
                clip.write_text(updated, encoding="utf-8")
                log(f"invalid source; preserving {clip.name}: {invalid_reason}")
                continue
            if platform == "小红书":
                process_xhs(clip)
            else:
                process_web(clip)
        cleanup_verified_clips()
        return 0
    finally:
        shutil.rmtree(LOCK, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
