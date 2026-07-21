---
name: xhs-knowledge-capture
description: Clean and process Xiaohongshu (小红书/RED) Obsidian Web Clipper notes into durable, searchable knowledge cards, including image OCR and video download/transcription. Use when processing new Clippings, organizing Xiaohongshu saves, turning video speech into clean spoken scripts, classifying material for the main, food, or home account, connecting clips to existing notes, or generating content ideas.
---

# Xiaohongshu Knowledge Capture

Turn raw Web Clipper output into reusable knowledge. In unattended runs, use downloaded video and raw transcripts only as temporary working files; allow a deterministic watcher to remove them and the raw clip after full verification.

## Workflow

1. Locate the Obsidian vault and its `Clippings` folder.
2. Find requested clips, or scan for Xiaohongshu URLs whose `process-status` is absent or `待处理`.
3. Treat the raw clip as the source record during processing. Never delete it yourself during an unattended run.
4. Run `scripts/extract_clip.py <clip>` to canonicalize metadata and list unique note images.
5. Determine the media type:
   - Image post: use the Sources root discovered by the automation prompt and download only unique note images into `<sources-root>/assets/social/<note-id>/`; exclude avatars, comment images, recommendations, UI assets, and duplicate slides. Inspect every image and transcribe visible Chinese text in carousel order. Embed each retained image with a 700px Obsidian display width, for example `![[<sources-root>/assets/social/<note-id>/01.webp|700]]`; keep the original file unchanged.
   - Video post: run `scripts/download_transcribe_video.py <clip> <sources-root>/.automation/media/<note-id>`. Read the complete raw transcript. Create a cleaned spoken script that removes filler words (`嗯`, `啊`, `呃`), false starts, and meaningless repetition without changing claims, examples, sequence, or tone. Preserve the raw transcript file for verification.
6. If media download, OCR, or video transcription fails, set the raw clip to `process-status: 等待图片` or `process-status: 等待视频`, record the concrete failure, and stop. Do not mark the card complete.
7. Keep only insight-bearing comments. Exclude buttons, usernames without useful context, UI labels, counts, and loading text.
8. Read [references/schema.md](references/schema.md), select the account, topics, and one primary material folder, then create one knowledge card under the output root supplied by the automation prompt, defaulting to `06 - Sources/001-input/<primary-folder>/`. Use explicit numbered headings for both top-level and subsection headings, e.g. `## 二、知识提炼` and `### 2.1 核心观点`; do not rely on Obsidian automatic numbering. For video, put `## 五、清理后的口播稿` at the end of the card.
9. Search the vault for 2-5 genuinely related notes and add wiki links. Do not add weak links merely to fill the section.
10. Add `process-status: 已沉淀` and `knowledge-note: "[[...]]"` to the raw clip only after the knowledge card is successfully written and verified. Set the card itself to `status: 已沉淀`. In an unattended cleanup flow, omit `source-clip` from the permanent card because the raw clip will be deleted; retain the canonical `source` URL.

## Language handling

- When the complete caption, image text, or transcript is predominantly English, preserve the English and place a faithful Chinese translation immediately after each complete sentence or short semantic paragraph.
- Use paired blocks: English first, blank line, Chinese second. Segment by meaning, not subtitle timestamps or visual wrapping.
- Preserve names, URLs, code, product names, numbers, qualifications, examples, and sequence. Do not translate code or URLs.
- Set `language: [English, 中文]` and `translation-mode: bilingual-paired` in the finished card.
- Do not force bilingual pairing when the source is Chinese with occasional English terms.

## Account routing

- `主账号`: AI tools/workflows, product management, career growth, personal growth, or investing.
- `美食`: restaurants, recipes, ingredients, cooking, food products, or food shooting.
- `家居`: home products, organization, cleaning, renovation, spatial design, or smart home.
- `多账号`: only when the same source has a concrete reusable angle for at least two accounts.
- `待判断`: use when evidence is insufficient; do not force classification.

## Material folder routing

Store every completed card under the configured output root and one primary topic folder, defaulting to `06 - Sources/001-input/<primary-folder>/`. Platform stays in frontmatter as metadata; it should not decide the folder.

Choose exactly one primary folder for the file path:

The automation prompt may provide a mapping from stable topic IDs to user-renamed folder paths. When present, choose the semantic topic ID below and use its mapped path exactly; never recreate an older display name.

- `ai`: AI tools, AI workflow, AI coding, agents, prompt engineering, automation, model usage, AI product examples.
- `creator`: content strategy, account positioning, creator workflow, media PR, creator monetization, topic selection, publishing, community growth.
- `food`: restaurants, recipes, ingredients, cooking, food products, dining, food photography.
- `home`: home products, organization, cleaning, renovation, interior design, spatial design, smart home, home aesthetics.
- `investing`: investing, personal finance, asset allocation, financial markets, company/stock analysis.
- `product`: product management, product strategy, user research, requirements, roadmaps, growth product.
- `career`: workplace communication, career choices, job search, management, collaboration, productivity at work.
- `growth`: habits, learning, reading, time management, life systems, self-reflection, personal productivity.
- `main`: use only when the material is useful to the main account but does not clearly fit a more specific folder above.
- `unclassified`: use only when evidence is insufficient.

Also write the chosen primary folder into `topics` when appropriate, alongside more specific tags. Example: a YouTube file-management workflow for creators can be stored in `06 - Sources/001-input/自媒体/` if its main reusable value is creator workflow, or `06 - Sources/001-input/个人成长/` if its main reusable value is personal life organization.

## Quality rules

- Use the original tokenized URL for media download before replacing `source` with the canonical URL. Preserve it as `source-original` until processing finishes.
- Separate author caption, image OCR, useful comments, personal interpretation, and generated ideas.
- Store facts from the source separately from AI inference.
- Generate 3-8 ideas only when the clip supports them.
- Do not call a bookmark a knowledge card unless the image/body content was actually read.
- Never infer video content from the caption, comments, duration, thumbnail, or `blob:` element.
- Do not mark a video note complete unless the actual audio was transcribed and the cleaned spoken script is present.
- Never embed or permanently link the downloaded video in the knowledge card. Treat the video and raw transcript as disposable inputs; the permanent card keeps the source URL and cleaned spoken script.
- Preserve full-resolution source images on disk, but cap their inline Obsidian display width at 700px.

## Verification

- Confirm the raw clip still exists.
- Confirm the canonical source URL appears in the knowledge card. In unattended cleanup flows, confirm no `source-clip` wikilink is kept in the permanent card.
- Confirm retained images are unique and in carousel order.
- Confirm OCR covers every retained image.
- For video, confirm the local video, raw transcript, and cleaned spoken script all exist.
- Confirm the knowledge card has an account, topics, material types, summary, knowledge extraction, content creation ideas, source facts, and for video notes, a cleaned spoken script.
- Confirm a second run does not create a duplicate knowledge card.
- For predominantly English sources, confirm every substantive English block is immediately followed by its Chinese counterpart and the bilingual frontmatter is present.
