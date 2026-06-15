---
name: doc-list
description: Phase 2 of api-doc-parser — extract API modules (tags) from an OpenAPI/Swagger document, display a numbered table with endpoint counts, and accept user selection via index, keyword, or mixed modes. Writes selectedTags to shared state file.
---

# doc-list — Phase 2: Module Listing

Extract all API modules (tags) from the OpenAPI document and present them for user selection. This is the second phase of the `api-doc-parser` pipeline. Reads from the shared state file (written by `doc-fetch`), and writes selected module names back to state for `doc-parse`.

## Pre-flight: Dependency Check

```bash
# Check jq >= 1.6
jq --version 2>/dev/null || { echo "ERROR: jq is not installed. Please install jq >= 1.6."; exit 1; }
```

## State File

Location (platform-appropriate):
- **Linux/macOS:** `/tmp/api-doc-parser/state.json`
- **Windows:** `/tmp/api-doc-parser/state.json` (Git Bash) or `%TEMP%\api-doc-parser\state.json`
- **Fallback:** `<project-root>/.api-doc-parser/state.json`

### Read Existing State

Read the state file to obtain `sourcePath`. **Priority:** `/tmp/api-doc-parser/state.json` first, fall back to `<project-root>/.api-doc-parser/state.json`.

```bash
STATE_FILE=""
if [ -f /tmp/api-doc-parser/state.json ]; then
  STATE_FILE="/tmp/api-doc-parser/state.json"
elif [ -f .api-doc-parser/state.json ]; then
  STATE_FILE=".api-doc-parser/state.json"
fi

if [ -z "$STATE_FILE" ]; then
  echo "ERROR: No state file found."
fi

jq -r '.sourcePath' "$STATE_FILE" 2>/dev/null || echo ""
```

If the state file is missing or `sourcePath` is empty:
- Prompt: "No source document registered. Please provide a URL or file path first (doc-fetch)."
- Do not proceed.

If `sourcePath` points to a file that no longer exists:
- Prompt: "Source file `<sourcePath>` no longer exists. Please re-fetch the source (doc-fetch)."

If the state file already has `selectedTags` populated:
- Report: "Previously selected modules: `<tags>`. Would you like to re-select or proceed with these?"

---

## Phase 2a: Extract Tags (Modules)

### Extract tag names and descriptions

```bash
jq -r '.tags[]? | "\(.name)|||\(.description // "(no description)")"' <source-file>
```

**CRITICAL:** Never read the full JSON file. jq extracts only tag names and descriptions -- typically <500 bytes total.

### Count endpoints per tag

```bash
jq -r '[.paths | to_entries[] | .value | to_entries[]? | .value.tags[]?] | group_by(.) | .[] | "\(.[0]):\(length)"' <source-file>
```

### Validate tags exist

If `jq -r '.tags[]?.name' <source-file>` returns empty:

1. Check if the document uses Swagger 2.0 format:
   ```bash
   jq -r '.swagger // ""' <source-file>
   ```
   If the output starts with `"2.0"`, tags may be missing entirely.

2. **Swagger 2.0 fallback:** Extract unique tags from path operations:
   ```bash
   jq -r '[.paths | to_entries[] | .value | to_entries[]? | .value.tags[]?] | unique | .[]' <source-file>
   ```

3. If still no tags: assign all paths to a synthetic "_default" module.
   ```
   No tags found in document. All endpoints will be grouped under "_default" module.
   ```

---

## Phase 2b: Display Module List

Present the modules in a numbered table:

```
## API Modules Found

| # | Module (tag) | Description | Endpoints |
|---|-------------|-------------|-----------|
| 1 | 飞行计划    | Flight plan management | 12 |
| 2 | 飞行监控    | Real-time flight monitoring | 8 |
| 3 | 系统管理    | System administration | 5 |
| ...                                          |

**How to select:**
- By index: `1,3,6`
- By keyword: `飞行,监控`
- Mix: `1,飞行,6`
- All: `all` or `全部`
```

### Pagination for >50 tags

If more than 50 tags exist, display 20 per page:

```
## API Modules Found (Page 1/3)

| # | Module (tag) | Description | Endpoints |
|---|-------------|-------------|-----------|
| 1 | tag1       | desc1       | 5  |
| ...                                        |

Showing 1-20 of 57 modules. Commands: `n` (next page), `p` (previous), or enter selection now.
```

Wait for user input. Navigate pages if requested, then accept selection.

---

## Phase 2c: Parse User Selection

Wait for user input, then parse using the following strategy:

```
User input → Parse strategy:
  "1,3,6"     → indices → map to tags[0], tags[2], tags[5] (1-indexed)
  "飞行,监控"  → keywords → fuzzy match (case-insensitive, substring) against tag names
  "1,飞行"    → mixed → resolve indices first, then keywords, deduplicate by tag name
  "all"/"全部" → select all modules
```

### Fuzzy Matching Rules

1. **Exact match** (case-insensitive) — highest priority. A keyword matching a tag name exactly.
2. **Substring match** (e.g., "计划" matches "飞行计划") — if no exact match found.
3. **Multiple candidates** — if more than one tag matches a keyword, display all candidates and let the user pick:
   ```
   Keyword "飞行" matches multiple modules:
   | # | Module |
   |---|--------|
   | 1 | 飞行计划 |
   | 2 | 飞行监控 |
   
   Enter indices to select (comma-separated), or "all" for all matches:
   ```
4. **No matches** — report and re-prompt:
   ```
   No module matching '<keyword>'. Available modules: <list>. Please try again.
   ```

### Index Validation

- Indices are 1-indexed (first module = 1).
- Validate that each index is within range 1 to N.
- Report out-of-range indices:
  ```
  Index #<N> out of range (1–<max>). Please re-enter.
  ```

### Deduplication

After resolving all indices and keywords, deduplicate by tag name. If the deduplicated count differs from the original selection count, report:

```
Resolved <N> selections, deduplicated to <M> unique modules.
```

---

## Phase 2d: Large Module Warning

Count endpoints for each selected module. If any selected module has >30 endpoints:

```
⚠️ Module "通用接口" has 42 endpoints — too many for full detail display.

Summary:
| Method | Path | Summary |
|--------|------|---------|
| GET | /api/common/users | Get user list |
| POST | /api/common/users | Create user |
| ... (42 total) |

Full parse may consume significant context. Continue with full detail, or select a subset?
```

Generate the summary by:
```bash
jq --arg tag "TAG_NAME" -r '
  .paths | to_entries[] | .key as $path |
  .value | to_entries[] | select(.value.tags? // [] | contains([$tag])) |
  "| \(.key | ascii_upcase) | \($path) | \(.value.summary // "(no summary)") |"
' <source-file>
```

Wait for user confirmation before proceeding. Options:
- "full" / "all" — proceed with all endpoints
- Index selection — select a subset of endpoints
- "skip" — remove this module from selection

---

## Phase 2e: Update State File

After valid selection, update the state file with `selectedTags`:

Read existing state, merge in `selectedTags`, write back.

```bash
# Read current state, add selectedTags, write back
jq --argjson tags '["tag1","tag2"]' '. + {selectedTags: $tags}' /tmp/api-doc-parser/state.json > /tmp/api-doc-parser/state.json.tmp && mv /tmp/api-doc-parser/state.json.tmp /tmp/api-doc-parser/state.json
```

### Updated State Example

```json
{
  "sourcePath": "/tmp/api-doc.json",
  "sourceType": "url",
  "sourceUrl": "https://petstore3.swagger.io/api/v3/openapi.json",
  "openapiVersion": "3.0.3",
  "fetchedAt": "2026-06-15T10:30:00Z",
  "selectedTags": ["pet", "store"]
}
```

---

## Completion

After updating state, report:

```
Selected modules: <count>
  - <tag1> (<N> endpoints)
  - <tag2> (<M> endpoints)

Proceeding to endpoint extraction (doc-parse)...
```

Then immediately invoke `doc-parse` to continue the pipeline.

## Context Overflow Prevention

- **Never read raw OpenAPI JSON into Agent context.** All extraction uses jq pipelines.
- **Tag extraction is a single jq query** producing at most a few hundred bytes.
- **Endpoint counting is a single jq query** producing at most a few hundred bytes.
- **Large module summary** uses jq with method/path/summary only -- no parameter or schema details.
