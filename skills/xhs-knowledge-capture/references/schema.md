# Knowledge card schema

Use this frontmatter:

```yaml
---
type: knowledge-card
platform: 小红书
account:
  - 主账号
topics:
  - 品牌营销
material-types:
  - 方法
  - 案例
status: 已沉淀
source:
source-clip: "[[raw clip name]]" # omit when an unattended watcher deletes the raw clip
author:
published:
collected-at:
---
```

Save the finished card at:

```text
06 - Sources/素材/<primary-folder>/<Title>.md
```

`<primary-folder>` is the strongest content theme, not the platform. Use `AI`, `自媒体`, `美食`, `家居`, `投资`, `产品经理`, `职场成长`, `个人成长`, `主账号`, or `待判断`.

Use these sections in order:

```markdown
# Title

## 一、一句话总结

## 二、知识提炼

### 2.1 核心观点

### 2.2 方法 / 流程

### 2.3 案例 / 数据

## 三、内容创作

### 3.1 可衍生选题

### 3.2 可复用素材

### 3.3 关联知识

## 四、来源内容

### 4.1 作者正文

### 4.2 图片原文（OCR）

### 4.3 有效评论

## 五、清理后的口播稿
```

Omit empty optional subsections. Do not add `used-in` to frontmatter. Number all subsection headings with their parent section number, such as `2.1`, `3.1`, and `4.1`; if an optional subsection is omitted, keep the remaining subsection numbers stable rather than renumbering concepts. Include `## 五、清理后的口播稿` only for video notes with a verified transcript.
