# Web knowledge card schema

Use this frontmatter:

```yaml
---
type: knowledge-card
platform:
account:
  - 主账号
topics:
  - AI 工具
material-types:
  - 方法
status: 已沉淀
source:
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

### 4.1 页面正文 / 作者观点

### 4.2 关键摘录

### 4.3 有效评论 / 补充信息

## 五、清理后的口播稿
```

Omit empty optional subsections. Keep subsection numbers stable when possible. Include `## 五、清理后的口播稿` only when the source includes a transcript or spoken-video text.
