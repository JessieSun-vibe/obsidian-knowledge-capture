---
name: web-knowledge-capture
description: Process Obsidian Web Clipper notes from YouTube or general web pages into durable, searchable knowledge cards. Use when generic web clippings, YouTube transcripts, articles, blogs, documentation pages, product pages, or saved webpages should become structured Obsidian knowledge cards with numbered sections and source links.
---

# Web Knowledge Capture

Turn general Obsidian Web Clipper notes into reusable knowledge cards. Use only the text already saved in the raw clipping and any trusted local transcript provided by the deterministic Obsidian prefetch step; do not browse or download external media inside Codex during unattended automation.

## Workflow

1. Locate the Obsidian vault and its `Clippings` folder.
2. Find requested clips, or scan for notes whose `type` is `web-material` and whose `process-status` is `待处理`.
3. Treat the raw clip as the source record during processing. Never delete it yourself during an unattended run.
4. Read [references/schema.md](references/schema.md), classify the material, and create one knowledge card under `06 - Sources/素材/<primary-folder>/`.
5. If the note contains a transcript, time-coded video text, or the automation prompt reports a local transcript file, read the complete transcript and create `## 五、清理后的口播稿` by removing filler words, duplicated fragments, timestamps that do not add meaning, and obvious subtitle noise while preserving claims, examples, and sequence.
6. If the page is a normal article or webpage without transcript, omit `## 五、清理后的口播稿`.
7. Separate source facts from AI interpretation. Do not infer claims that are not supported by the captured text.
8. Search the vault for 2-5 genuinely related notes and add wiki links under `### 3.3 关联知识`. Do not add weak links just to fill the section.
9. Add `process-status: 已沉淀` and `knowledge-note: "[[...]]"` to the raw clip only after the knowledge card is written and verified. Set the card itself to `status: 已沉淀`.
10. In unattended cleanup flows, omit `source-clip` from the permanent card because the raw clip will be deleted; retain the canonical `source` URL.

## Account routing

- `主账号`: AI tools/workflows, product management, career growth, personal growth, investing, productivity, or general intellectual content.
- `美食`: restaurants, recipes, ingredients, cooking, food products, food shooting, or dining content.
- `家居`: home products, organization, cleaning, renovation, spatial design, smart home, or home aesthetics.
- `多账号`: only when the same source has a concrete reusable angle for at least two accounts.
- `待判断`: use when evidence is insufficient; do not force classification.

## Material folder routing

Store every completed card under `06 - Sources/素材/<primary-folder>/`, regardless of whether the source came from Xiaohongshu, YouTube, or a normal webpage. Platform stays in frontmatter as metadata; it should not decide the folder.

Choose exactly one primary folder for the file path:

- `AI`: AI tools, AI workflow, AI coding, agents, prompt engineering, automation, model usage, AI product examples.
- `自媒体`: content strategy, account positioning, creator workflow, media PR, creator monetization, topic selection, publishing, community growth.
- `美食`: restaurants, recipes, ingredients, cooking, food products, dining, food photography.
- `家居`: home products, organization, cleaning, renovation, interior design, spatial design, smart home, home aesthetics.
- `投资`: investing, personal finance, asset allocation, financial markets, company/stock analysis.
- `产品经理`: product management, product strategy, user research, requirements, roadmaps, growth product.
- `职场成长`: workplace communication, career choices, job search, management, collaboration, productivity at work.
- `个人成长`: habits, learning, reading, time management, life systems, self-reflection, personal productivity.
- `主账号`: use only when the material is useful to the main account but does not clearly fit a more specific folder above.
- `待判断`: use only when evidence is insufficient.

Also write the chosen primary folder into `topics` when appropriate, alongside more specific tags. Example: a YouTube file-management workflow for creators can be stored in `06 - Sources/素材/自媒体/` if its main reusable value is creator workflow, or `06 - Sources/素材/个人成长/` if its main reusable value is personal life organization.

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
- Confirm a second run does not create a duplicate knowledge card.
