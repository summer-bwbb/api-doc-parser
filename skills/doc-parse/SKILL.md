---
name: doc-parse
description: Phase 3-5 of api-doc-parser — extract endpoint details from OpenAPI/Swagger by selected tag(s), generate Markdown and JSON output, and deliver via display mode (A) or file save mode (B). Reads selectedTags from shared state file.
---

# doc-parse — Phase 3-5: Endpoint Extraction and Output

Extract full endpoint details for selected API modules and generate dual-format output. This is the third (and final operational) phase of the `api-doc-parser` pipeline. Reads `sourcePath` and `selectedTags` from the shared state file.

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

```bash
jq -r '.sourcePath' /tmp/api-doc-parser/state.json 2>/dev/null || echo ""
jq -r '.selectedTags[]' /tmp/api-doc-parser/state.json 2>/dev/null || echo ""
```

### Handle Missing State

- If `sourcePath` is missing: "No source document registered. Please run doc-fetch first."
- If `selectedTags` is missing or empty: "No modules selected. Please run doc-list first."
- If the user provides a keyword directly (e.g., "parse the 飞行计划 module"): attempt to match the keyword against available tags. If a unique match is found, use it as `selectedTags` and continue. If ambiguous, prompt for clarification.

### Direct Parse (Bypass doc-list)

If the user provides a tag keyword with their parse request, and `sourcePath` exists in state, you can bypass `doc-list`:

1. Extract all tags from the source: `jq -r '.tags[]?.name' <source-file>`
2. Match the user's keyword using the same fuzzy matching rules from `doc-list`.
3. If a single unambiguous match: set `selectedTags` and proceed.
4. If multiple matches or no match: fall back to `doc-list` for interactive selection.

---

## Phase 3: Endpoint Extraction

For each selected tag name, extract endpoints using jq. **Never read raw JSON into context.**

### Step 1: Filter paths by tag

```bash
jq --arg tag "$TAG_NAME" '
  .paths | to_entries | map(
    select(.value | to_entries | .[].value.tags? // [] | contains([$tag]))
  ) | from_entries
' <source-file>
```

### Step 2: Extract endpoint details (single jq query)

This query runs entirely in shell -- only the structured result enters Agent context:

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

### Step 3: Schema Expansion ($ref Resolution)

After extracting endpoints, resolve all `$ref` references into full field definitions. This ensures Responses and Request Body display complete schema details instead of just reference names.

#### Step 3a: Collect all unique $ref names

From the source document, gather all `$ref` values in `responses` and `requestBody` for the selected tag:

```bash
cat > /tmp/api-doc-parser/get-refs.jq << 'JQEOF'
.paths | to_entries[] |
  .value | to_entries[] |
  select(.key != "parameters") |
  select(.value.tags? // [] | contains(["$TAG_NAME"])) |
  .value |
  (
    (.responses // {} | to_entries | map(.value) |
     map(.content // {} | to_entries | map(.value.schema) | .[]) |
     map(."$ref" // empty, .items."$ref" // empty) | .[]),
    (.requestBody // {} | .content // {} | to_entries | map(.value.schema) | .[] |
     ."$ref" // empty, .items."$ref" // empty)
  ) |
  select(. != null) |
  select(startswith("#/components/schemas/")) |
  split("/")[-1]
JQEOF

# Replace $TAG_NAME with actual tag, then run
sed -i 's/\$TAG_NAME/实际TAG名/' /tmp/api-doc-parser/get-refs.jq
jq -r -f /tmp/api-doc-parser/get-refs.jq <source-file> | sort -u
```

**Output:** A deduplicated list of schema names (e.g., `ResultDTOVoid`, `ResultDTOLong`, `SaveHighPointMonitorParam`, ...).

#### Step 3b: Batch-resolve schemas from components

For each unique schema name, query `components/schemas/<name>`:

```bash
# Use bash heredoc with schema name as bash variable, jq $ variables escaped
cat > /tmp/api-doc-parser/resolve.jq << JQEOF
.components.schemas["$SCHEMA_NAME"] |
{
  description: (.description // null),
  required: (.required // []),
  fields: (.properties // {} | to_entries | map(
    .key as \$fname |
    .value |
    {
      name: \$fname,
      type: (
        if ."\$ref" then "object"
        elif .items."\$ref" then "array"
        else (.type // "object")
        end
      ),
      format: (.format // null),
      description: (.description // "(无描述)"),
      ref: (
        if ."\$ref" then (."\$ref" | split("/")[-1])
        elif .items."\$ref" then (.items."\$ref" | split("/")[-1])
        else null end
      ),
      default: (.default // null),
      deprecated: (.deprecated // false)
    }
  ))
}
JQEOF

jq -f /tmp/api-doc-parser/resolve.jq <source-file>
```

**Important jq notes:**
- `$ref` is a valid jq field access syntax (e.g., `."$ref"` reads the `$ref` key). This is NOT a variable.
- In bash heredoc, escape jq variables (`$fname`) with `\$fname` while leaving `$SCHEMA_NAME` unescaped for bash expansion.
- For batch resolution of all schemas at once, use the pattern in Step 3a output to build a loop.

#### Step 3c: Recursive expansion (depth limit: 2)

If a resolved schema contains fields with nested `$ref`, resolve those too. **Maximum 2 levels deep** to prevent circular references and context bloat.

- **Depth 0:** Top-level response/requestBody schemas (e.g., `ResultDTOIPageHighPointMonitorDTO`)
- **Depth 1:** Nested schemas (e.g., `IPageHighPointMonitorDTO` inside `data` field)
- **Depth 2:** Further nesting (e.g., `HighPointMonitorDTO` inside `records` array)
- **Beyond depth 2:** Display as `→ SchemaName` with note "（递归上限，请查看 Swagger UI）"

Circular reference detection: if a schema name has already been resolved at an earlier depth, do not re-resolve it. Display as `→ SchemaName` with note "（循环引用）".

#### Step 3d: Deduplication and caching

- **Same schema, multiple endpoints:** Resolve once, reuse everywhere. Cache resolved schemas in memory keyed by schema name.
- **Shared error schemas:** Many endpoints share the same error response schema (e.g., `ResultDTOVoid` for 400/500/502). Resolve once, merge display in output.

### Step 4: Parse the jq output

### Empty Module Handling

If the filtered paths object is empty after jq filtering:

```
No endpoints found for module "<tag name>".
```

Continue processing remaining selected modules. Do not halt the entire pipeline.

### Large Module Protection

If a selected module has >30 endpoints (already warned in Phase 2, but re-check here):

1. Display summary (method + path + summary only) first.
2. Warn about context consumption.
3. Wait for explicit confirmation before full extraction.

---

## Phase 4: Output Generation

### Format A: Markdown (human-readable)

For each module, generate the following Markdown structure with **fully expanded schemas**:

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

### Request Body (application/json, required)

#### SchemaName

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| highPointMonitorId | integer(int64) | Yes | 主键ID（编辑时必填） |
| name | string | No | 名称 |
| deviceCode | string | No | 设备编号 |
| ... | | | |

> If the Request Body schema contains nested $ref fields, expand them as sub-tables:

#### NestedSchemaName

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| subField1 | string | — | 描述 |
| subField2 | array<ItemName> | — | 描述 |

### Responses

| Status | Description | Schema |
|--------|-------------|--------|
| 200 | OK | ResultDTOIPageHighPointMonitorDTO |
| 400 | Bad Request | ResultDTOVoid |
| 500 | Internal Server Error | ResultDTOVoid |
| 502 | Bad Gateway | ResultDTOVoid |

#### 200 OK — ResultDTOIPageHighPointMonitorDTO

| 字段 | 类型 | 描述 |
|------|------|------|
| errorCode | string | 错误码 |
| errorMsg | string | 错误消息 |
| data | IPageHighPointMonitorDTO | 数据（详见下方） |

#### IPageHighPointMonitorDTO

| 字段 | 类型 | 描述 |
|------|------|------|
| size | integer(int64) | 每页大小 |
| current | integer(int64) | 当前页码 |
| total | integer(int64) | 总记录数 |
| records | array<HighPointMonitorDTO> | 记录列表 |

#### HighPointMonitorDTO

| 字段 | 类型 | 描述 |
|------|------|------|
| highPointMonitorId | integer(int64) | 主键ID |
| name | string | 名称 |
| deviceCode | string | 设备编号 |
| ... | | |

> **Dedup optimization:** When multiple status codes share the same schema, merge them:
>
> #### 400 / 500 / 502 — ResultDTOVoid（通用错误响应）
>
> | 字段 | 类型 | 描述 |
> |------|------|------|
> | errorCode | string | 错误码 |
> | errorMsg | string | 错误消息 |
> | data | any | 数据（无固定结构） |

---
```

**Formatting rules:**
- Separator line `---` between endpoints
- Parameters table: skip if empty, show "无参数"
- Request body section: skip if no request body; otherwise expand schema as field table with columns `字段 | 类型 | 必填 | 描述`
- Responses: expand each unique schema as a field table with columns `字段 | 类型 | 描述`; nested schemas shown as sub-tables
- **Dedup shared schemas:** Multiple status codes with the same schema merged into one section (e.g., `400 / 500 / 502 — ResultDTOVoid（通用错误响应）`)
- Group endpoints by HTTP method: GET first, then POST, PUT, DELETE, PATCH
- Schema depth limit: 2 levels of nesting; beyond that show `-> SchemaName（递归上限，请查看 Swagger UI）`
- Array types displayed as `array<TypeName>` when items contain a $ref
- Deprecated fields marked with strikethrough and `(已废弃)` note

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
      "requestBody": {
        "required": true,
        "contentType": "application/json",
        "schema": {
          "name": "SaveHighPointMonitorParam",
          "description": "高点监控数据",
          "fields": [
            {
              "name": "highPointMonitorId",
              "type": "integer",
              "format": "int64",
              "description": "主键ID（编辑时必填）",
              "required": true,
              "default": null,
              "nestedSchema": null
            },
            {
              "name": "name",
              "type": "string",
              "format": null,
              "description": "名称",
              "required": false,
              "default": null,
              "nestedSchema": null
            }
          ],
          "nestedSchemas": {}
        }
      },
      "responses": [
        {
          "status": "200",
          "description": "OK",
          "schema": {
            "name": "ResultDTOLong",
            "description": "通用返回结果",
            "fields": [
              {"name": "errorCode", "type": "string", "description": "错误码", "nestedSchema": null},
              {"name": "errorMsg", "type": "string", "description": "错误消息", "nestedSchema": null},
              {"name": "data", "type": "integer", "format": "int64", "description": "数据", "nestedSchema": null}
            ],
            "nestedSchemas": {}
          }
        },
        {
          "status": "400",
          "description": "Bad Request",
          "schema": {
            "name": "ResultDTOVoid",
            "description": "通用返回结果",
            "fields": [
              {"name": "errorCode", "type": "string", "description": "错误码", "nestedSchema": null},
              {"name": "errorMsg", "type": "string", "description": "错误消息", "nestedSchema": null},
              {"name": "data", "type": "any", "description": "数据", "nestedSchema": null}
            ],
            "nestedSchemas": {}
          }
        }
      ]
    }
  ]
}
```

**JSON rules:**
- `null` for absent fields (not omitted)
- `requestBody` is `null` when absent; when present, contains full expanded schema object
- `responses[].schema` contains a full schema object with `name`, `description`, `fields[]`, and `nestedSchemas{}`
- Each field has: `name`, `type`, `format` (nullable), `description`, `required` (nullable), `default` (nullable), `nestedSchema` (string name or null)
- `nestedSchemas` maps schema names to their own `{description, fields[]}` objects (depth limit: 2)
- `parameters` is `[]` (empty array) when none, not `null`
- Generate timestamp using: `date -u +"%Y-%m-%dT%H:%M:%SZ"`
- Detect OpenAPI version from document: `jq -r '.openapi // .swagger' <source-file>`

### Multiple Modules

Each selected module generates its own Markdown section and its own JSON object/file. When saving to files, use the module name as filename:

```
api-doc-parser/.output/
├── 飞行计划.md
├── 飞行计划.json
├── 飞行监控.md
└── 飞行监控.json
```

**Filename sanitization:** Replace `/`, `\`, `:`, `*`, `?`, `"`, `<`, `>`, `|` with `_`.

---

## Phase 5: Output Mode

The output mode can be:
- Persisted in state.json (`outputMode`: "A" or "B") -- if present, use it as default but allow override.
- Overridden via flags: `-a` / `--display` (Mode A) or `-b` / `--save` (Mode B).
- Prompted if neither is set (first run).

### First-run prompt

If `outputMode` is not set in state.json:

```
Output mode:
  A — Display directly in conversation (no files written)
  B — Save Markdown + JSON files to api-doc-parser/.output/

Which mode? (A/B)
```

After user selection, persist in state.json:
```bash
jq '. + {outputMode: "A"}' /tmp/api-doc-parser/state.json > /tmp/api-doc-parser/state.json.tmp && mv /tmp/api-doc-parser/state.json.tmp /tmp/api-doc-parser/state.json
```

### Mode A: Direct Display

Output the Markdown directly into the conversation. Display a summary after the full output:

```
## Parse Complete

- **Source:** <URL or file path>
- **Modules parsed:** <count>
- **Total endpoints:** <count>
- **Format:** Markdown (shown above)

To save for later reference, re-run with output mode B.
```

No files are written to disk.

### Mode B: File Persistence

1. Create `.output/` directory if needed:
   ```bash
   mkdir -p api-doc-parser/.output/
   ```

2. Write Markdown files:
   Use the Write tool to save `api-doc-parser/.output/<module>.md` for each module.

3. Write JSON files:
   Use the Write tool to save `api-doc-parser/.output/<module>.json` for each module.

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

## Error Recovery

| Error | Recovery |
|-------|----------|
| No endpoints for module | Report: "No endpoints found for module [name]." Continue with remaining modules. |
| jq not available | For files ≤256KB: fall back to Read with offset/limit. For >256KB: report "jq required, please install jq >= 1.6." |
| Module name contains filesystem-unsafe chars | Sanitize: replace `\/:*?"<>\|` with `_` |
| State file missing | Prompt: "No source registered. Start with doc-fetch." |
| selectedTags empty | Prompt: "No modules selected. Run doc-list to select modules." |

---

## Context Overflow Prevention

1. **Never read raw OpenAPI JSON into Agent context.** All extraction uses jq pipelines.
2. **jq for all path filtering.** The filter query runs in shell, only filtered results enter context.
3. **Endpoint extraction uses a single jq query** per tag, delimited by `===ENDPOINT===`.
4. **Large module protection** — >30 endpoints requires confirmation before full extraction.
5. **Schema expansion depth limit** — max 2 levels of $ref nesting. Beyond that, show `-> SchemaName（递归上限）`.
6. **Schema deduplication** — same schema referenced by multiple endpoints/status codes is resolved only once and reused.
7. **Single schema field cap** — if a schema has >50 fields, show first 50 and note `（字段过多，仅展示前 50 个，完整定义请查看 Swagger UI）`.
8. **Schema queries via jq only** — never read `components/schemas` raw into context; always use jq filters to extract specific schemas by name.
9. **Optional temp file cleanup:**
   ```bash
   rm -f /tmp/api-doc.json /tmp/api-doc-parser/endpoints-raw.json
   ```
   This is optional — temp files are harmless and may be reused.
