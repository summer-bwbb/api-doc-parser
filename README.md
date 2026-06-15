# api-doc-parser

[![Agent Skill](https://img.shields.io/badge/Agent-Skill-6366f1)](SKILL.md)
[![OpenAPI](https://img.shields.io/badge/OpenAPI-3.x-6ba539)](https://spec.openapis.org/oas/v3.1.0)
[![Swagger](https://img.shields.io/badge/Swagger-2.0-85ea2d)](https://swagger.io/specification/v2/)

---

### Overview

**api-doc-parser** is an **Agent Skill** for parsing OpenAPI 3.x and Swagger 2.0 API documentation. It extracts endpoint details by module (tag), supports URL and local file input sources, and outputs Markdown (copy-paste ready) and JSON (machine-readable) formats.

The skill uses **jq pipelines** to pre-filter JSON at the shell layer, preventing large (100-500KB) OpenAPI documents from entering the Agent context.

### When to Use

Tell your AI coding agent:

| Request | What happens |
|---------|-------------|
| "Parse API docs from http://host/v3/api-docs" | Fetches URL, lists modules, asks for selection, outputs endpoints |
| "Extract endpoints for 飞行模块 from docs/api.json" | Parses local file, finds matching module, outputs endpoints |
| `/doc:parse` | Invokes the skill interactively |
| `/doc:help` | Displays usage instructions |

### Supported Sources

| Source | Format | Method |
|--------|--------|--------|
| Remote URL | OpenAPI 3.x / Swagger 2.0 JSON | `curl` → temp file → `jq` |
| Local file | `.json` | `jq` for files >256KB; direct read for small |
| Local file | `.md` | LLM extraction from markdown |
| Local file | `.txt` | LLM extraction from plain text |

### Output Formats

**Markdown** — human-readable tables with method, path, parameters, request body, responses. Copy-paste ready for documentation or communication.

**JSON** — structured, machine-readable. Includes meta (source, timestamp, OpenAPI version), module info, and full endpoint array. Cross-session referenceable.

### Output Modes

- **Mode A (Direct display):** Results shown in conversation. No files written. Good for quick lookups.
- **Mode B (File persistence):** Files saved to `api-doc-parser/.output/<module>.md` and `.json`. Good for cross-session reference.

### Module Selection

| Input | Example | Result |
|-------|---------|--------|
| By index | `1,3,6` | Modules at positions 1, 3, 6 |
| By keyword | `飞行,监控` | Fuzzy match against tag names |
| Mixed | `1,飞行` | Union of both, deduplicated |
| All | `all` or `全部` | All modules |

### Limitations (v1)

- `$ref` schema references are not expanded — only reference names are shown
- Non-OpenAPI format files (.md/.txt) rely on LLM extraction, which is less precise than structured parsing
- Requires `jq` and `curl` for optimal operation

### File Structure

```
api-doc-parser/
├── SKILL.md          ← Core skill logic (all platforms)
├── README.md         ← This file
├── metadata.json     ← Skill metadata
└── .output/          ← Parsed output (Mode B)
    ├── <module>.md
    └── <module>.json
```
