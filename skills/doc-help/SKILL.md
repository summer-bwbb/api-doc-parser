---
name: doc-help
description: Display help and usage information for the api-doc-parser skill suite. Use when the user types /doc:help, asks "how do I use this", or needs guidance on commands, input formats, or output modes.
---

# doc-help — Help and Usage

Display usage instructions for the `api-doc-parser` skill suite. This skill is informational only -- it does not modify state or produce output files.

## Supported Commands

| Command | Description |
|---------|-------------|
| `/doc:parse` | Full pipeline: provide URL or file, select modules, generate output |
| `/doc:help` | Display this help information |

## Sub-skills (invoked automatically)

The parser runs as a 3-phase pipeline of specialized sub-skills:

| Sub-skill | Invocation | Purpose |
|-----------|-----------|---------|
| `doc-fetch` | Automatic (Phase 1) | Fetch and validate source document |
| `doc-list` | Automatic (Phase 2) | List and select API modules |
| `doc-parse` | Automatic (Phase 3) | Extract endpoints and generate output |

The meta-skill `using-api-doc-parser` orchestrates these automatically. You do not need to invoke sub-skills manually.

## Input Formats

| Format | Examples | Notes |
|--------|----------|-------|
| Remote URL (OpenAPI JSON) | `https://example.com/v3/api-docs` | Fetched via curl; must return valid JSON |
| Local JSON file | `./api-docs/openapi.json` | OpenAPI 3.x or Swagger 2.0 |
| Local Markdown file | `./docs/api-reference.md` | Best-effort LLM extraction |
| Local Text file | `./docs/endpoints.txt` | Best-effort LLM extraction |

## Output Formats

| Format | Description | File Extension |
|--------|-------------|---------------|
| Markdown | Human-readable, copy-paste ready tables | `.md` |
| JSON | Structured, machine-readable, cross-session referenceable | `.json` |

Both formats are generated together. JSON files include meta (source, timestamp, version), module info, endpoint count, and structured endpoint arrays.

## Output Modes

| Mode | Behavior | When to Use |
|------|----------|-------------|
| **A** (Display) | Output directly in conversation, no files written | Quick lookup, one-time reference |
| **B** (Save) | Write `.md` and `.json` files to `api-doc-parser/.output/` | Cross-session reference, sharing with team |

Mode is prompted on first run and persisted in state. Subsequent runs reuse the same mode. Override with `-a` (display) or `-b` (save) in your request.

## Module Selection

When listing modules, you can select by:

- **Index:** `1,3,6` — selects modules at positions 1, 3, and 6
- **Keyword:** `飞行,监控` — fuzzy-matches tag names (case-insensitive, substring)
- **Mixed:** `1,飞行,6` — indices first, then keywords, deduplicated
- **All:** `all` or `全部` — selects every module

## Example Usage

### Full pipeline with URL

```
User: /doc:parse https://petstore3.swagger.io/api/v3/openapi.json

Agent:
  → Fetches and validates the document
  → Displays module list with endpoint counts
  → User selects: "1,3"
  → Extracts endpoints for selected modules
  → Output mode prompt → User selects "B"
  → Saves .md and .json files
```

### Direct keyword parse

```
User: Parse the 飞行计划 module

Agent (if source already registered):
  → Matches "飞行计划" to tag
  → Extracts endpoints for that module
  → Outputs in previously selected mode
```

### Local file

```
User: /doc:parse ./my-project/api-docs.json

Agent:
  → Validates file, checks size
  → Displays module list
  → User selects: "all"
  → Generates output for all modules
```

## Output File Structure

```
api-doc-parser/.output/
├── 飞行计划.md          ← Markdown: module header + endpoint tables
├── 飞行计划.json        ← JSON: structured endpoint data
├── 飞行监控.md
└── 飞行监控.json
```

## Dependencies

- `jq` >= 1.6 (required for JSON filtering)
- `curl` >= 7.0 (required for URL fetching)

## Limitations (v1)

- `$ref` schema references are recorded by name only, not expanded
- `.md` and `.txt` input is best-effort (LLM extraction from unstructured text)
- Large modules (>30 endpoints) require explicit confirmation before full extraction
- Large JSON files (>256KB) require jq; cannot be read directly into context
