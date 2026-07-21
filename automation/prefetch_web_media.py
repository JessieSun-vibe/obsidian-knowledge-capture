#!/usr/bin/env python3
"""Fetch generic web media before the sandboxed Codex processing step."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from hashlib import sha1
from pathlib import Path
from urllib.parse import parse_qs, urlsplit


VAULT = Path(os.environ.get("OBSIDIAN_VAULT", Path.cwd())).expanduser().resolve()
CODEX_HOME = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser()
VIDEO_SCRIPT = CODEX_HOME / "skills" / "xhs-knowledge-capture" / "scripts" / "download_transcribe_video.py"
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


def frontmatter_value(text: str, key: str) -> str | None:
    match = re.search(rf'^{re.escape(key)}:\s*["\']?([^"\'\n]+)', text, re.M)
    return match.group(1).strip() if match else None


def source_url(text: str) -> str:
    url = frontmatter_value(text, "source")
    if not url:
        raise RuntimeError("missing source URL")
    return url


def is_youtube(url: str) -> bool:
    host = (urlsplit(url).hostname or "").lower()
    return host in {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"}


def is_supported_video_url(url: str) -> bool:
    parsed = urlsplit(url)
    host = (parsed.hostname or "").lower()
    path = parsed.path.lower()
    return (
        is_youtube(url)
        or host.endswith("douyin.com")
        or host.endswith("iesdouyin.com")
        or (host.endswith("instagram.com") and path.startswith(("/reel/", "/reels/")))
    )


def media_id(url: str) -> str:
    parsed = urlsplit(url)
    host = (parsed.hostname or "").lower()
    if host == "youtu.be":
        value = parsed.path.strip("/").split("/")[0]
    else:
        value = (parse_qs(parsed.query).get("v") or [""])[0]
    if not value:
        value = sha1(url.encode("utf-8")).hexdigest()[:16]
    return re.sub(r"[^A-Za-z0-9_-]+", "-", value)


def normalized_video_url(url: str) -> str:
    """Convert modal/feed URLs into stable video-detail URLs for yt-dlp."""
    parsed = urlsplit(url)
    host = (parsed.hostname or "").lower()
    if host.endswith("douyin.com"):
        modal_id = (parse_qs(parsed.query).get("modal_id") or [""])[0]
        if modal_id.isdigit():
            return f"https://www.douyin.com/video/{modal_id}"
    return url


def has_explicit_transcript(text: str) -> bool:
    """Only skip video retrieval for text explicitly captured as a transcript."""
    return bool(
        re.search(r"^(?:#{1,6}\s*)?(?:完整)?(?:逐字稿|视频转录|Transcript)\b", text, re.M | re.I)
        and len(re.sub(r"^---.*?---", "", text, flags=re.S).strip()) >= 800
    )


def fetch_youtube_transcript(video_id: str, output: Path) -> dict | None:
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError:
        return None
    try:
        transcript = YouTubeTranscriptApi().fetch(
            video_id,
            languages=("zh-Hans", "zh-CN", "zh", "en", "en-US"),
            preserve_formatting=False,
        )
    except Exception:
        return None

    lines: list[str] = []
    for item in transcript:
        text = getattr(item, "text", "") if not isinstance(item, dict) else item.get("text", "")
        text = re.sub(r"\s+", " ", text or "").strip()
        if text:
            lines.append(text)
    if not lines:
        return None
    output.mkdir(parents=True, exist_ok=True)
    raw_path = output / "transcript-raw.txt"
    raw_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    metadata = {
        "source": "youtube-transcript-api",
        "transcript": str(raw_path),
        "segments": len(lines),
        "language": getattr(transcript, "language_code", None),
    }
    (output / "transcription.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return metadata


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: prefetch_web_media.py CLIP.md", file=sys.stderr)
        return 2
    clip = Path(sys.argv[1]).resolve()
    text = clip.read_text(encoding="utf-8")
    url = source_url(text)
    if not is_supported_video_url(url):
        print(json.dumps({"type": "none", "reason": "not a supported video URL"}, ensure_ascii=False))
        return 0
    if has_explicit_transcript(text):
        print(json.dumps({"type": "none", "reason": "clipping contains an explicit transcript"}, ensure_ascii=False))
        return 0

    download_url = normalized_video_url(url)
    output = SOURCES_ROOT / ".automation" / "media" / media_id(download_url)
    transcript_meta = fetch_youtube_transcript(media_id(url), output) if is_youtube(url) else None
    if transcript_meta:
        result = {"type": "transcript", "directory": str(output), "source": url, **transcript_meta}
        print(json.dumps(result, ensure_ascii=False))
        return 0

    if not (output / "source.mp4").exists() or not (output / "transcript-raw.txt").exists():
        command = [sys.executable, str(VIDEO_SCRIPT), str(clip), str(output), download_url]
        completed = subprocess.run(command, text=True, capture_output=True, timeout=3600)
        if completed.returncode != 0:
            raise RuntimeError((completed.stderr or completed.stdout)[-2000:])
    result = {"type": "video", "directory": str(output), "source": url}
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
