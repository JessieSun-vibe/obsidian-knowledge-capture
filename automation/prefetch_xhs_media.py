#!/usr/bin/env python3
"""Fetch XHS note media before the sandboxed Codex processing step."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit


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


def source_url(text: str) -> str:
    match = re.search(r'^source:\s*["\']?([^"\'\n]+)', text, re.M)
    if not match:
        raise RuntimeError("missing source URL")
    return match.group(1).strip()


def note_id(url: str) -> str:
    match = re.search(r'/(?:explore|discovery/item)/([0-9a-f]+)', url)
    if not match:
        raise RuntimeError("cannot determine note id")
    return match.group(1)


def xhs_media_section(text: str) -> str:
    """Return the Web Clipper's note-media section, excluding comments/feed."""
    match = re.search(
        r'^### 4\.2 小红书图片 / 视频\s*$\n(.*?)(?=^### |^## |\Z)',
        text,
        re.M | re.S,
    )
    return match.group(1) if match else ""


def image_urls(text: str) -> list[str]:
    # The unified template deliberately isolates the note carousel in 4.2.
    # Never scan the full clipping when that section exists: the rest of an
    # XHS page contains avatars, comment attachments and recommendation cards.
    scoped = xhs_media_section(text)
    candidates = re.findall(r'!\[[^\]]*\]\((https?://[^\s)]+)', scoped)
    candidates += re.findall(r'<img[^>]+src=["\'](https?://[^"\']+)', scoped, re.I)
    retained: list[str] = []
    seen: set[str] = set()
    for url in candidates:
        base = url.split("|")[0]
        host = urlsplit(base).hostname or ""
        lowered = base.lower()
        if "xhscdn.com" not in host:
            continue
        if any(token in lowered for token in ("avatar", "/comment/", "picasso-static", "fe-platform")):
            continue
        canonical = base.split("?")[0]
        if canonical not in seen:
            seen.add(canonical)
            retained.append(base)
    return retained


def download_images(text: str, url: str, nid: str) -> dict:
    urls = image_urls(text)
    if not urls:
        raise RuntimeError("no note image URLs found")
    output = SOURCES_ROOT / "assets" / "social" / nid
    output.mkdir(parents=True, exist_ok=True)
    paths = []
    for index, image_url in enumerate(urls, 1):
        suffix = Path(urlsplit(image_url).path).suffix.lower()
        if suffix not in {".jpg", ".jpeg", ".png", ".webp", ".avif"}:
            suffix = ".webp"
        path = output / f"{index:02d}{suffix}"
        if not path.exists() or path.stat().st_size == 0:
            request = urllib.request.Request(
                image_url,
                headers={"User-Agent": "Mozilla/5.0", "Referer": url},
            )
            with urllib.request.urlopen(request, timeout=60) as response:
                path.write_bytes(response.read())
        paths.append(str(path))
    return {"type": "images", "note_id": nid, "files": paths}


def looks_like_video(text: str) -> bool:
    """Recognize XHS video notes even when the site hides the video element."""
    return bool(
        re.search(r'<video\b|blob:https?://', text, re.I)
        or re.search(r'\b00:00\s+00:00\b', text)
        or ("倍速" in text and "请刷新试试" in text)
    )


def download_video(clip: Path, nid: str) -> dict:
    output = SOURCES_ROOT / ".automation" / "media" / nid
    if not (output / "transcript-raw.txt").exists():
        command = [sys.executable, str(VIDEO_SCRIPT), str(clip), str(output)]
        completed = subprocess.run(command, text=True, capture_output=True, timeout=3600)
        if completed.returncode != 0:
            raise RuntimeError((completed.stderr or completed.stdout)[-2000:])
    return {"type": "video", "note_id": nid, "directory": str(output)}


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: prefetch_xhs_media.py CLIP.md", file=sys.stderr)
        return 2
    clip = Path(sys.argv[1]).resolve()
    text = clip.read_text(encoding="utf-8")
    url = source_url(text)
    nid = note_id(url)
    if looks_like_video(text):
        # Video and raw transcript are disposable working files. Keep them in
        # the hidden automation cache, never in the permanent knowledge tree.
        result = download_video(clip, nid)
    else:
        try:
            result = download_images(text, url, nid)
        except RuntimeError as exc:
            # XHS frequently omits both the real <video> node and note images
            # from Web Clipper output. If there are no note images, try the
            # tokenized source URL as a video before declaring the clip broken.
            if str(exc) != "no note image URLs found":
                raise
            result = download_video(clip, nid)
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
