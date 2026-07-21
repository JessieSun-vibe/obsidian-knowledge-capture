# Obsidian Knowledge Capture

Turn X, WeChat, Zhihu, Weibo, Xiaohongshu, Instagram, Douyin, YouTube, and general web clippings into structured Obsidian knowledge cards with one capture template and Codex skills.

This project installs:

- Obsidian Web Clipper templates
- a minimal Chrome helper for automatic Douyin media capture
- an Obsidian local plugin that watches `Clippings/`
- automatic platform and content-type detection
- Codex skills for social images, video transcripts, and general web content
- automation scripts that process raw clips into reusable material cards

Your daily action is always the same: choose `统一来源｜知识收件箱` in Obsidian Web Clipper and save. The local Obsidian plugin handles the rest automatically.

It does not include the author's personal notes, clippings, transcripts, videos, logs, or knowledge cards.

## What it looks like after installation

Inside your own Obsidian vault:

```text
Clippings/
06 - Sources/
├── Automation/
├── Templates/
└── 001-input/
    ├── AI/
    ├── 自媒体/
    ├── 美食/
    ├── 家居/
    ├── 投资/
    ├── 产品经理/
    ├── 职场成长/
    ├── 个人成长/
    ├── 主账号/
    └── 待判断/
.obsidian/
└── plugins/
    └── xhs-auto-process/
```

`06 - Sources` is only the initial display name. The installer adds a hidden `.obsidian-knowledge-sources` marker, so the whole folder can later be renamed in Obsidian without breaking the plugin or automation.

The folders are empty defaults. Your own clips will be processed into your own cards.

## Requirements

- macOS recommended; the core webpage workflow can run on Linux and Windows when Codex and Python are available
- Obsidian
- Obsidian Web Clipper browser extension
- Codex / ChatGPT desktop app with Codex CLI available
- Python 3.10+ recommended

Optional dependencies for video/transcript workflows:

```bash
python3 -m pip install -r requirements.txt
```

The bundled local transcription path uses `mlx-whisper` and currently targets Apple Silicon Macs. Other platforms can still process captured text and existing transcripts, but need a replacement transcription backend for audio-only videos.

Optional local webpage fallback:

```bash
npx wigolo init --non-interactive --agents=codex
```

When Wigolo is registered as a Codex MCP server, the automation can use it once to supplement an ordinary webpage or social post whose Web Clipper body is insufficient. The workflow still works without Wigolo and preserves incomplete clips for retry.

## Install

1. Download or clone this repo.

```bash
git clone https://github.com/JessieSun-vibe/obsidian-knowledge-capture.git
cd obsidian-knowledge-capture
```

2. Run:

```bash
python3 install.py --vault "/path/to/your/Obsidian Vault"
```

3. Restart Obsidian.
4. Enable the community plugin named `统一来源知识自动沉淀`.
5. Until the Douyin helper is published in the Chrome Web Store, open `chrome://extensions`, enable Developer mode, choose **Load unpacked**, and select:

```text
<your vault>/06 - Sources/Browser Extension/douyin-bridge/
```

The helper only runs on `www.douyin.com`. It does not request the Chrome cookies permission and does not read or export login cookies.

6. Open Obsidian Web Clipper settings and import templates from:

```text
<your vault>/06 - Sources/Templates/
```

Import:

- `unified-source.json` (recommended default)

The following legacy templates remain available as fallbacks for existing installations:

- `xiaohongshu.json`
- `web-youtube.json`

## Daily usage

1. Open a supported social post, video, article, or webpage.
2. Use the Web Clipper template `统一来源｜知识收件箱`.
3. Add to Obsidian.
4. The plugin watches `Clippings/`, detects the platform, and calls the appropriate Codex skill.
5. The final card is written directly to `06 - Sources/001-input/<topic>/`.
6. The raw clipping is deleted only after the final card passes deterministic verification.

Supported routing includes:

| Source | Automatic handling |
| --- | --- |
| X / WeChat / Zhihu / Weibo / general web | Captured body and metadata |
| Xiaohongshu images | Caption, filtered carousel images, OCR |
| Xiaohongshu video | Download, local transcription, cleaned spoken script |
| YouTube | Existing transcript, transcript API, or local transcription fallback |
| Douyin / Instagram Reels | Video download and local transcription when supported by `yt-dlp` |

Sites that require login or present anti-bot challenges may still need a valid browser session or a richer clip. The workflow preserves failed raw clips instead of inventing missing content.

Retained Xiaohongshu images keep their original files for later reuse. Knowledge cards embed them at a default width of 700px so large vertical images remain readable without dominating the note.

## English sources

When the substantive source or transcript is predominantly English, the finished card preserves the English and places a Chinese translation immediately below each complete sentence or short semantic paragraph:

```text
Hello, how are you?

你好，你怎么样？
```

Chinese sources that only contain occasional English product names or terminology are not redundantly translated.

## Important boundaries

- If YouTube transcript is missing, the clip may stop at `等待内容`.
- If Xiaohongshu image download fails, the clip may stop at `等待图片`.
- If Xiaohongshu video download/transcription fails, the clip may stop at `等待视频`.
- The system avoids creating knowledge cards from title/description alone.
- Login-gated platforms can fail when the browser has no usable session.
- Platform support means the workflow knows how to route the source; it does not guarantee that every private or anti-bot page can always be downloaded.

## Configuration

The processor finds `codex` on `PATH`, then falls back to the ChatGPT desktop app location on macOS. Override it when necessary:

```bash
export CODEX_BIN="/absolute/path/to/codex"
```

The Obsidian plugin uses `python3` (`python` on Windows). Override it before starting Obsidian when necessary:

```bash
export OBSIDIAN_KNOWLEDGE_PYTHON="/absolute/path/to/python3"
```

The automation uses the current vault as `OBSIDIAN_VAULT` by default and `~/.codex` as `CODEX_HOME`; both can be overridden with environment variables.

The knowledge-card output root initially defaults to `06 - Sources/001-input`. The Sources root has a `.obsidian-knowledge-sources` marker, and the output root has a `.obsidian-knowledge-output` marker. Rename either folder in Obsidian and the markers move with it, allowing the plugin and automation to discover the current paths automatically.

Each topic folder also contains a hidden `.obsidian-knowledge-topic` marker with a stable semantic ID. You can rename `AI` to `人工智能`, `ai`, or another display name in Obsidian; the marker follows the folder and future cards continue routing to it. Upgrades discover existing markers and do not recreate the old default names.

For an explicit override, set one environment variable before starting Obsidian:

```bash
export OBSIDIAN_KNOWLEDGE_OUTPUT="06 - Sources/your-new-folder-name"
```

You can also explicitly override the Sources root:

```bash
export OBSIDIAN_KNOWLEDGE_SOURCES="your-renamed-sources-folder"
```

Legacy cards under `06 - Sources/素材` and `06 - Sources/Knowledge` remain valid and are still recognized by the completion verifier.

## Customizing material folders

The default folders are:

```text
AI
自媒体
美食
家居
投资
产品经理
职场成长
个人成长
主账号
待判断
```

You can edit the routing rules in:

```text
~/.codex/skills/xhs-knowledge-capture/SKILL.md
~/.codex/skills/web-knowledge-capture/SKILL.md
```

## Safety and cleanup

- The Codex skill never deletes the raw clipping.
- The deterministic watcher verifies the final card has `status: 已沉淀`, a valid source URL, and a unique linked card before deleting the raw clipping.
- Failed image, video, transcript, or content extraction leaves the clipping in place with a waiting or failure status.

## Privacy

Do not publish your own:

- `Clippings/`
- `06 - Sources/001-input/`
- `06 - Sources/.automation/`
- downloaded videos
- transcripts
- logs

## License

MIT. See [LICENSE](LICENSE).
