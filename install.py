#!/usr/bin/env python3
"""Install Obsidian Knowledge Capture into a local Obsidian vault.

Usage:
  python3 install.py --vault "/path/to/your/Obsidian Vault"

This installer copies:
- Codex skills into ~/.codex/skills
- Obsidian plugin into <vault>/.obsidian/plugins/xhs-auto-process
- automation scripts into <vault>/06 - Sources/Automation
- Web Clipper templates into <vault>/06 - Sources/Templates
- default empty material folders into <vault>/06 - Sources/素材
"""

from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DEFAULT_FOLDERS = [
    "AI",
    "自媒体",
    "美食",
    "家居",
    "投资",
    "产品经理",
    "职场成长",
    "个人成长",
    "主账号",
    "待判断",
]


def copytree(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def copy_files(src_dir: Path, dst_dir: Path) -> None:
    dst_dir.mkdir(parents=True, exist_ok=True)
    for path in src_dir.iterdir():
        if path.is_file():
            shutil.copy2(path, dst_dir / path.name)


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
    copy_files(ROOT / "automation", vault / "06 - Sources" / "Automation")
    copy_files(ROOT / "web-clipper-templates", vault / "06 - Sources" / "Templates")

    # Default inbox/material folders.
    (vault / "Clippings").mkdir(exist_ok=True)
    for folder in DEFAULT_FOLDERS:
        (vault / "06 - Sources" / "素材" / folder).mkdir(parents=True, exist_ok=True)

    print("Installed Obsidian Knowledge Capture.")
    print(f"Vault: {vault}")
    print(f"Codex skills: {skills_dst}")
    print()
    print("Next steps:")
    print("1. Restart Obsidian.")
    print("2. Enable community plugin: 网页知识自动沉淀.")
    print("3. Import Web Clipper templates from your vault: 06 - Sources/Templates/")
    print("4. Install Python dependencies if needed: python3 -m pip install -r requirements.txt")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

