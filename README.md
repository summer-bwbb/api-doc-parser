# api-doc-parser

[![Agent Skill](https://img.shields.io/badge/Agent-Skill-6366f1)](SKILL.md)
[![OpenAPI](https://img.shields.io/badge/OpenAPI-3.x-6ba539)](https://spec.openapis.org/oas/v3.1.0)
[![Swagger](https://img.shields.io/badge/Swagger-2.0-85ea2d)](https://swagger.io/specification/v2/)
[![Version](https://img.shields.io/badge/version-0.0.2-blue)](metadata.json)
[![Platforms](https://img.shields.io/badge/platforms-9-8b5cf6)](docs/INSTALL.md)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![GitHub](https://img.shields.io/badge/GitHub-summer--bwbb/api--doc--parser-181717?logo=github)](https://github.com/summer-bwbb/api-doc-parser)

---

### Overview

**api-doc-parser** is an **Agent Skill** for parsing OpenAPI 3.x and Swagger 2.0 API documentation. It extracts endpoint details by module (tag), supports URL and local file input sources, and outputs Markdown (copy-paste ready) and JSON (machine-readable) formats.

The skill uses **jq pipelines** to pre-filter JSON at the shell layer, preventing large (100-500KB) OpenAPI documents from entering the Agent context.

**v2** introduces a sub-skill architecture with fine-grained slash commands (`/doc:fetch`, `/doc:list`, `/doc:parse`, `/doc:help`), 9-platform support, and 3 installation methods.

### Sub-skill Architecture

The pipeline is split into five sub-skills, each covering one phase:

| Sub-skill | Phase | Purpose | Slash Command |
|-----------|-------|---------|---------------|
| `doc-fetch` | Phase 1 | Source input -- fetch URL, validate local file, write state | `/doc:fetch <URL\|file>` |
| `doc-list` | Phase 2 | Module listing -- extract tags, display table, accept selection | `/doc:list [query]` |
| `doc-parse` | Phase 3-5 | Endpoint extraction + output generation (Markdown + JSON) | `/doc:parse [query] [-a\|-b]` |
| `doc-help` | Help | Display commands, formats, examples | `/doc:help` |
| `using-api-doc-parser` | Meta | Teaches the Agent how to discover and chain sub-skills | Injected at SessionStart |

The pipeline still works as a single natural-language request -- just say "Parse API docs from <URL>" and the agent will chain through all phases automatically.

### Installation

Choose one of three methods:

| Method | Command | Best For |
|--------|---------|----------|
| **Plugin** (Claude Code) | `claude plugins install api-doc-parser` | Claude Code users |
| **NPM** | `npm install -g api-doc-parser-skill` | Cross-platform, auto-updates |
| **Manual** | `git clone https://github.com/summer-bwbb/api-doc-parser.git && cp -r api-doc-parser/skills/* ~/.claude/skills/` | Custom setups, offline |

See [docs/INSTALL.md](docs/INSTALL.md) for detailed per-platform instructions.

### Command Reference

| Command | Purpose |
|---------|---------|
| `/doc:fetch <URL\|file>` | Fetch and validate API documentation source |
| `/doc:list [query]` | List modules and select which to parse |
| `/doc:parse [query] [-a\|-b]` | Extract endpoints and generate output (`-a` display, `-b` save files) |
| `/doc:help` | Show usage instructions and examples |

### Supported Sources

| Source | Format | Method |
|--------|--------|--------|
| Remote URL | OpenAPI 3.x / Swagger 2.0 JSON | `curl` -> temp file -> `jq` |
| Local file | `.json` | `jq` for files >256KB; direct read for small |
| Local file | `.md` | LLM extraction from markdown |
| Local file | `.txt` | LLM extraction from plain text |

### Output Formats

**Markdown** -- human-readable tables with method, path, parameters, request body, responses. Copy-paste ready for documentation or communication.

**JSON** -- structured, machine-readable. Includes meta (source, timestamp, OpenAPI version), module info, and full endpoint array. Cross-session referenceable.

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

### Supported Platforms

Nine AI coding platforms are supported. See [docs/INSTALL.md](docs/INSTALL.md) for setup per platform.

| Platform | Directory | Install Method |
|----------|-----------|---------------|
| Claude Code | `.claude-plugin/` | Plugin |
| Cursor | `.cursor-plugin/` | Manual |
| Codex | `.codex-plugin/` | Manual |
| Qoder | `.codex/` | Manual |
| OpenCode | `.opencode/` | Manual |
| Trae | `.trae/` | Manual |
| Kiwi | `.kimi/` | Manual |
| Gemini CLI | `.gemini/` | Manual |
| Copilot CLI | `.github/` | Manual |

### File Structure

```
api-doc-parser/
├── SKILL.md                          ← Core skill logic (v2 with sub-skill navigation)
├── README.md                         ← This file
├── AGENTS.md                         ← Agent entry point
├── GEMINI.md                         ← Gemini CLI entry point
├── metadata.json                     ← Skill metadata (v2.0.0)
├── package.json                      ← NPM package definition
├── gemini-extension.json             ← Gemini extension manifest
├── LICENSE                           ← MIT License
├── docs/                             ← Documentation
│   ├── INSTALL.md                    ← Per-platform installation guide
│   ├── USAGE.md                      ← Detailed usage guide
│   └── CHANGELOG.md                  ← Version history
├── skills/                           ← Sub-skills
│   ├── doc-fetch/SKILL.md            ← Phase 1: Source input
│   ├── doc-list/SKILL.md             ← Phase 2: Module listing
│   ├── doc-parse/SKILL.md            ← Phase 3-5: Endpoint extraction + output
│   ├── doc-help/SKILL.md             ← Help and usage info
│   └── using-api-doc-parser/SKILL.md ← Meta-instruction for Agent discovery
├── hooks/                            ← Plugin hooks
├── scripts/                          ← Utility scripts
├── .claude-plugin/                   ← Claude Code plugin manifest
├── .cursor-plugin/                   ← Cursor plugin manifest
├── .codex-plugin/                    ← Codex plugin manifest
├── .output/                          ← Parsed output (Mode B)
│   ├── <module>.md
│   └── <module>.json
└── [platform directories]            ← .cursor/, .codex/, .gemini/, etc.
```

### Limitations

- `$ref` schema references are not expanded -- only reference names are shown
- Non-OpenAPI format files (.md/.txt) rely on LLM extraction, which is less precise than structured parsing
- Requires `jq` and `curl` for optimal operation

### Documentation

- [Installation Guide](docs/INSTALL.md) -- Per-platform setup instructions
- [Usage Guide](docs/USAGE.md) -- Detailed usage with examples
- [Changelog](docs/CHANGELOG.md) -- Version history
