#!/usr/bin/env python3
"""Extract deterministic metadata and unique note images from a raw XHS clip."""

from __future__ import annotations

import json
import mimetypes
import re
import sys
import urllib.request
from pathlib import Path


def frontmatter_value(text: str, key: str) -> str:
    block = text.split("---", 2)[1] if text.startswith("---") and text.count("---") >= 2 else ""
    match = re.search(rf"(?m)^{re.escape(key)}:[ \t]*(.*)$", block)
    if not match:
        return ""
    value = match.group(1).strip().strip('"')
    if value:
        return value
    tail = block[match.end():]
    list_match = re.match(r"\s*\n\s*-\s*[\"']?([^\n\"']+)", tail)
    return list_match.group(1).strip() if list_match else ""


def canonical_xhs_url(value: str) -> str:
    match = re.search(r"https?://www\.xiaohongshu\.com/(?:explore|discovery/item)/[0-9a-zA-Z]+", value)
    return match.group(0) if match else value.split("?", 1)[0]


def unique_note_images(text: str) -> list[str]:
    # Default full-page clips usually place the active carousel after the last
    # "回到顶部" marker. Scoping to that tail avoids profile/recommendation art.
    media_text = text.rsplit("回到顶部", 1)[-1] if "回到顶部" in text else text
    urls = re.findall(r"https?://[^\s)]+", media_text)
    result: list[str] = []
    seen: set[str] = set()
    for url in urls:
        if "/notes_pre_post/" not in url and "/note_post/" not in url:
            continue
        clean = url.rstrip(".,]")
        identity = clean.split("/notes_pre_post/", 1)[-1].split("?", 1)[0]
        if identity in seen:
            continue
        seen.add(identity)
        result.append(clean)
    return result


def download_images(urls: list[str], output_dir: Path) -> list[str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    saved: list[str] = []
    for index, url in enumerate(urls, start=1):
        request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(request, timeout=30) as response:
            content_type = response.headers.get_content_type()
            extension = mimetypes.guess_extension(content_type) or ".webp"
            if extension == ".jpe":
                extension = ".jpg"
            target = output_dir / f"{index:02d}{extension}"
            target.write_bytes(response.read())
            saved.append(str(target))
    return saved


def main() -> int:
    if len(sys.argv) not in (2, 4) or (len(sys.argv) == 4 and sys.argv[2] != "--download-dir"):
        print("usage: extract_clip.py CLIP.md [--download-dir DIR]", file=sys.stderr)
        return 2
    path = Path(sys.argv[1])
    text = path.read_text(encoding="utf-8")
    images = unique_note_images(text)
    data = {
        "path": str(path),
        "title": frontmatter_value(text, "title") or path.stem,
        "source": canonical_xhs_url(frontmatter_value(text, "source")),
        "author": frontmatter_value(text, "author").replace("[[", "").replace("]]", ""),
        "published": frontmatter_value(text, "published"),
        "created": frontmatter_value(text, "created"),
        "description": frontmatter_value(text, "description"),
        "images": images,
    }
    if len(sys.argv) == 4:
        data["local_images"] = download_images(images, Path(sys.argv[3]))
    print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
