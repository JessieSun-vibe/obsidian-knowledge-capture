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


VAULT = Path(os.environ.get("OBSIDIAN_VAULT", Path.cwd())).expanduser().resolve()
INBOX = VAULT / "Clippings"
STATE = VAULT / "06 - Sources" / ".automation"
LOCK = STATE / "xhs-auto-process.lock"
LOG = STATE / "xhs-auto-process.log"
CODEX = Path(os.environ.get("CODEX_BIN", "/Applications/ChatGPT.app/Contents/Resources/codex")).expanduser()
PREFETCH = VAULT / "06 - Sources" / "Automation" / "prefetch_xhs_media.py"
PREFETCH_WEB = VAULT / "06 - Sources" / "Automation" / "prefetch_web_media.py"


def log(message: str) -> None:
    STATE.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with LOG.open("a", encoding="utf-8") as handle:
        handle.write(f"[{stamp}] {message}\n")


def pending_xhs_clips() -> list[Path]:
    clips: list[Path] = []
    for path in INBOX.glob("*.md"):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        if re.search(r'^platform:\s*["\']?小红书["\']?\s*$', text, re.M) and re.search(
            r'^(?:"process-status"|process-status):\s*["\']?待处理["\']?\s*$', text, re.M
        ):
            if time.time() - path.stat().st_mtime >= 10:
                clips.append(path)
    return sorted(clips, key=lambda p: p.stat().st_mtime)


def pending_web_clips() -> list[Path]:
    clips: list[Path] = []
    for path in INBOX.glob("*.md"):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        is_web = re.search(r'^type:\s*["\']?web-material["\']?\s*$', text, re.M)
        is_pending = re.search(r'^(?:"process-status"|process-status):\s*["\']?待处理["\']?\s*$', text, re.M)
        is_xhs = re.search(r'^platform:\s*["\']?小红书["\']?\s*$', text, re.M)
        if is_web and is_pending and not is_xhs:
            if time.time() - path.stat().st_mtime >= 10:
                clips.append(path)
    return sorted(clips, key=lambda p: p.stat().st_mtime)


def linked_card(clip: Path) -> Path | None:
    if not clip.exists():
        return None
    text = clip.read_text(encoding="utf-8")
    status = re.search(r'^(?:"process-status"|process-status):\s*["\']?([^"\'\n]+)', text, re.M)
    link = re.search(r'^knowledge-note:\s*["\']?\[\[([^\]|]+)', text, re.M)
    done_statuses = {"已沉淀", "已沉澱"}
    if not status or status.group(1).strip() not in done_statuses or not link:
        return None
    name = link.group(1).strip()
    search_roots = [
        VAULT / "06 - Sources" / "素材",
        VAULT / "06 - Sources" / "Knowledge",
    ]
    matches = []
    for root in search_roots:
        if root.exists():
            matches.extend(root.glob(f"**/{name}.md"))
    if len(matches) != 1:
        return None
    card_text = matches[0].read_text(encoding="utf-8")
    if "status: 已沉淀" not in card_text and "status: 已沉澱" not in card_text:
        return None
    if not re.search(r'^source:\s*https?://', card_text, re.M):
        return None
    return matches[0]


def process_xhs(clip: Path) -> bool:
    local_media = ""
    try:
        prepared = subprocess.run(
            [sys.executable, str(PREFETCH), str(clip)],
            cwd=VAULT,
            text=True,
            capture_output=True,
            timeout=3600,
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
- For a video note, use the already-downloaded local video and transcript reported above. Do not attempt network access. Turn the complete transcript into a clean spoken script by removing filler words such as 嗯、啊、呃, false starts, and meaningless repetition while preserving meaning and factual details. Put both the cleaned spoken script and knowledge extraction in the knowledge card.
- For an image note, use every local image reported above. Do not attempt network access.
- If the actual video cannot be downloaded or transcribed, set process-status to 等待视频, explain the failure in the raw clipping, and do not set the knowledge card to 已沉淀.
- For image posts, inspect every retained image before completion.
- On complete success, set both the raw clip process-status and the knowledge card status to 已沉淀.
- The raw clipping will be deleted after verification. Do not keep a `source-clip` wikilink in the final knowledge card; retain the canonical `source` URL instead.
- Do not delete the raw clipping yourself. The deterministic watcher will delete it only after verification.
"""
    cmd = [
        str(CODEX), "exec", "--ephemeral", "--skip-git-repo-check",
        "--sandbox", "workspace-write", "--cd", str(VAULT), prompt,
    ]
    log(f"processing {clip.name}")
    result = subprocess.run(cmd, cwd=VAULT, text=True, capture_output=True, timeout=3600)
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
            timeout=3600,
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
- Use only the text captured in the raw clipping and any already-downloaded local transcript reported above. Do not browse, download media, or attempt network access inside Codex.
- If this is a YouTube or spoken-video note and a local transcript is reported above, read the complete transcript file. Turn it into a clean spoken script by removing filler words, timestamp noise, duplicated subtitle fragments, and meaningless repetition while preserving meaning and factual details.
- If this is a YouTube or spoken-video note and the clipping itself contains transcript text, use the captured transcript.
- If this is an ordinary webpage or article, omit `## 五、清理后的口播稿`.
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
    result = subprocess.run(cmd, cwd=VAULT, text=True, capture_output=True, timeout=3600)
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
        if media_info.get("type") == "video" and media_info.get("directory"):
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
        for clip in pending_xhs_clips():
            process_xhs(clip)
        for clip in pending_web_clips():
            process_web(clip)
        return 0
    finally:
        shutil.rmtree(LOCK, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
