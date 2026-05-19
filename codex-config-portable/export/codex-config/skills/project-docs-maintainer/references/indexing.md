# Indexing Patterns

Use progressive disclosure. Index files should guide, not duplicate.

## Root Index

Root `docs/README.md` should include:

- Repository documentation purpose.
- Project documentation entry table.
- Scope notes.
- Maintenance rules.

Do not link every deep document from root.

## Project Index

Project `docs/README.md` should include:

- Project identity in one paragraph.
- Recommended reading order.
- Four-category table.
- Existing source/legacy locations.
- Maintenance rules.

## Category Index

Category `README.md` should include:

```markdown
# <Project> <Type> 文档索引

One-sentence purpose.

| 文档 | 内容 | 状态 |
| --- | --- | --- |
| [doc](./doc.md) | Short purpose | active |
```

## Link Checks

Before finishing:

- Resolve links relative to the current Markdown file.
- Watch paths from nested category directories: `docs/system/README.md` often needs `../../` to reach project root.
- URL-encode spaces as `%20` in Markdown links.
- Prefer relative links over absolute local paths.
