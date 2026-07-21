from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class InstallerTests(unittest.TestCase):
    def install(self, vault: Path, codex_home: Path) -> None:
        subprocess.run(
            [
                sys.executable,
                str(ROOT / "install.py"),
                "--vault",
                str(vault),
                "--codex-home",
                str(codex_home),
            ],
            check=True,
            capture_output=True,
            text=True,
        )

    def test_blank_install_and_renamed_upgrade(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            vault = root / "Test Vault"
            codex_home = root / "codex-home"
            (vault / ".obsidian").mkdir(parents=True)

            self.install(vault, codex_home)
            self.assertTrue(
                (vault / ".obsidian/plugins/xhs-auto-process/main.js").is_file()
            )
            self.assertTrue(
                (vault / "06 - Sources/Templates/unified-source.json").is_file()
            )
            self.assertTrue(
                (
                    vault
                    / "06 - Sources/Browser Extension/douyin-bridge/manifest.json"
                ).is_file()
            )
            custom_skill_file = (
                codex_home / "skills/xhs-knowledge-capture/user-notes.txt"
            )
            custom_skill_file.write_text("keep me\n", encoding="utf-8")

            sources = vault / "09-知识来源"
            (vault / "06 - Sources").rename(sources)
            output = sources / "006-素材"
            (sources / "001-input").rename(output)
            (output / "AI").rename(output / "人工智能")

            self.install(vault, codex_home)
            self.assertFalse((vault / "06 - Sources").exists())
            self.assertFalse((sources / "001-input").exists())
            self.assertFalse((output / "AI").exists())
            self.assertTrue(
                (output / "人工智能/.obsidian-knowledge-topic").is_file()
            )
            self.assertTrue((sources / "Templates/unified-source.json").is_file())
            self.assertEqual(
                custom_skill_file.read_text(encoding="utf-8"), "keep me\n"
            )


if __name__ == "__main__":
    unittest.main()
