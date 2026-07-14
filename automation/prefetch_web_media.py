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


def has_substantial_body(text: str) -> bool:
    body = re.sub(r"^---.*?---", "", text, flags=re.S).strip()
    # Ignore the fixed template scaffolding and the source embed line.
    body = re.sub(r"!\[\]\(https?://www\.youtube\.com/watch\?v=[^)]+\)", "", body)
    body = re.sub(r"^#{1,6}\s+.*$", "", body, flags=re.M)
    body = re.sub(r"^\s*[-*]\s+.*$", "", body, flags=re.M)
    return len(body.strip()) >= 800


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
    if not is_youtube(url):
        print(json.dumps({"type": "none", "reason": "not a YouTube URL"}, ensure_ascii=False))
        return 0
    if has_substantial_body(text):
        print(json.dumps({"type": "none", "reason": "clipping already has enough body text"}, ensure_ascii=False))
        return 0

    output = VAULT / "06 - Sources" / ".automation" / "media" / media_id(url)
    transcript_meta = fetch_youtube_transcript(media_id(url), output)
    if transcript_meta:
        result = {"type": "transcript", "directory": str(output), "source": url, **transcript_meta}
        print(json.dumps(result, ensure_ascii=False))
        return 0

    if not (output / "source.mp4").exists() or not (output / "transcript-raw.txt").exists():
        command = [sys.executable, str(VIDEO_SCRIPT), str(clip), str(output)]
        completed = subprocess.run(command, text=True, capture_output=True, timeout=3600)
        if completed.returncode != 0:
            raise RuntimeError((completed.stderr or completed.stdout)[-2000:])
    result = {"type": "video", "directory": str(output), "source": url}
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
