#!/usr/bin/env python3
"""Install Obsidian Knowledge Capture into a local Obsidian vault.

Usage:
  python3 install.py --vault "/path/to/your/Obsidian Vault"

This installer copies:
- Codex skills into ~/.codex/skills
- Obsidian plugin into <vault>/.obsidian/plugins/xhs-auto-process
- automation scripts into the marked Sources root's `Automation/`
- Web Clipper templates into the marked Sources root's `Templates/`
- default empty material folders into the marked Sources root's `001-input/`
"""

from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUT_MARKER = ".obsidian-knowledge-output"
TOPIC_MARKER = ".obsidian-knowledge-topic"
SOURCES_MARKER = ".obsidian-knowledge-sources"
DEFAULT_FOLDERS = {
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


def copytree(src: Path, dst: Path) -> None:
    # Upgrade package-owned files in place. Do not delete additional files a
    # user may have added to the installed skill, plugin, or helper directory.
    shutil.copytree(src, dst, dirs_exist_ok=True)


def copy_files(src_dir: Path, dst_dir: Path) -> None:
    dst_dir.mkdir(parents=True, exist_ok=True)
    for path in src_dir.iterdir():
        if path.is_file():
            shutil.copy2(path, dst_dir / path.name)


def discover_sources_root(vault: Path) -> Path:
    markers = list(vault.glob(f"*/{SOURCES_MARKER}"))
    if len(markers) == 1:
        return markers[0].parent
    return vault / "06 - Sources"


def discover_output_root(sources_root: Path) -> Path:
    markers = list(sources_root.glob(f"*/{OUTPUT_MARKER}"))
    if len(markers) == 1:
        return markers[0].parent
    return sources_root / "001-input"


def ensure_topic_folders(output_root: Path) -> None:
    existing: set[str] = set()
    if output_root.exists():
        for marker in output_root.rglob(TOPIC_MARKER):
            try:
                existing.add(marker.read_text(encoding="utf-8").strip())
            except OSError:
                continue
    for topic_id, default_name in DEFAULT_FOLDERS.items():
        if topic_id in existing:
            continue
        folder = output_root / default_name
        folder.mkdir(parents=True, exist_ok=True)
        (folder / TOPIC_MARKER).write_text(topic_id + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault", required=True, help="Path to your Obsidian vault")
    parser.add_argument(
        "--codex-home",
        default=os.environ.get("CODEX_HOME", str(Path.home() / ".codex")),
        help="Codex home directory. Default: ~/.codex",
    )
    args = parser.parse_args()

    vault = Path(args.vault).expanduser().resolve()
    codex_home = Path(args.codex_home).expanduser().resolve()
    if not vault.exists():
        raise SystemExit(f"Vault path does not exist: {vault}")

    # Codex skills.
    skills_dst = codex_home / "skills"
    skills_dst.mkdir(parents=True, exist_ok=True)
    for skill in ("xhs-knowledge-capture", "web-knowledge-capture"):
        copytree(ROOT / "skills" / skill, skills_dst / skill)

    # Obsidian plugin.
    copytree(
        ROOT / "obsidian-plugin" / "xhs-auto-process",
        vault / ".obsidian" / "plugins" / "xhs-auto-process",
    )

    # Automation scripts and clipper templates.
    sources_root = discover_sources_root(vault)
    sources_root.mkdir(parents=True, exist_ok=True)
    (sources_root / SOURCES_MARKER).write_text(
        "This marker lets Obsidian Knowledge Capture follow the Sources root when it is renamed.\n",
        encoding="utf-8",
    )
    copy_files(ROOT / "automation", sources_root / "Automation")
    copy_files(ROOT / "web-clipper-templates", sources_root / "Templates")
    copytree(ROOT / "chrome-extension", sources_root / "Browser Extension" / "douyin-bridge")

    # Default inbox/material folders.
    (vault / "Clippings").mkdir(exist_ok=True)
    output_root = discover_output_root(sources_root)
    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / OUTPUT_MARKER).write_text(
        "This marker lets Obsidian Knowledge Capture follow the output folder when it is renamed.\n",
        encoding="utf-8",
    )
    ensure_topic_folders(output_root)

    print("Installed Obsidian Knowledge Capture.")
    print(f"Vault: {vault}")
    print(f"Codex skills: {skills_dst}")
    print()
    print("Next steps:")
    print("1. Restart Obsidian.")
    print("2. Enable community plugin: 统一来源知识自动沉淀.")
    print(f"3. Import {sources_root.relative_to(vault)}/Templates/unified-source.json in Obsidian Web Clipper.")
    print("4. Install Python dependencies if needed: python3 -m pip install -r requirements.txt")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
