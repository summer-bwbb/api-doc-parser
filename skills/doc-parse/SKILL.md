---
name: doc-parse
description: Phase 3-5 of api-doc-parser — extract endpoint details from OpenAPI/Swagger by selected tag(s), generate Markdown and JSON output, and deliver via display mode (A) or file save mode (B). Reads selectedTags from shared state file.
---

# doc-parse — Phase 3-5: Endpoint Extraction and Output

Extract full endpoint details for selected API modules and generate dual-format output. This phase reads `sourcePath` and `selectedTags` from the shared state file and delegates the heavy lifting to a local Python script for performance.

## Pre-flight: Dependency Check

```bash
# Check jq >= 1.6
jq --version 2>/dev/null || { echo "ERROR: jq is not installed. Please install jq >= 1.6."; exit 1; }

# Check python3 (preferred; fallback to jq path if missing)
PYTHON_CMD=""
if command -v python3 >/dev/null 2>&1; then
  PYTHON_CMD=python3
elif command -v python >/dev/null 2>&1; then
  PYTHON_CMD=python
elif command -v py >/dev/null 2>&1; then
  PYTHON_CMD="py -3"
fi

if [ -z "$PYTHON_CMD" ]; then
  echo "WARNING: python3 not found. Falling back to jq-based v2 path."
  PYTHON_MISSING=1
fi

# Ensure UTF-8 output on Windows/Git Bash
export PYTHONIOENCODING=utf-8
```

## State File

Location (platform-appropriate):
- **Linux/macOS:** `/tmp/api-doc-parser/state.json`
- **Windows:** `/tmp/api-doc-parser/state.json` (Git Bash) or `%TEMP%\api-doc-parser\state.json`
- **Fallback:** `<project-root>/.api-doc-parser/state.json`

```bash
jq -r '.sourcePath' /tmp/api-doc-parser/state.json 2>/dev/null || echo ""
jq -r '.selectedTags[]' /tmp/api-doc-parser/state.json 2>/dev/null || echo ""
```

### Handle Missing State

- If `sourcePath` is missing: "No source document registered. Please run doc-fetch first."
- If `selectedTags` is missing or empty: "No modules selected. Please run doc-list first."

### Direct Parse (Bypass doc-list)

If the user provides a tag keyword directly:

1. Extract all tags: `jq -r '.tags[]?.name' <source-file>`
2. Fuzzy-match the keyword.
3. If single unambiguous match: set `selectedTags` and proceed.
4. Otherwise: fall back to `doc-list`.

## Phase 3-5: Delegate to parse.py

The core extraction, schema expansion, and formatting are handled by `skills/doc-parse/parse.py`. This avoids loading large OpenAPI JSON into the Agent context and replaces dozens of jq calls with a single script execution.

### Determine output mode

Priority:
1. CLI flags `-a` / `--display` → Mode A; `-b` / `--save` → Mode B
2. `state.json` field `outputMode`
3. Prompt user if neither is set

Persist selection to state.json:
```bash
jq '. + {outputMode: "B"}' /tmp/api-doc-parser/state.json > /tmp/api-doc-parser/state.json.tmp && mv /tmp/api-doc-parser/state.json.tmp /tmp/api-doc-parser/state.json
```

### Large module protection

Count endpoints per selected tag first:
```bash
jq --arg tag "TAG_NAME" -r '
  [.paths | to_entries[] | .value | to_entries[] |
   select(.value.tags? // [] | contains([$tag]))] | length
' <source-file>
```

If any tag has >30 endpoints and `--auto` is not set, show a summary and ask for confirmation.

### Run parse.py

```bash
$PYTHON_CMD skills/doc-parse/parse.py \
  --state /tmp/api-doc-parser/state.json \
  --output-dir api-doc-parser/.output \
  --mode B
```

Optional flags:
- `--auto` — Skip large-module confirmation.
- `--no-json` — Skip JSON output in mode B.
- `--no-md` — Skip Markdown output in mode B.

On Windows with `py` launcher:
```bash
PYTHONIOENCODING=utf-8 py -3 skills/doc-parse/parse.py \
  --state /tmp/api-doc-parser/state.json \
  --output-dir "api-doc-parser/.output" \
  --mode B
```

The script prints a machine-readable summary to stdout:
```
PARSE_COMPLETE
<tag>\t<count>\t<md_path>\t<json_path>
...
```

Warnings (e.g. large modules) go to stderr so they do not pollute the summary.

### Fallback when python3 is unavailable

If `python3` / `python` / `py` are all missing, use the original jq-based extraction path documented in the v2 archive. This preserves compatibility but does not provide the performance optimization.

## Phase 4: Output Generation

### Mode A: Direct Display

Run `parse.py --mode A` and stream its Markdown output into the conversation. Then display:

```
## Parse Complete

- **Source:** <sourceUrl>
- **Modules parsed:** <count>
- **Total endpoints:** <count>
- **Format:** Markdown (shown above)
```

### Mode B: File Persistence

Run `parse.py --mode B`. It writes files directly to `api-doc-parser/.output/`. Display:

```
## Parse Complete — Files Saved

- **Source:** <sourceUrl>
- **Modules parsed:** <count>
- **Total endpoints:** <count>

### Output Files

| File | Format | Size |
|------|--------|------|
| api-doc-parser/.output/<module>.md | Markdown | <size> |
| api-doc-parser/.output/<module>.json | JSON | <size> |
```

File sizes can be obtained from `wc -c <file>`.

## Context Overflow Prevention

1. **Never read raw OpenAPI JSON into Agent context.** `parse.py` reads it directly (and uses `orjson` when installed for faster loading).
2. **Schema expansion depth limit:** max 2 levels; beyond that show `→ SchemaName（递归上限，请查看 Swagger UI）`.
3. **Schema deduplication:** same schema resolved once and reused.
4. **Single schema field cap:** if a schema has >50 fields, show first 50 with a note.
5. **Optional temp file cleanup:**
   ```bash
   rm -f /tmp/api-doc.json /tmp/api-doc-parser/endpoints-raw.json
   ```

## Error Recovery

| Error | Recovery |
|-------|----------|
| No endpoints for module | Report: "No endpoints found for module [name]." Continue with remaining modules. |
| jq not available | For files ≤256KB: fall back to Read with offset/limit. For >256KB: report "jq required, please install jq >= 1.6." |
| python3 not available | Fall back to original jq-based v2 path. |
| State file missing | Prompt: "No source registered. Start with doc-fetch." |
| selectedTags empty | Prompt: "No modules selected. Run doc-list to select modules." |
