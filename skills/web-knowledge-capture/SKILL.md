---
name: web-knowledge-capture
description: Process unified Obsidian Web Clipper source notes from X, WeChat, Zhihu, Weibo, Instagram, Douyin, YouTube, or general web pages into durable, searchable knowledge cards. Use when social posts, video transcripts, articles, blogs, documentation, product pages, or saved webpages should become automatically classified Obsidian knowledge cards with bilingual English-Chinese source text when required.
---

# Web Knowledge Capture

Turn unified Obsidian Web Clipper notes into reusable knowledge cards. Prefer text saved in the raw clipping and trusted local transcripts provided by the deterministic prefetch step. During unattended automation, use a configured Wigolo MCP fetch only as a fallback for an insufficient ordinary webpage or social-post body; do not perform general web search or download external video inside Codex.

## Workflow

1. Locate the Obsidian vault and its `Clippings` folder.
2. Find requested clips, or scan for notes whose `type` is `source-material` or legacy `web-material` and whose `process-status` is `待处理`.
3. Treat the raw clip as the source record during processing. Never delete it yourself during an unattended run.
4. Check whether the captured body is sufficient. When it is insufficient and a `wigolo` MCP fetch tool is configured, fetch the canonical `source` URL once and use the returned page text and metadata as supplemental source material. If the tool is absent, fails, or still returns insufficient content, set `process-status: 等待内容`, record the concrete reason, and stop.
5. Read [references/schema.md](references/schema.md), classify the material, and create one knowledge card under the output root supplied by the automation prompt, defaulting to `06 - Sources/001-input/<primary-folder>/`.
6. If the note contains a transcript, time-coded video text, or the automation prompt reports a local transcript file, read the complete transcript and create `## 五、清理后的口播稿` by removing filler words, duplicated fragments, timestamps that do not add meaning, and obvious subtitle noise while preserving claims, examples, and sequence.
7. If the page is a normal article or webpage without transcript, omit `## 五、清理后的口播稿`.
8. Separate source facts from AI interpretation. Do not infer claims that are not supported by the captured or Wigolo-fetched text.
9. Search the vault for 2-5 genuinely related notes and add wiki links under `### 3.3 关联知识`. Do not add weak links just to fill the section.
10. Add `process-status: 已沉淀` and `knowledge-note: "[[...]]"` to the raw clip only after the knowledge card is written and verified. Set the card itself to `status: 已沉淀`.
11. In unattended cleanup flows, omit `source-clip` from the permanent card because the raw clip will be deleted; retain the canonical `source` URL.

## Language handling

- Detect the language from the substantive source body or complete transcript, not navigation, metadata, or isolated product names.
- When the substantive source is predominantly English, preserve all meaning-bearing English source content and place a faithful Chinese translation immediately after each complete sentence or short semantic paragraph.
- Use paired blocks: English first, blank line, Chinese second. Do not collect the complete English text and complete Chinese translation into separate sections.
- Segment transcripts by complete meaning rather than subtitle timestamps or visual line wrapping.
- Preserve names, URLs, code, commands, model names, product names, numbers, and factual qualifications. Do not translate code or URLs.
- Set `language: [English, 中文]` and `translation-mode: bilingual-paired` in the finished card.
- When the source is Chinese with occasional English terminology, keep the terminology in place and do not create redundant bilingual pairs.

## Account routing

- `主账号`: AI tools/workflows, product management, career growth, personal growth, investing, productivity, or general intellectual content.
- `美食`: restaurants, recipes, ingredients, cooking, food products, food shooting, or dining content.
- `家居`: home products, organization, cleaning, renovation, spatial design, smart home, or home aesthetics.
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

- Use explicit numbered headings for both top-level and subsection headings, e.g. `## 二、知识提炼` and `### 2.1 核心观点`.
- Do not add `used-in` to frontmatter.
- Keep the source URL in frontmatter.
- Do not call a bookmark a knowledge card unless the page body or transcript was actually read.
- For YouTube transcript notes, preserve the speaker's meaning while making the spoken script readable.
- If a local transcript path is reported, read that file before deciding the clipping lacks content.
- For ordinary webpages, extract the reusable ideas, methods, examples, and content angles from the captured body.
- If the raw clipping has too little captured body to support a knowledge card, set `process-status: 等待内容`, record the reason in the raw clip, and stop.

## Verification

- Confirm the raw clip still exists.
- Confirm the card has `status: 已沉淀` and a `source` URL.
- Confirm the card follows [references/schema.md](references/schema.md).
- Confirm transcript-based cards include `## 五、清理后的口播稿`; ordinary webpages omit it.
- For predominantly English sources, confirm every substantive English block is immediately followed by its Chinese counterpart and the bilingual frontmatter is present.
- Confirm a second run does not create a duplicate knowledge card.
