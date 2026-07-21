#!/usr/bin/env python3
"""Download a supported social video and transcribe it locally with MLX Whisper."""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path


def frontmatter_value(text: str, key: str) -> str | None:
    match = re.search(rf'^{re.escape(key)}:\s*["\']?([^"\'\n]+)', text, re.M)
    return match.group(1).strip() if match else None


def chrome_last_used_profile() -> str | None:
    """Return Chrome's profile directory name without reading cookie values."""
    state = Path.home() / "Library" / "Application Support" / "Google" / "Chrome" / "Local State"
    try:
        data = json.loads(state.read_text(encoding="utf-8"))
        profile = data.get("profile", {}).get("last_used")
        return profile if isinstance(profile, str) and profile else None
    except (OSError, ValueError, TypeError):
        return None


def main() -> int:
    if len(sys.argv) not in {3, 4}:
        print("usage: download_transcribe_video.py CLIP.md OUTPUT_DIR [DOWNLOAD_URL]", file=sys.stderr)
        return 2
    clip = Path(sys.argv[1]).resolve()
    output = Path(sys.argv[2]).resolve()
    output.mkdir(parents=True, exist_ok=True)
    text = clip.read_text(encoding="utf-8")
    captured_media_url = frontmatter_value(text, "media-url")
    if captured_media_url and not captured_media_url.startswith(("http://", "https://")):
        captured_media_url = None
    url = captured_media_url or (sys.argv[3] if len(sys.argv) == 4 else (
        frontmatter_value(text, "source-original") or frontmatter_value(text, "source")
    ))
    if not url:
        raise RuntimeError("missing source URL")

    try:
        import yt_dlp
    except ImportError as exc:
        raise RuntimeError("yt-dlp is not installed") from exc

    template = str(output / "source.%(ext)s")
    common = {
        "outtmpl": template,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "overwrites": False,
    }
    error: Exception | None = None
    info = None
    media = output / "source.mp4"
    if media.exists() and media.stat().st_size > 0:
        info = {"id": "local-prefetch"}
    # Reading browser cookies can expose authenticated sessions. Keep it an
    # explicit opt-in instead of silently probing Chrome after a public fetch.
    allow_browser_cookies = os.environ.get("OBSIDIAN_KNOWLEDGE_BROWSER_COOKIES") == "1"
    cookie_modes = (False, True) if allow_browser_cookies else (False,)
    for cookies in (() if info is not None else cookie_modes):
        opts = dict(common)
        if cookies:
            opts["cookiesfrombrowser"] = ("chrome", chrome_last_used_profile(), None, None)
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                media = Path(ydl.prepare_filename(info))
            if media.exists():
                break
        except Exception as exc:  # yt-dlp exposes several site-specific failures
            error = exc
            info = None
    if info is None or not media.exists():
        raise RuntimeError(f"video download failed: {error}")

    # mlx-whisper shells out to ffmpeg. imageio-ffmpeg supplies a local binary
    # without requiring Homebrew; expose it under the expected executable name.
    try:
        import imageio_ffmpeg
        ffmpeg = Path(imageio_ffmpeg.get_ffmpeg_exe())
        bindir = output / ".bin"
        bindir.mkdir(exist_ok=True)
        link = bindir / "ffmpeg"
        if not link.exists():
            link.symlink_to(ffmpeg)
        os.environ["PATH"] = f"{bindir}:{os.environ.get('PATH', '')}"
        import mlx_whisper
    except ImportError as exc:
        raise RuntimeError("mlx-whisper or imageio-ffmpeg is not installed") from exc

    result = mlx_whisper.transcribe(
        str(media),
        path_or_hf_repo="mlx-community/whisper-large-v3-turbo",
        word_timestamps=False,
    )
    transcript = (result.get("text") or "").strip()
    if not transcript:
        raise RuntimeError("transcription returned empty text")
    raw_path = output / "transcript-raw.txt"
    raw_path.write_text(transcript + "\n", encoding="utf-8")
    metadata = {
        "source_url": url,
        "video": str(media),
        "transcript": str(raw_path),
        "language": result.get("language"),
        "segments": len(result.get("segments") or []),
    }
    (output / "transcription.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(metadata, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
