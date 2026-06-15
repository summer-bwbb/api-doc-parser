---
name: api-doc-parser
description: Parse OpenAPI 3.x / Swagger 2.0 API documentation. Extract endpoint details by module (tag), output Markdown + JSON. Supports URL fetch (curl) and local file (.json/.md/.txt) import. Use when user asks to "parse API docs", "extract endpoints from Swagger", "list API modules", "find API endpoints by module", or references an OpenAPI/Swagger document URL or file.
---

# API Doc Parser

Parse OpenAPI 3.x and Swagger 2.0 API documentation by module. Extract full endpoint details with context overflow protection. Dual-format output: Markdown (copy-paste ready) and JSON (cross-session referenceable).

**CRITICAL — Context overflow prevention:** Never read the raw OpenAPI JSON file into the Agent context. Always use jq in the shell layer to pre-filter. The full JSON stays in temp files; only filtered results enter context.

## Phase 1: Source Input

### Detect input type

Ask the user for the API documentation source. If a URL or file path was already provided, use it directly.

| Input | Detection | Action |
|-------|-----------|--------|
| URL | Starts with `http://` or `https://` | Fetch via curl → `/tmp/api-doc.json` |
| Local `.json` file | Path ends in `.json` | Use directly with jq |
| Local `.md` file | Path ends in `.md` | Read with offset/limit pagination, LLM extract |
| Local `.txt` file | Path ends in `.txt` | Read with offset/limit pagination, LLM extract |

### URL source

```bash
# Step 1: Check connectivity and Content-Type
curl -s -I -o /dev/null -w "%{http_code}" "<URL>"
# If non-200, report error and offer retry or fallback to local file

# Step 2: Fetch and save to temp file (never display raw content)
curl -s "<URL>" -o /tmp/api-doc.json

# Step 3: Validate it's JSON
jq 'type' /tmp/api-doc.json
# Expected: "object". If not, report "Not a valid JSON document"
```

If curl fails (non-200, timeout, DNS error):
- Report: "Unable to fetch URL: <URL>. Error: <details>"
- Offer: "Would you like to retry, or provide a local file path instead?"

### Local JSON file

Check file size first:
```bash
wc -c < "<filepath>"
```
- If ≤ 262144 bytes (256KB): Can read with offset/limit if needed, but prioritize jq filtering
- If > 256KB: MUST use jq. Never use Read on the file.

### Local .md / .txt file

Read the file in paginated chunks using Read with `offset` and `limit`. Use LLM extraction to identify API endpoints, methods, parameters, and responses from the unstructured text. This path is best-effort — structured JSON input is always preferred.

**Phase 1 output:** The temp file path or confirmed local path for further processing.

## Phase 2: Module Listing

### Extract tags (modules) using jq

```bash
# Extract all unique tags from the OpenAPI document
# Never read the full JSON — jq outputs only tag names and descriptions
jq -r '.tags[]? | "\(.name)|||\(.description // "(no description)")"' <source-file>
```

Also count endpoints per tag:

```bash
# Count paths per tag
jq -r '[.paths | to_entries[] | .value | to_entries[]? | .value.tags[]?] | group_by(.) | .[] | "\(.[0]):\(length)"' <source-file>
```

### Display module list to user

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

### Validate tags exist

If `jq -r '.tags[]?.name'` returns empty:
- Check if the document uses Swagger 2.0 format (`swagger: "2.0"`)
- For Swagger 2.0: the tags may be missing entirely — fall back to listing all unique tags from path operations
- If no path operations have tags either, assign all paths to a synthetic "_default" module

### Accept and parse user selection

Wait for user input, then parse:

```
User input → Parse strategy:
  "1,3,6"     → indices → map to tags[0], tags[2], tags[5]
  "飞行,监控"  → keywords → fuzzy match (case-insensitive, substring) against tag names
  "1,飞行"    → mixed → resolve indices first, then keywords, deduplicate by tag name
  "all"/"全部" → select all modules
```

**Fuzzy matching rules:**
1. Exact match (case-insensitive) — highest priority
2. Substring match (e.g., "计划" matches "飞行计划")
3. Multiple matches → display all candidates, let user pick
4. No matches → report "No module matching '<keyword>'. Available modules: <list>. Please try again."

**Deduplication:** After resolving all indices and keywords, deduplicate by tag name. Report original count → deduplicated count if different.

### Large module warning

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

Wait for user confirmation before proceeding.

**Phase 2 output:** A list of validated tag names to parse, stored as shell variables for Phase 3.

## Phase 3: Endpoint Extraction

### Filter paths by selected tags

For each selected tag name, filter the OpenAPI paths using jq. Build a jq filter that includes only paths where at least one operation has the target tag.

```bash
# Build the tag filter for jq
# TAG_NAME is one of the selected modules
jq --arg tag "$TAG_NAME" '
  .paths | to_entries | map(
    select(.value | to_entries | .[].value.tags? // [] | contains([$tag]))
  ) | from_entries
' <source-file>
```

### Extract endpoint details with a single jq query

For the filtered paths, extract all required fields in one jq query. This query runs entirely in shell — only the structured result enters Agent context.

```bash
jq --arg tag "$TAG_NAME" -r '
  .paths | to_entries | map(
    select(.value | to_entries | .[].value.tags? // [] | contains([$tag]))
  ) | .[] | .key as $path |
  .value | to_entries[] |
  "===ENDPOINT===",
  "path:\($path)",
  "method:\(.key)",
  "summary:\(.value.summary // "(no summary)")",
  "description:\(.value.description // "(no description)")",
  "operationId:\(.value.operationId // "(no operationId)")",
  "parameters:\(.value.parameters // [] | tojson)",
  "requestBody:\(.value.requestBody // {} | tojson)",
  "responses:\(.value.responses // {} | tojson)"
' <source-file>
```

### Parse the jq output

The `===ENDPOINT===` delimiter separates endpoints. For each endpoint block:

**Parameters:** Parse the JSON array and extract:
- `name` — parameter name
- `in` — location (query, path, header, cookie)
- `description` — human-readable description
- `required` — boolean
- `schema.type` — data type
- `schema.default` — default value if present

**Request body:** If present and non-empty:
- `required` — boolean
- For each content type: `schema.$ref` — record the reference name only

**Responses:** For each status code:
- `description` — human-readable description
- For each content type: `schema.$ref` — record the reference name only

**$ref handling (v1):** Only record the reference name (the last segment after `/`). Do NOT expand into `components/schemas`. Display as: `→ ResultDTOOdmTaskListResponse`. The user can look up the schema in Swagger UI.

### Empty module handling

If the filtered paths object is empty after jq filtering:
```
No endpoints found for module "<tag name>".
```
Continue processing remaining selected modules.

**Phase 3 output:** A structured list of endpoints per module, ready for formatting.

## Phase 4: Output Generation

### Format A: Markdown (human-readable)

For each module, generate the following Markdown structure:

```markdown
# <Module Name>

> <Module Description>

**Endpoints:** <count>

---

## <METHOD> <PATH> — <Summary>

**Description:** <Description>

**Operation ID:** `<operationId>`

### Request Parameters

| Name | In | Type | Required | Default | Description |
|------|----|------|----------|---------|-------------|
| userId | query | string | Yes | — | User unique identifier |
| page | query | integer | No | 1 | Page number |

### Request Body

| Content-Type | Required | Schema |
|-------------|----------|--------|
| application/json | Yes | → ResultDTOOdmTaskListResponse |

### Responses

| Status | Description | Schema |
|--------|-------------|--------|
| 200 | OK | → ResultDTOOdmTaskListResponse |
| 400 | Bad Request | — |
| 500 | Internal Server Error | — |

---
```

**Rules:**
- Separator line `---` between endpoints
- Parameters table: skip if empty, show "None" row
- Request body section: skip if no request body
- Schema references: show as `→ RefName` (arrow + last segment of $ref)
- Group endpoints by HTTP method: GET first, then POST, PUT, DELETE, PATCH

### Format B: Structured JSON

For each module, generate the following JSON structure:

```json
{
  "meta": {
    "sourceUrl": "<original URL or file path>",
    "generatedAt": "<ISO 8601 timestamp>",
    "openapiVersion": "<3.1.0 or 2.0>"
  },
  "module": {
    "name": "<tag name>",
    "description": "<tag description>"
  },
  "endpointCount": 12,
  "endpoints": [
    {
      "path": "/api/flights",
      "method": "GET",
      "summary": "Get flight list",
      "description": "Return paginated flight list",
      "operationId": "getFlights",
      "parameters": [
        {
          "name": "page",
          "in": "query",
          "type": "integer",
          "required": false,
          "default": 1,
          "description": "Page number"
        }
      ],
      "requestBody": null,
      "responses": [
        {
          "status": "200",
          "description": "OK",
          "schemaRef": "ResultDTOOdmTaskListResponse"
        },
        {
          "status": "500",
          "description": "Internal Server Error",
          "schemaRef": null
        }
      ]
    }
  ]
}
```

**Rules:**
- `null` for absent fields (not omitted)
- `schemaRef` is the last segment of the `$ref`, or `null` if no schema reference
- `parameters` is `[]` (empty array) when none, not `null`
- Generate timestamp using: `date -u +"%Y-%m-%dT%H:%M:%SZ"`
- Detect OpenAPI version from document: `jq -r '.openapi // .swagger' <source-file>`

### Multiple modules

Each selected module generates its own Markdown section (separated by `## Module Selection: ...` header) and its own JSON file. When saving to files, use the module name as filename:

```
api-doc-parser/.output/
├── 飞行计划.md
├── 飞行计划.json
├── 飞行监控.md
└── 飞行监控.json
```

Sanitize filenames: replace `/`, `\`, `:`, `*`, `?`, `"`, `<`, `>`, `|` with `_`.

**Phase 4 output:** Formatted Markdown in Agent context and/or JSON files on disk.

## Phase 5: Output Mode

### Ask user for output mode

```
Output mode:
  A — Display directly in conversation (no files written)
  B — Save Markdown + JSON files to api-doc-parser/.output/

Which mode? (A/B)
```

### Mode A: Direct display

Output the Markdown directly into the conversation. Display a summary after the full output:

```
## Parse Complete

- **Source:** <URL or file path>
- **Modules parsed:** <count>
- **Total endpoints:** <count>
- **Format:** Markdown (shown above)

To save for later reference, re-run with output mode B.
```

### Mode B: File persistence

1. Create `.output/` directory if it doesn't exist:
   ```bash
   mkdir -p api-doc-parser/.output/
   ```

2. Write Markdown file:
   Write the Markdown content to `api-doc-parser/.output/<module>.md`

3. Write JSON file:
   Write the JSON content to `api-doc-parser/.output/<module>.json`

4. Display summary in conversation:

```
## Parse Complete — Files Saved

- **Source:** <URL or file path>
- **Modules parsed:** <count>
- **Total endpoints:** <count>

### Output Files

| File | Format | Size |
|------|--------|------|
| api-doc-parser/.output/飞行计划.md | Markdown | 12.3 KB |
| api-doc-parser/.output/飞行计划.json | JSON | 8.7 KB |
| api-doc-parser/.output/飞行监控.md | Markdown | 9.1 KB |
| api-doc-parser/.output/飞行监控.json | JSON | 6.2 KB |
```

---

## Context Overflow Protection Rules

**These rules are CRITICAL and must be followed exactly.**

### Rule 1: Never read raw OpenAPI JSON into Agent context

Do NOT use the Read tool on any OpenAPI JSON file. Always use jq pipelines in Bash to extract only the needed data. The raw file may be 100-500KB — too large for safe context loading.

### Rule 2: jq for all JSON filtering

| Task | Command |
|------|---------|
| Extract tag list | `jq '.tags[]' <file>` |
| Count endpoints per tag | `jq '[.paths \| to_entries[] \| .value \| to_entries[]? \| .value.tags[]?] \| group_by(.) \| .[] \| "\(.[0]):\(length)"' <file>` |
| Filter paths by tag | `jq --arg tag "TAG" '.paths \| to_entries \| map(select(.value \| to_entries \| .[].value.tags? \| contains([\$tag]))) \| from_entries' <file>` |
| Get OpenAPI version | `jq -r '.openapi // .swagger' <file>` |

### Rule 3: Large module protection

Before full endpoint extraction, count endpoints for each selected module. If >30:
1. Display summary (method + path + summary only) first
2. Warn user about context consumption
3. Wait for explicit confirmation before full extraction

### Rule 4: Local file size check

For local `.json` files, run `wc -c <file>` first. If >262144 bytes (256KB):
- MUST use jq filtering, never Read the file
- If jq is not available: report "jq required for files >256KB" and stop

### Rule 5: .md and .txt pagination

For non-JSON files, use Read with `offset` and `limit` parameters (max 2000 lines per read). Never read the entire file at once if it exceeds 2000 lines.

### Rule 6: Temp file cleanup (optional)

After parsing, optionally clean up temp files:
```bash
rm -f /tmp/api-doc.json
```
This is optional — temp files are harmless and may be reused.

---

## Error Recovery Table

| Error | Recovery |
|-------|----------|
| URL unreachable | Report HTTP status/error; offer retry or local file fallback |
| Invalid JSON | Report "Not a valid OpenAPI/Swagger JSON document"; show first 100 chars for diagnosis |
| No tags found | Fall back: extract unique tags from path operations; if still none, use "_default" module |
| No endpoints for module | Report "No endpoints found for module [name]"; continue with remaining modules |
| jq not available | For files ≤256KB: fall back to Read with offset/limit; For >256KB: report "jq required, please install jq" |
| Module name contains filesystem-unsafe chars | Sanitize: replace `\/:*?"<>\|` with `_` |
| User selects non-existent index | Report "Index # out of range (1–N)"; ask to re-enter |
| Empty .md/.txt file | Report "File is empty"; ask for new source |
