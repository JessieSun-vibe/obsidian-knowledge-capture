# Obsidian Knowledge Capture

Turn Xiaohongshu, YouTube, and general web clippings into structured Obsidian knowledge cards with Codex skills.

This project installs:

- Obsidian Web Clipper templates
- an Obsidian local plugin that watches `Clippings/`
- Codex skills for Xiaohongshu and generic web / YouTube
- automation scripts that process raw clips into reusable material cards

It does not include the author's personal notes, clippings, transcripts, videos, logs, or knowledge cards.

## What it looks like after installation

Inside your own Obsidian vault:

```text
Clippings/
06 - Sources/
├── Automation/
├── Templates/
└── 素材/
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

The folders are empty defaults. Your own clips will be processed into your own cards.

## Requirements

- macOS recommended
- Obsidian
- Obsidian Web Clipper browser extension
- Codex / ChatGPT desktop app with Codex CLI available
- Python 3.10+ recommended

Optional dependencies for video/transcript workflows:

```bash
python3 -m pip install -r requirements.txt
```

## Install

1. Download or clone this repo.
2. Run:

```bash
python3 install.py --vault "/path/to/your/Obsidian Vault"
```

3. Restart Obsidian.
4. Enable the community plugin named `网页知识自动沉淀`.
5. Open Obsidian Web Clipper settings and import templates from:

```text
<your vault>/06 - Sources/Templates/
```

Import both:

- `xiaohongshu.json`
- `web-youtube.json`

## Daily usage

### Xiaohongshu

1. Open a Xiaohongshu note detail page.
2. Use the Web Clipper template `小红书｜知识收件箱`.
3. Add to Obsidian.
4. The plugin watches `Clippings/`, calls Codex, and creates a card under `06 - Sources/素材/<topic>/`.

### YouTube / Web

1. Open a YouTube video or webpage.
2. Use the Web Clipper template `通用网页｜知识收件箱`.
3. For YouTube, make sure the clipper preview includes transcript text.
4. Add to Obsidian.
5. The final card goes to `06 - Sources/素材/<topic>/`.

## Important boundaries

- If YouTube transcript is missing, the clip may stop at `等待内容`.
- If Xiaohongshu image download fails, the clip may stop at `等待图片`.
- If Xiaohongshu video download/transcription fails, the clip may stop at `等待视频`.
- The system avoids creating knowledge cards from title/description alone.

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

## Privacy

Do not publish your own:

- `Clippings/`
- `06 - Sources/素材/`
- `06 - Sources/.automation/`
- downloaded videos
- transcripts
- logs
