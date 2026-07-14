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


def image_urls(text: str) -> list[str]:
    candidates = re.findall(r'!\[[^\]]*\]\((https?://[^\s)]+)', text)
    candidates += re.findall(r'<img[^>]+src=["\'](https?://[^"\']+)', text, re.I)
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
    output = VAULT / "06 - Sources" / "assets" / "social" / nid
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


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: prefetch_xhs_media.py CLIP.md", file=sys.stderr)
        return 2
    clip = Path(sys.argv[1]).resolve()
    text = clip.read_text(encoding="utf-8")
    url = source_url(text)
    nid = note_id(url)
    if re.search(r'<video\b|blob:https?://', text, re.I):
        # Video and raw transcript are disposable working files. Keep them in
        # the hidden automation cache, never in the permanent knowledge tree.
        output = VAULT / "06 - Sources" / ".automation" / "media" / nid
        if not (output / "source.mp4").exists() or not (output / "transcript-raw.txt").exists():
            command = [sys.executable, str(VIDEO_SCRIPT), str(clip), str(output)]
            completed = subprocess.run(command, text=True, capture_output=True, timeout=3600)
            if completed.returncode != 0:
                raise RuntimeError((completed.stderr or completed.stdout)[-2000:])
        result = {"type": "video", "note_id": nid, "directory": str(output)}
    else:
        result = download_images(text, url, nid)
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
