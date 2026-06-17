---
change: upgrade-api-doc-parser-v2
design-doc: docs/superpowers/specs/2026-06-15-upgrade-api-doc-parser-v2-design.md
base-ref: fb0a432f9edfaea84a60c80500aceac9239d32d7
---

# API Doc Parser v2 升级实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将单一 SKILL.md (v1) 升级为 5 个独立子技能 + 9 平台命令路由 + Plugin/NPM 双渠道分发的 v2 架构

**Architecture:** 子技能在 `skills/` 作为唯一真身，各平台仅保留薄代理文件（`@` 引用）。SessionStart hook 注入 `using-api-doc-parser` 元指令。`/tmp/api-doc-parser/state.json` 实现 Phase 间状态传递。3 种安装方式：Plugin、NPM、手动。

**Tech Stack:** Shell (bash), jq (≥1.6), curl (≥7.0), Node.js (postinstall/preuninstall scripts), Markdown

---

## File Structure Overview

```
api-doc-parser/
├── skills/                        ← 【唯一真身】5 个子技能
│   ├── using-api-doc-parser/SKILL.md
│   ├── doc-fetch/SKILL.md
│   ├── doc-list/SKILL.md
│   ├── doc-parse/SKILL.md
│   └── doc-help/SKILL.md
├── hooks/
│   ├── hooks.json
│   └── session-start.sh
├── scripts/
│   ├── postinstall.js
│   ├── preuninstall.js
│   └── check-deps.sh
├── docs/
│   ├── INSTALL.md
│   ├── USAGE.md
│   └── CHANGELOG.md
├── .claude-plugin/ + .cursor-plugin/ + .codex-plugin/
├── .claude/ + .cursor/ + .codex/ + .gemini/ + .kimi/ + .qoder/ + .trae/ + .opencode/ + .github/
│   └── skills/{5 sub-skills}/SKILL.md (thin @ proxies)
│   └── commands/doc/{fetch,list,parse,help}.{md,toml,prompt.md}
├── SKILL.md                       ← 修改：v1 内容 + 子技能导航
├── metadata.json                  ← 修改：version → 2.0.0
├── README.md                      ← 修改：v2 架构说明
├── package.json                   ← 新增
├── GEMINI.md                      ← 新增
├── AGENTS.md                      ← 新增
└── gemini-extension.json          ← 新增
```

---

### Task 1: Cleanup — 移除无关的 openspec 文件

**Files:**
- Delete: `.claude/skills/openspec-*/` (6 dirs)
- Delete: `.claude/commands/opsx/` (6 files)
- Delete: `.cursor/skills/openspec-*/` (6 dirs)
- Delete: `.cursor/commands/opsx-*.md` (6 files)
- Delete: `.codex/skills/openspec-*/` (6 dirs, if any commands files exist too)
- Delete: `.gemini/skills/openspec-*/` (6 dirs)
- Delete: `.kimi/skills/openspec-*/` (6 dirs)
- Delete: `.qoder/skills/openspec-*/` (6 dirs)
- Delete: `.qoder/commands/opsx/` (if exists)
- Delete: `.trae/skills/openspec-*/` (6 dirs)
- Delete: `.opencode/skills/openspec-*/` (6 dirs)
- Delete: `.opencode/commands/opsx-*.md` (if exists)
- Delete: `.github/skills/openspec-*/` (6 dirs)
- Delete: `.github/prompts/opsx-*.prompt.md` (if exists)

- [ ] **Step 1: Remove all openspec directories and files**

```bash
# Remove openspec skills from all platform directories
rm -rf .claude/skills/openspec-*/
rm -rf .claude/commands/opsx/
rm -rf .cursor/skills/openspec-*/
rm -f .cursor/commands/opsx-*.md
rm -rf .codex/skills/openspec-*/
rm -rf .gemini/skills/openspec-*/
rm -rf .kimi/skills/openspec-*/
rm -rf .qoder/skills/openspec-*/
rm -rf .qoder/commands/opsx/
rm -rf .trae/skills/openspec-*/
rm -rf .opencode/skills/openspec-*/
rm -f .opencode/commands/opsx-*.md
rm -rf .github/skills/openspec-*/
rm -f .github/prompts/opsx-*.prompt.md
```

- [ ] **Step 2: Verify cleanup**

```bash
# Confirm no openspec files remain
find . -path '*/openspec-*' -type f 2>/dev/null || echo "No openspec files found — cleanup successful."
```

- [ ] **Step 3: Verify existing files intact**

```bash
# Confirm SKILL.md, metadata.json, README.md still exist
ls -la SKILL.md metadata.json README.md
```

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "chore: remove openspec files unrelated to api-doc-parser

These files belong to the openspec plugin and should be installed
independently rather than bundled inside api-doc-parser."
```

---

### Task 2: Create core sub-skills in `skills/`

**Files:**
- Create: `skills/using-api-doc-parser/SKILL.md`
- Create: `skills/doc-fetch/SKILL.md`
- Create: `skills/doc-list/SKILL.md`
- Create: `skills/doc-parse/SKILL.md`
- Create: `skills/doc-help/SKILL.md`

- [ ] **Step 1: Create `skills/using-api-doc-parser/SKILL.md`**

```markdown
---
name: using-api-doc-parser
description: Meta-instructions for discovering and invoking api-doc-parser sub-skills. This skill is injected at session start via SessionStart hook and teaches agents how to chain doc-fetch → doc-list → doc-parse for OpenAPI/Swagger documentation parsing.
---

# Using API Doc Parser

You have the **api-doc-parser** plugin installed. It provides a set of sub-skills for parsing OpenAPI 3.x and Swagger 2.0 API documentation.

## Sub-Skills

| Sub-skill | Purpose | Invocation |
|-----------|---------|------------|
| `doc-fetch` | Fetch and validate API docs from URL or local file | `/doc:fetch <URL or path>` |
| `doc-list` | List all API modules (tags) with endpoint counts | `/doc:list [keywords\|indices\|all]` |
| `doc-parse` | Extract full endpoint details for selected modules | `/doc:parse [--mode A\|B] [query]` |
| `doc-help` | Display usage instructions and examples | `/doc:help` |

## Natural Language Triggers

When the user mentions ANY of these, invoke the corresponding sub-skill via the Skill tool:
- "parse API docs", "extract endpoints", "list API modules" → `doc-fetch` + `doc-list` + `doc-parse`
- "Swagger", "OpenAPI", "api-docs" with a URL or file → `doc-fetch`
- "show endpoints", "API reference", "endpoint details" → `doc-list` + `doc-parse`

## Pipeline

The sub-skills share state via `/tmp/api-doc-parser/state.json`. They can be called independently:

```
/doc:fetch <source>  →  /doc:list  →  /doc:parse [query]
```

Each step can be called in separate conversation turns. State persists across calls.

## Output Modes

- **Mode A** (default): Display results directly in conversation
- **Mode B**: Save `.md` + `.json` files to `api-doc-parser/.output/`

Override with `--display` (Mode A) or `--save` (Mode B) on `/doc:parse`.
```

- [ ] **Step 2: Create `skills/doc-fetch/SKILL.md`**

```markdown
---
name: doc-fetch
description: Fetch and validate OpenAPI/Swagger documentation from a URL or local file. Phase 1 of the api-doc-parser pipeline. Saves source metadata to /tmp/api-doc-parser/state.json for subsequent doc-list and doc-parse calls.
---

# API Doc Fetch

Fetch API documentation from a URL or local file and prepare it for parsing.

## Runtime Dependency Check

Before executing, verify required tools are available:

```bash
# Check jq
if ! command -v jq &> /dev/null; then
  echo "ERROR: jq is required. Install:"
  case "$(uname -s)" in
    Darwin*) echo "  brew install jq" ;;
    Linux*)  echo "  sudo apt install jq" ;;
    MINGW*)  echo "  choco install jq" ;;
  esac
  exit 1
fi

# Check jq version >= 1.6
JQ_VER=$(jq --version 2>&1 | grep -oP '\d+\.\d+' | head -1)
if [ -z "$JQ_VER" ]; then
  echo "ERROR: Could not detect jq version. jq >= 1.6 required."
  exit 1
fi

# Check curl
if ! command -v curl &> /dev/null; then
  echo "ERROR: curl is required. Install:"
  case "$(uname -s)" in
    Darwin*) echo "  brew install curl" ;;
    Linux*)  echo "  sudo apt install curl" ;;
    MINGW*)  echo "  choco install curl" ;;
  esac
  exit 1
fi
```

## Determine Temp Directory

```bash
# Cross-platform temp directory
if [ -n "$TMPDIR" ]; then
  TEMP_DIR="$TMPDIR"
elif [ -n "$TEMP" ]; then
  TEMP_DIR="$TEMP"
else
  TEMP_DIR="/tmp"
fi
STATE_DIR="$TEMP_DIR/api-doc-parser"
mkdir -p "$STATE_DIR"
```

## Step 1: Detect Input Type

Ask the user for the API documentation source. If already provided in the command arguments (`$ARGUMENTS` or `$1`), use it directly.

| Input | Detection | Action |
|-------|-----------|--------|
| URL | Starts with `http://` or `https://` | Fetch via curl → save to `$STATE_DIR/fetched.json` |
| Local `.json` file | Path ends in `.json` | Copy or reference directly |
| Local `.md` file | Path ends in `.md` | Record path for LLM extraction |
| Local `.txt` file | Path ends in `.txt` | Record path for LLM extraction |

## Step 2: Process by Input Type

### URL source

```bash
SOURCE_URL="$1"

# Step 2a: Check connectivity
HTTP_CODE=$(curl -s -I -o /dev/null -w "%{http_code}" "$SOURCE_URL" 2>&1)
if [ "$HTTP_CODE" != "200" ]; then
  echo "ERROR: Unable to reach URL: $SOURCE_URL"
  echo "HTTP status: $HTTP_CODE"
  echo "Would you like to retry, or provide a local file path instead?"
  exit 1
fi

# Step 2b: Fetch and save (never display raw content)
curl -s "$SOURCE_URL" -o "$STATE_DIR/fetched.json"

# Step 2c: Check file size — warn if >10MB, reject if >50MB
FILE_SIZE=$(wc -c < "$STATE_DIR/fetched.json" 2>/dev/null || echo 0)
if [ "$FILE_SIZE" -gt 52428800 ]; then
  echo "ERROR: File size ($FILE_SIZE bytes) exceeds 50MB limit. Refusing to process."
  rm -f "$STATE_DIR/fetched.json"
  exit 1
elif [ "$FILE_SIZE" -gt 10485760 ]; then
  echo "WARNING: File is large ($FILE_SIZE bytes). Parsing may be slow."
fi

# Step 2d: Validate JSON
if ! jq 'type' "$STATE_DIR/fetched.json" > /dev/null 2>&1; then
  echo "ERROR: Not a valid JSON document."
  echo "First 200 characters:"
  head -c 200 "$STATE_DIR/fetched.json"
  exit 1
fi

# Step 2e: Validate OpenAPI/Swagger format
OPENAPI_VER=$(jq -r '.openapi // .swagger // empty' "$STATE_DIR/fetched.json")
if [ -z "$OPENAPI_VER" ]; then
  echo "ERROR: Not a valid OpenAPI or Swagger document (no 'openapi' or 'swagger' field found)."
  exit 1
fi

# Detect Swagger 2.x
if echo "$OPENAPI_VER" | grep -q '^2\.'; then
  echo "WARNING: Swagger 2.x detected. Some features may be limited."
fi
```

### Local JSON file

```bash
SOURCE_FILE="$1"

# Check file exists
if [ ! -f "$SOURCE_FILE" ]; then
  echo "ERROR: File not found: $SOURCE_FILE"
  echo "Please check the path. Using an absolute path is recommended."
  exit 1
fi

# Check file size
FILE_SIZE=$(wc -c < "$SOURCE_FILE" 2>/dev/null || echo 0)

# Copy to temp for consistent processing
cp "$SOURCE_FILE" "$STATE_DIR/fetched.json"

# Validate JSON
if ! jq 'type' "$STATE_DIR/fetched.json" > /dev/null 2>&1; then
  echo "ERROR: Not a valid JSON document."
  rm -f "$STATE_DIR/fetched.json"
  exit 1
fi

# Validate OpenAPI/Swagger
OPENAPI_VER=$(jq -r '.openapi // .swagger // empty' "$STATE_DIR/fetched.json")
if [ -z "$OPENAPI_VER" ]; then
  echo "ERROR: Not a valid OpenAPI or Swagger document."
  rm -f "$STATE_DIR/fetched.json"
  exit 1
fi
```

### Local .md / .txt file

```bash
SOURCE_FILE="$1"

if [ ! -f "$SOURCE_FILE" ]; then
  echo "ERROR: File not found: $SOURCE_FILE"
  exit 1
fi

# For .md/.txt, just record the path — LLM extraction will happen in doc-parse
cp "$SOURCE_FILE" "$STATE_DIR/fetched.plain"
```

## Step 3: Write State File

After successful fetch, write state.json:

```bash
SOURCE_TYPE="url"  # or "file"
NOW=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

jq -n \
  --arg sourcePath "$STATE_DIR/fetched.json" \
  --arg sourceType "$SOURCE_TYPE" \
  --arg sourceUrl "${SOURCE_URL:-$SOURCE_FILE}" \
  --arg openapiVersion "$OPENAPI_VER" \
  --arg fetchedAt "$NOW" \
  '{
    sourcePath: $sourcePath,
    sourceType: $sourceType,
    sourceUrl: $sourceUrl,
    openapiVersion: $openapiVersion,
    fetchedAt: $fetchedAt,
    outputMode: null
  }' > "$STATE_DIR/state.json"

echo "✓ Documentation fetched successfully."
echo "  Source: ${SOURCE_URL:-$SOURCE_FILE}"
echo "  OpenAPI version: $OPENAPI_VER"
echo "  Ready for /doc:list or next pipeline step."
```

## Output Mode Initialization

`selectedTags` is NOT set here — it's cleared to ensure a fresh module selection with each new source. `outputMode` is initialized as `null` — first `/doc:parse` call will prompt the user to choose.

## Error Recovery Table

| Error | Recovery |
|-------|----------|
| URL unreachable | Report HTTP status/error; offer retry or local file fallback |
| Invalid JSON | Report "Not a valid OpenAPI/Swagger JSON document"; show first 200 chars |
| File >50MB | Reject with error message |
| File 10-50MB | Warn but allow; suggest cropping |
| No openapi/swagger field | Report "Not a valid OpenAPI/Swagger document" |
| Swagger 2.x | Warn "Some features limited" but continue |
| jq not available | Report install instructions and stop |
| Can't write to state dir | Fall back to memory-only mode; warn state won't persist |
```

- [ ] **Step 3: Create `skills/doc-list/SKILL.md`**

```markdown
---
name: doc-list
description: List all API modules (tags) from an OpenAPI/Swagger document, with endpoint counts. Phase 2 of the api-doc-parser pipeline. Supports keyword fuzzy matching, index selection, and all selection. Writes selectedTags to shared state file.
---

# API Doc List

List all API modules (tags) from a fetched OpenAPI/Swagger document. Select modules by index, keyword, or both.

## Runtime Dependency Check

```bash
if ! command -v jq &> /dev/null; then
  echo "ERROR: jq is required. Install:"
  case "$(uname -s)" in
    Darwin*) echo "  brew install jq" ;;
    Linux*)  echo "  sudo apt install jq" ;;
    MINGW*)  echo "  choco install jq" ;;
  esac
  exit 1
fi
```

## Step 1: Determine Temp Directory and Load State

```bash
# Cross-platform temp directory
if [ -n "$TMPDIR" ]; then TEMP_DIR="$TMPDIR"
elif [ -n "$TEMP" ]; then TEMP_DIR="$TEMP"
else TEMP_DIR="/tmp"
fi
STATE_DIR="$TEMP_DIR/api-doc-parser"
STATE_FILE="$STATE_DIR/state.json"
```

### Read state with priority: /tmp → project-level

```
read_state():
  1. if STATE_FILE exists → use it
  2. elif <project>/.api-doc-parser/state.json exists → copy to STATE_FILE, use it
  3. else → prompt user to provide a source (URL or file), then delegate to doc-fetch internally
```

### Validate state file

```bash
if ! jq '.' "$STATE_FILE" > /dev/null 2>&1; then
  echo "ERROR: State file corrupted (invalid JSON). Please re-run /doc:fetch."
  exit 1
fi
```

### Check source file still exists

```bash
SOURCE_PATH=$(jq -r '.sourcePath' "$STATE_FILE")
if [ ! -f "$SOURCE_PATH" ]; then
  echo "ERROR: Source file not found: $SOURCE_PATH"
  echo "Please re-run /doc:fetch."
  exit 1
fi
```

## Step 2: Extract Tags

```bash
# Extract all unique tags with descriptions
jq -r '.tags[]? | "\(.name)|||\(.description // "(no description)")"' "$SOURCE_PATH"
```

If `.tags` is empty (Swagger 2.0 may lack tags), extract unique tags from path operations:

```bash
# Fallback: extract tags from path operations
jq -r '[.paths | to_entries[] | .value | to_entries[]? | .value.tags[]?] | unique | .[]' "$SOURCE_PATH"
```

If still no tags, assign all paths to a synthetic "_default" module.

### Count endpoints per tag

```bash
jq -r '[.paths | to_entries[] | .value | to_entries[]? | .value.tags[]?] | group_by(.) | .[] | "\(.[0]):\(length)"' "$SOURCE_PATH"
```

## Step 3: Display Module List

Present modules in a numbered table:

```
## API Modules Found

| # | Module (tag) | Description | Endpoints |
|---|-------------|-------------|-----------|
| 1 | pet         | Pet operations | 8 |
| 2 | store       | Store operations | 4 |
| 3 | user        | User operations | 10 |

**How to select:**
- By index: `1,3`
- By keyword: `pet,store`
- Mix: `1,user`
- All: `all`
```

### Pagination for >50 tags

If more than 50 tags, display 20 per page:

```
Showing page 1/3 (tags 1-20 of 55)

| # | Module | ... |
|---|--------|-----|
| 1 | ...    | ... |
...
| 20 | ...   | ... |

Next: "page 2" | Previous: "-" | Select across pages: list indices from any page
```

## Step 4: Parse User Selection

Parse user input:

```
Input → Strategy:
  "1,3,6"     → indices → map to tags[0], tags[2], tags[5]
  "pet,store" → keywords → fuzzy match against tag names
  "1,store"   → mixed → resolve indices first, then keywords, deduplicate
  "all"        → select all
```

### Fuzzy matching rules

1. Exact match (case-insensitive) — highest priority
2. Substring match (e.g., "pet" matches "petStore")
3. Multiple matches → display all candidates, let user pick
4. No matches → report and show valid options

### Invalid input handling

If user provides an index out of range:
```
Index 15 out of range. Valid range: 1-10. Please re-enter.
```

## Step 5: Write Selected Tags to State

```bash
# Get current state, add selectedTags, write back
TAGS_JSON=$(printf '%s\n' "${SELECTED_TAGS[@]}" | jq -R . | jq -s .)
jq --argjson tags "$TAGS_JSON" \
  '. + {selectedTags: $tags}' \
  "$STATE_FILE" > "$STATE_FILE.tmp" && mv "$STATE_FILE.tmp" "$STATE_FILE"

echo "✓ Selected modules: ${SELECTED_TAGS[*]}"
echo "Ready for /doc:parse."
```

## Edge Cases

| Condition | Behavior |
|-----------|----------|
| Document has no tags | Display "1 个默认模块（未分类端点）" |
| Tags >50 | Paginate 20 per page, show navigation instructions |
| Invalid index input | Error + show valid range |
| Keyword no match | Show 3 closest candidates via fuzzy match |
| State file missing | Interactive fallback → ask for URL or file path |
| Source file deleted | Detect → prompt re-fetch |
```

- [ ] **Step 4: Create `skills/doc-parse/SKILL.md`**

```markdown
---
name: doc-parse
description: Extract full endpoint details for selected API modules. Phases 3-5 of the api-doc-parser pipeline. Supports Mode A (display) and Mode B (save files), with parameter overrides (-a/-b, --display/--save).
---

# API Doc Parse

Extract full endpoint details for selected API modules. Generates Markdown and JSON output.

## Runtime Dependency Check

```bash
if ! command -v jq &> /dev/null; then
  echo "ERROR: jq is required. Install:"
  case "$(uname -s)" in
    Darwin*) echo "  brew install jq" ;;
    Linux*)  echo "  sudo apt install jq" ;;
    MINGW*)  echo "  choco install jq" ;;
  esac
  exit 1
fi
```

## Step 0: Determine Temp Directory and Load State

```bash
# Cross-platform temp directory
if [ -n "$TMPDIR" ]; then TEMP_DIR="$TMPDIR"
elif [ -n "$TEMP" ]; then TEMP_DIR="$TEMP"
else TEMP_DIR="/tmp"
fi
STATE_DIR="$TEMP_DIR/api-doc-parser"
STATE_FILE="$STATE_DIR/state.json"
```

### Read state with priority: /tmp → project-level

Same priority logic as doc-list. If no state exists, prompt user for source → auto-fetch → auto-list.

### Validate state and source

```bash
# Validate JSON
if ! jq '.' "$STATE_FILE" > /dev/null 2>&1; then
  echo "ERROR: State file corrupted. Please re-run /doc:fetch."
  exit 1
fi

# Check source exists
SOURCE_PATH=$(jq -r '.sourcePath' "$STATE_FILE")
if [ ! -f "$SOURCE_PATH" ]; then
  echo "ERROR: Source file not found: $SOURCE_PATH. Please re-run /doc:fetch."
  exit 1
fi

# Check selectedTags exist
TAGS_COUNT=$(jq -r '.selectedTags | length' "$STATE_FILE")
if [ "$TAGS_COUNT" -eq 0 ] || [ "$(jq -r '.selectedTags' "$STATE_FILE")" = "null" ]; then
  echo "No modules selected. Run /doc:list first, or pass a keyword to auto-select."
  exit 1
fi
```

## Step 1: Inline Query Resolution

If user passes a keyword argument (e.g., `/doc:parse pet`), bypass doc-list:

```bash
QUERY="$1"  # Optional keyword argument

if [ -n "$QUERY" ] && [ "$QUERY" != "-a" ] && [ "$QUERY" != "--display" ] && [ "$QUERY" != "-b" ] && [ "$QUERY" != "--save" ]; then
  # Resolve keyword to tags via fuzzy match
  # If single match, set as selectedTags
  # If multiple matches, display candidates and ask user to narrow
fi
```

## Step 2: Determine Output Mode

```bash
OUTPUT_MODE=""  # Will be determined

# Check for explicit parameter overrides first
for arg in "$@"; do
  case "$arg" in
    -a|--display) OUTPUT_MODE="A"; break ;;
    -b|--save)    OUTPUT_MODE="B"; break ;;
  esac
done

# If no override, check state.json
if [ -z "$OUTPUT_MODE" ]; then
  PERSISTED_MODE=$(jq -r '.outputMode // empty' "$STATE_FILE")
  if [ -n "$PERSISTED_MODE" ]; then
    OUTPUT_MODE="$PERSISTED_MODE"
  else
    # First run — ask user
    echo "Output mode:"
    echo "  A — Display directly in conversation (no files written)"
    echo "  B — Save Markdown + JSON files to api-doc-parser/.output/"
    echo ""
    echo "Which mode? (A/B)"
    # Read user response and persist
    OUTPUT_MODE="<user_choice>"
    # Persist to state
    jq --arg mode "$OUTPUT_MODE" '. + {outputMode: $mode}' "$STATE_FILE" > "$STATE_FILE.tmp" && mv "$STATE_FILE.tmp" "$STATE_FILE"
  fi
fi
```

## Step 3: Extract Endpoints by Tag

For each selected tag, filter paths using jq:

```bash
TAG_NAME="$1"  # One selected tag

# Filter paths by tag
FILTERED_PATHS=$(jq --arg tag "$TAG_NAME" '
  .paths | to_entries | map(
    select(.value | to_entries | map(.value.tags // []) | flatten | contains([$tag]))
  ) | from_entries
' "$SOURCE_PATH")
```

### Large module check (>30 endpoints)

Before full extraction, count endpoints:

```bash
ENDPOINT_COUNT=$(echo "$FILTERED_PATHS" | jq 'to_entries | length')
if [ "$ENDPOINT_COUNT" -gt 30 ]; then
  echo "WARNING: Module \"$TAG_NAME\" has $ENDPOINT_COUNT endpoints."
  # Display summary table (method + path + summary only)
  echo "$FILTERED_PATHS" | jq -r '
    to_entries | .[] | .key as $path |
    .value | to_entries[] |
    "| \(.key | ascii_upcase) | \($path) | \(.value.summary // "(no summary)") |"
  '
  echo "Continue with full detail? (y/n)"
  # Wait for confirmation
fi
```

### Extract full endpoint details

```bash
jq --arg tag "$TAG_NAME" -r '
  .paths | to_entries | map(
    select(.value | to_entries | map(.value.tags // []) | flatten | contains([$tag]))
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
' "$SOURCE_PATH"
```

### $ref handling (v1 behavior)

Record only the reference name (last segment after `/`). Do NOT expand. Display as: `→ SchemaName`.

### Empty module handling

If filtered paths is empty:
```
No endpoints found for module "<tag name>".
```
Continue processing remaining selected modules.

## Step 4: Generate Output

### Mode A: Markdown Display

For each module, generate this Markdown structure:

```markdown
# <Module Name>

> <Module Description>

**Endpoints:** <count>

---

## GET /api/pets — List all pets

**Description:** Returns a list of pets

**Operation ID:** `listPets`

### Request Parameters

| Name | In | Type | Required | Default | Description |
|------|----|------|----------|---------|-------------|
| limit | query | integer | No | 20 | Max items per page |

### Request Body

| Content-Type | Required | Schema |
|-------------|----------|--------|
| application/json | Yes | → PetRequest |

### Responses

| Status | Description | Schema |
|--------|-------------|--------|
| 200 | OK | → PetList |
| 400 | Bad Request | — |
| 500 | Internal Server Error | — |

---
```

**Rules:**
- Endpoints grouped by HTTP method: GET, POST, PUT, DELETE, PATCH
- Separator `---` between endpoints
- Parameters table: "None" row if empty
- Request body: skip section if no request body
- Schema references: `→ RefName` (arrow + last $ref segment)
- Sanitize filenames: replace `\/:*?"<>|` with `_`

### Mode A: Display Summary

After output:
```
## Parse Complete

- **Source:** <URL or file path>
- **Modules parsed:** <count>
- **Total endpoints:** <count>
- **Format:** Markdown (shown above)

To save for later reference, re-run with /doc:parse --save.
```

### Mode B: File Persistence

```bash
OUTPUT_DIR="./api-doc-parser/.output"
mkdir -p "$OUTPUT_DIR"

# For each module, write .md and .json files
MODULE_NAME_SAFE=$(echo "$MODULE_NAME" | sed 's/[\\/:*?"<>|]/_/g')

# Write Markdown
cat > "$OUTPUT_DIR/$MODULE_NAME_SAFE.md" << 'MARKDOWN_EOF'
<markdown content>
MARKDOWN_EOF

# Write JSON
cat > "$OUTPUT_DIR/$MODULE_NAME_SAFE.json" << 'JSON_EOF'
<json content>
JSON_EOF
```

### JSON structure

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
      "path": "/api/pets",
      "method": "GET",
      "summary": "List all pets",
      "description": "Returns a list of pets",
      "operationId": "listPets",
      "parameters": [
        {
          "name": "limit",
          "in": "query",
          "type": "integer",
          "required": false,
          "default": 20,
          "description": "Max items per page"
        }
      ],
      "requestBody": null,
      "responses": [
        {
          "status": "200",
          "description": "OK",
          "schemaRef": "PetList"
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
- `schemaRef` is last $ref segment, or `null`
- `parameters` is `[]` when none, not `null`
- Timestamp: `date -u +"%Y-%m-%dT%H:%M:%SZ"`
- OpenAPI version: `jq -r '.openapi // .swagger' "$SOURCE_PATH"`

### Mode B: File conflict resolution

If file already exists:
```bash
if [ -f "$OUTPUT_DIR/$MODULE_NAME_SAFE.md" ]; then
  TIMESTAMP=$(date +"%Y%m%d%H%M%S")
  MODULE_NAME_SAFE="${MODULE_NAME_SAFE}_$TIMESTAMP"
fi
```

### Mode B: Summary display

```
## Parse Complete — Files Saved

- **Source:** <URL or file path>
- **Modules parsed:** <count>
- **Total endpoints:** <count>

### Output Files

| File | Format | Size |
|------|--------|------|
| api-doc-parser/.output/pet.md | Markdown | 12.3 KB |
| api-doc-parser/.output/pet.json | JSON | 8.7 KB |
```

## Context Overflow Protection Rules

1. **Never read raw OpenAPI JSON into Agent context** — always use jq pipelines
2. **jq for all JSON filtering** — extract only needed data
3. **Large module (>30 endpoints) confirmation** — warn and confirm before full extraction
4. **File size check** — if >256KB, must use jq; never Read the file
5. **.md/.txt pagination** — use `offset` and `limit` params
```

- [ ] **Step 5: Create `skills/doc-help/SKILL.md`**

```markdown
---
name: doc-help
description: Display usage instructions for api-doc-parser — supported commands, input formats, output modes, and example usage.
---

# API Doc Parser Help

Parse OpenAPI 3.x / Swagger 2.0 API documentation. Extract endpoint details by module.

## Quick Start

```
/doc:fetch https://petstore3.swagger.io/api/v3/openapi.json
/doc:list
/doc:parse pet
```

## Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/doc:fetch <source>` | Fetch API docs from URL or local file | `/doc:fetch https://api.example.com/v3/api-docs` |
| `/doc:list [query]` | List modules; optional filter by keyword/index | `/doc:list 1,3` or `/doc:list pet` |
| `/doc:parse [query]` | Parse endpoints; optional keyword or mode flag | `/doc:parse --save` or `/doc:parse store` |
| `/doc:help` | Show this help | `/doc:help` |

## Input Formats

| Format | Example | Method |
|--------|---------|--------|
| URL (OpenAPI JSON) | `https://host/v3/api-docs` | curl fetch → jq parse |
| Local .json | `./docs/api.json` | jq direct parse |
| Local .md | `./docs/api.md` | LLM extraction (best-effort) |
| Local .txt | `./docs/api.txt` | LLM extraction (best-effort) |

## Output Modes

- **Mode A** (display): Results shown in conversation. No files written.
- **Mode B** (save): Files written to `api-doc-parser/.output/<module>.md` + `.json`

Override with flags: `--display` / `-a` (Mode A), `--save` / `-b` (Mode B).

## Module Selection

| Input | Example | Result |
|-------|---------|--------|
| By index | `1,3,6` | Modules at positions 1, 3, 6 |
| By keyword | `pet,store` | Fuzzy match against tag names |
| Mixed | `1,user` | Union of both, deduplicated |
| All | `all` | All modules |

## Requirements

- `jq` >= 1.6
- `curl` >= 7.0 (for URL sources)

## Examples

1. **Quick parse from URL:**
   ```
   /doc:fetch https://petstore3.swagger.io/api/v3/openapi.json
   /doc:list
   /doc:parse pet --display
   ```

2. **Parse local file:**
   ```
   /doc:fetch ./docs/openapi.json
   /doc:list user
   /doc:parse --save
   ```

3. **Batch export all modules:**
   ```
   /doc:fetch ./docs/openapi.json
   /doc:list all
   /doc:parse --save
   ```

4. **Direct keyword parse:**
   ```
   /doc:fetch https://api.example.com/v3/api-docs
   /doc:parse store
   ```

## Output Files (Mode B)

```
api-doc-parser/.output/
├── <module>.md    ← Markdown (human-readable)
└── <module>.json  ← JSON (machine-readable)
```

## Limitations

- `$ref` schema references show reference names only (not expanded)
- Non-OpenAPI formats (.md/.txt) use LLM extraction (less precise)
- Maximum file size: 50MB
```

- [ ] **Step 6: Commit**

```bash
git add skills/
git commit -m "feat: create 5 core sub-skills in skills/ directory

- using-api-doc-parser: meta-skill injected at session start
- doc-fetch: Phase 1 — fetch and validate API docs from URL or local file
- doc-list: Phase 2 — list and select API modules by tag
- doc-parse: Phases 3-5 — extract endpoints, generate Markdown + JSON output
- doc-help: display usage instructions and examples

Each sub-skill writes/reads shared state via /tmp/api-doc-parser/state.json
for independent invocation across phases."
```

---

### Task 3: Create platform skills proxies and command routing files — Claude Code

**Files:**
- Create: `.claude/skills/using-api-doc-parser/SKILL.md`
- Create: `.claude/skills/doc-fetch/SKILL.md`
- Create: `.claude/skills/doc-list/SKILL.md`
- Create: `.claude/skills/doc-parse/SKILL.md`
- Create: `.claude/skills/doc-help/SKILL.md`
- Create: `.claude/commands/doc/fetch.md`
- Create: `.claude/commands/doc/list.md`
- Create: `.claude/commands/doc/parse.md`
- Create: `.claude/commands/doc/help.md`

- [ ] **Step 1: Create skills proxy files**

Each proxy is a 1-line `@` reference pointing to the canonical skill in `skills/`:

```bash
mkdir -p .claude/skills/using-api-doc-parser
mkdir -p .claude/skills/doc-fetch
mkdir -p .claude/skills/doc-list
mkdir -p .claude/skills/doc-parse
mkdir -p .claude/skills/doc-help
```

Create `.claude/skills/using-api-doc-parser/SKILL.md`:
```markdown
@../../skills/using-api-doc-parser/SKILL.md
```

Create `.claude/skills/doc-fetch/SKILL.md`:
```markdown
@../../skills/doc-fetch/SKILL.md
```

Create `.claude/skills/doc-list/SKILL.md`:
```markdown
@../../skills/doc-list/SKILL.md
```

Create `.claude/skills/doc-parse/SKILL.md`:
```markdown
@../../skills/doc-parse/SKILL.md
```

Create `.claude/skills/doc-help/SKILL.md`:
```markdown
@../../skills/doc-help/SKILL.md
```

- [ ] **Step 2: Create command routing files**

```bash
mkdir -p .claude/commands/doc
```

Create `.claude/commands/doc/fetch.md`:
```markdown
---
name: "DOC: Fetch"
description: "Fetch API documentation from URL or local file"
argument-hint: "<URL or file path>"
---

Read the instructions in `skills/doc-fetch/SKILL.md` and execute them for: $ARGUMENTS
```

Create `.claude/commands/doc/list.md`:
```markdown
---
name: "DOC: List"
description: "List API modules (tags) from OpenAPI/Swagger document"
argument-hint: "[keywords|indices|all]"
---

Read the instructions in `skills/doc-list/SKILL.md` and execute them for: $ARGUMENTS
```

Create `.claude/commands/doc/parse.md`:
```markdown
---
name: "DOC: Parse"
description: "Extract endpoint details for selected API modules"
argument-hint: "[query] [--display|--save]"
---

Read the instructions in `skills/doc-parse/SKILL.md` and execute them for: $ARGUMENTS
```

Create `.claude/commands/doc/help.md`:
```markdown
---
name: "DOC: Help"
description: "Display api-doc-parser usage instructions and examples"
argument-hint: ""
---

Read the instructions in `skills/doc-help/SKILL.md` and execute them.
```

- [ ] **Step 3: Commit**

```bash
git add .claude/
git commit -m "feat: add Claude Code platform skills proxies and command routing

5 thin proxy SKILL.md files reference canonical skills/ via @ redirects.
4 command routing files (.claude/commands/doc/*.md) enable /doc:fetch,
/doc:list, /doc:parse, /doc:help slash commands in Claude Code."
```

---

### Task 4: Create platform skills proxies and command routing files — Cursor

**Files:**
- Create: `.cursor/skills/{5 sub-skills}/SKILL.md` (5 files, `@` proxies)
- Create: `.cursor/commands/doc/{fetch,list,parse,help}.md` (4 files)

- [ ] **Step 1: Create skills proxies**

```bash
mkdir -p .cursor/skills/using-api-doc-parser
mkdir -p .cursor/skills/doc-fetch
mkdir -p .cursor/skills/doc-list
mkdir -p .cursor/skills/doc-parse
mkdir -p .cursor/skills/doc-help
mkdir -p .cursor/commands/doc
```

Each `.cursor/skills/<name>/SKILL.md`:
```markdown
@../../skills/<name>/SKILL.md
```

(replace `<name>` with: `using-api-doc-parser`, `doc-fetch`, `doc-list`, `doc-parse`, `doc-help`)

- [ ] **Step 2: Create Cursor commands**

Cursor uses `-` naming for commands (no `:`):

Create `.cursor/commands/doc/fetch.md`:
```markdown
---
description: "Fetch API documentation from URL or local file"
argument-hint: "<URL or file path>"
---

Read the instructions in `skills/doc-fetch/SKILL.md` and execute them for the provided source.
```

Create `.cursor/commands/doc/list.md`:
```markdown
---
description: "List API modules (tags) from OpenAPI/Swagger document"
argument-hint: "[keywords|indices|all]"
---

Read the instructions in `skills/doc-list/SKILL.md` and execute them for the provided query.
```

Create `.cursor/commands/doc/parse.md`:
```markdown
---
description: "Extract endpoint details for selected API modules"
argument-hint: "[query] [--display|--save]"
---

Read the instructions in `skills/doc-parse/SKILL.md` and execute them for the provided query.
```

Create `.cursor/commands/doc/help.md`:
```markdown
---
description: "Display api-doc-parser usage instructions"
---

Read the instructions in `skills/doc-help/SKILL.md` and execute them.
```

- [ ] **Step 3: Commit**

```bash
git add .cursor/
git commit -m "feat: add Cursor platform skills proxies and command routing

5 thin proxy SKILL.md files reference canonical skills/ via @ redirects.
4 command routing files (.cursor/commands/doc/*.md) enable /doc-fetch,
/doc-list, /doc-parse, /doc-help slash commands in Cursor."
```

---

### Task 5: Create platform skills proxies and command routing files — Codex

**Files:**
- Create: `.codex/skills/{5 sub-skills}/SKILL.md` (5 files, `@` proxies)
- Create: `.codex/commands/doc/{fetch,list,parse,help}.md` (4 files)

- [ ] **Step 1: Create skills proxies and commands**

```bash
mkdir -p .codex/skills/using-api-doc-parser
mkdir -p .codex/skills/doc-fetch
mkdir -p .codex/skills/doc-list
mkdir -p .codex/skills/doc-parse
mkdir -p .codex/skills/doc-help
mkdir -p .codex/commands/doc
```

Proxies: Same `@../../skills/<name>/SKILL.md` pattern.

Commands: Same content as Claude Code format (`.md` with YAML frontmatter, `$ARGUMENTS` for arguments), placed at `.codex/commands/doc/fetch.md`, `list.md`, `parse.md`, `help.md`.

- [ ] **Step 2: Commit**

```bash
git add .codex/
git commit -m "feat: add Codex platform skills proxies and command routing"
```

---

### Task 6: Create platform skills proxies and command routing files — Gemini

**Files:**
- Create: `.gemini/skills/{5 sub-skills}/SKILL.md` (5 files, `@` proxies)
- Create: `.gemini/commands/doc/{fetch,list,parse,help}.toml` (4 files, **TOML format**)

- [ ] **Step 1: Create skills proxies**

```bash
mkdir -p .gemini/skills/using-api-doc-parser
mkdir -p .gemini/skills/doc-fetch
mkdir -p .gemini/skills/doc-list
mkdir -p .gemini/skills/doc-parse
mkdir -p .gemini/skills/doc-help
mkdir -p .gemini/commands/doc
```

Proxies: Same `@../../skills/<name>/SKILL.md` pattern.

- [ ] **Step 2: Create Gemini TOML commands**

Gemini CLI is the only platform using `.toml` format.

Create `.gemini/commands/doc/fetch.toml`:
```toml
description = "Fetch API documentation from URL or local file"

prompt = """
Read the instructions in skills/doc-fetch/SKILL.md and execute them for the provided URL or file path.
"""
```

Create `.gemini/commands/doc/list.toml`:
```toml
description = "List API modules (tags) from OpenAPI/Swagger document"

prompt = """
Read the instructions in skills/doc-list/SKILL.md and execute them for the provided query.
"""
```

Create `.gemini/commands/doc/parse.toml`:
```toml
description = "Extract endpoint details for selected API modules"

prompt = """
Read the instructions in skills/doc-parse/SKILL.md and execute them for the provided query.
"""
```

Create `.gemini/commands/doc/help.toml`:
```toml
description = "Display api-doc-parser usage instructions"

prompt = """
Read the instructions in skills/doc-help/SKILL.md and execute them.
"""
```

- [ ] **Step 3: Commit**

```bash
git add .gemini/
git commit -m "feat: add Gemini CLI platform skills proxies and TOML command routing

Gemini CLI uses .toml format for commands (only non-.md platform).
5 thin proxy SKILL.md files reference canonical skills/ via @ redirects."
```

---

### Task 7: Create platform skills proxies — Kimi and Trae (skills only, no commands)

**Files:**
- Create: `.kimi/skills/{5 sub-skills}/SKILL.md` (5 files, `@` proxies)
- Create: `.trae/skills/{5 sub-skills}/SKILL.md` (5 files, `@` proxies)

Kimi and Trae only support skills — no command routing files.

- [ ] **Step 1: Create Kimi skills proxies**

```bash
mkdir -p .kimi/skills/using-api-doc-parser
mkdir -p .kimi/skills/doc-fetch
mkdir -p .kimi/skills/doc-list
mkdir -p .kimi/skills/doc-parse
mkdir -p .kimi/skills/doc-help
```

Each proxy: `@../../skills/<name>/SKILL.md`

- [ ] **Step 2: Create Trae skills proxies**

```bash
mkdir -p .trae/skills/using-api-doc-parser
mkdir -p .trae/skills/doc-fetch
mkdir -p .trae/skills/doc-list
mkdir -p .trae/skills/doc-parse
mkdir -p .trae/skills/doc-help
```

Each proxy: `@../../skills/<name>/SKILL.md`

- [ ] **Step 3: Commit**

```bash
git add .kimi/ .trae/
git commit -m "feat: add Kimi and Trae platform skills proxies (no commands)

Kimi and Trae only support skills, not slash commands. 5 thin proxy
SKILL.md files per platform reference canonical skills/ via @ redirects."
```

---

### Task 8: Create platform skills proxies and command routing files — Qoder and OpenCode

**Files:**
- Create: `.qoder/skills/{5 sub-skills}/SKILL.md` (5 files, `@` proxies)
- Create: `.qoder/commands/doc/{fetch,list,parse,help}.md` (4 files)
- Create: `.opencode/skills/{5 sub-skills}/SKILL.md` (5 files, `@` proxies)
- Create: `.opencode/commands/doc-{fetch,list,parse,help}.md` (4 files, no `doc/` subdir — filenames include prefix per openspec precedent)

- [ ] **Step 1: Create Qoder proxies and commands**

```bash
mkdir -p .qoder/skills/using-api-doc-parser
mkdir -p .qoder/skills/doc-fetch
mkdir -p .qoder/skills/doc-list
mkdir -p .qoder/skills/doc-parse
mkdir -p .qoder/skills/doc-help
mkdir -p .qoder/commands/doc
```

Proxies: `@../../skills/<name>/SKILL.md`
Commands: Same Claude Code format (`.md` with YAML frontmatter, `$ARGUMENTS`).

- [ ] **Step 2: Create OpenCode proxies and commands**

```bash
mkdir -p .opencode/skills/using-api-doc-parser
mkdir -p .opencode/skills/doc-fetch
mkdir -p .opencode/skills/doc-list
mkdir -p .opencode/skills/doc-parse
mkdir -p .opencode/skills/doc-help
mkdir -p .opencode/commands
```

Proxies: `@../../skills/<name>/SKILL.md`
Commands: OpenCode uses `.opencode/commands/{cmd}.md` format (no `doc/` subdirectory per openspec precedent).

Create `.opencode/commands/doc-fetch.md`:
```markdown
---
name: "DOC: Fetch"
description: "Fetch API documentation from URL or local file"
argument-hint: "<URL or file path>"
---

Read the instructions in `skills/doc-fetch/SKILL.md` and execute them for: $ARGUMENTS
```

Create `.opencode/commands/doc-list.md`:
```markdown
---
name: "DOC: List"
description: "List API modules from OpenAPI/Swagger document"
argument-hint: "[keywords|indices|all]"
---

Read the instructions in `skills/doc-list/SKILL.md` and execute them for: $ARGUMENTS
```

Create `.opencode/commands/doc-parse.md`:
```markdown
---
name: "DOC: Parse"
description: "Extract endpoint details for selected API modules"
argument-hint: "[query] [--display|--save]"
---

Read the instructions in `skills/doc-parse/SKILL.md` and execute them for: $ARGUMENTS
```

Create `.opencode/commands/doc-help.md`:
```markdown
---
name: "DOC: Help"
description: "Display api-doc-parser usage instructions"
---

Read the instructions in `skills/doc-help/SKILL.md` and execute them.
```

- [ ] **Step 3: Commit**

```bash
git add .qoder/ .opencode/
git commit -m "feat: add Qoder and OpenCode platform skills proxies and command routing"
```

---

### Task 9: Create GitHub Copilot platform files

**Files:**
- Create: `.github/skills/{5 sub-skills}/SKILL.md` (5 files, `@` proxies)
- Create: `.github/prompts/doc-fetch.prompt.md`
- Create: `.github/prompts/doc-list.prompt.md`
- Create: `.github/prompts/doc-parse.prompt.md`
- Create: `.github/prompts/doc-help.prompt.md`

- [ ] **Step 1: Create skills proxies**

```bash
mkdir -p .github/skills/using-api-doc-parser
mkdir -p .github/skills/doc-fetch
mkdir -p .github/skills/doc-list
mkdir -p .github/skills/doc-parse
mkdir -p .github/skills/doc-help
mkdir -p .github/prompts
```

Proxies: `@../../skills/<name>/SKILL.md`

- [ ] **Step 2: Create Copilot prompt files**

GitHub Copilot uses `.prompt.md` format with `${input:name}` parameter syntax.

Create `.github/prompts/doc-fetch.prompt.md`:
```markdown
---
description: "Fetch API documentation from URL or local file"
---

Read the instructions in `skills/doc-fetch/SKILL.md` and execute them for the provided source.
```

Create `.github/prompts/doc-list.prompt.md`:
```markdown
---
description: "List API modules (tags) from OpenAPI/Swagger document"
---

Read the instructions in `skills/doc-list/SKILL.md` and execute them for the provided query.
```

Create `.github/prompts/doc-parse.prompt.md`:
```markdown
---
description: "Extract endpoint details for selected API modules"
---

Read the instructions in `skills/doc-parse/SKILL.md` and execute them for the provided query.
```

Create `.github/prompts/doc-help.prompt.md`:
```markdown
---
description: "Display api-doc-parser usage instructions"
---

Read the instructions in `skills/doc-help/SKILL.md` and execute them.
```

- [ ] **Step 3: Commit**

```bash
git add .github/
git commit -m "feat: add GitHub Copilot platform skills proxies and .prompt.md routing

GitHub Copilot uses .prompt.md format for prompts. 5 thin proxy SKILL.md
files reference canonical skills/ via @ redirects. 4 prompt files enable
/doc-fetch, /doc-list, /doc-parse, /doc-help in GitHub Copilot."
```

---

### Task 10: Create Plugin Manifests

**Files:**
- Create: `.claude-plugin/plugin.json`
- Create: `.claude-plugin/marketplace.json`
- Create: `.cursor-plugin/plugin.json`
- Create: `.codex-plugin/plugin.json`

- [ ] **Step 1: Create `.claude-plugin/plugin.json`**

```bash
mkdir -p .claude-plugin
```

```json
{
  "$schema": "https://anthropic.com/claude-code/plugin.schema.json",
  "name": "api-doc-parser",
  "version": "2.0.0",
  "displayName": "API Doc Parser",
  "description": "Parse OpenAPI 3.x / Swagger 2.0 API documentation. Extract endpoint details by module.",
  "author": { "name": "summer-bwbb" },
  "license": "MIT",
  "keywords": ["openapi", "swagger", "api-docs", "documentation"],
  "category": "developer-tools",
  "skills": ["./skills/"],
  "commands": ["./commands/"]
}
```

- [ ] **Step 2: Create `.claude-plugin/marketplace.json`**

```json
{
  "name": "API Doc Parser",
  "description": "Parse OpenAPI 3.x / Swagger 2.0 API documentation. Extract endpoint details by module (tag) with dual-format output: Markdown (human-readable) and JSON (machine-readable). Supports URL fetch and local file import.",
  "owner": "summer-bwbb",
  "plugins": [
    {
      "name": "api-doc-parser",
      "version": "2.0.0",
      "description": "Parse OpenAPI 3.x / Swagger 2.0 API documentation by module.",
      "category": "developer-tools"
    }
  ]
}
```

- [ ] **Step 3: Create `.cursor-plugin/plugin.json`**

```bash
mkdir -p .cursor-plugin
```

```json
{
  "name": "api-doc-parser",
  "version": "2.0.0",
  "displayName": "API Doc Parser",
  "description": "Parse OpenAPI 3.x / Swagger 2.0 API documentation. Extract endpoint details by module.",
  "author": { "name": "summer-bwbb" },
  "license": "MIT",
  "keywords": ["openapi", "swagger", "api-docs", "documentation"],
  "category": "developer-tools",
  "skills": ["./skills/"],
  "commands": ["./commands/"]
}
```

- [ ] **Step 4: Create `.codex-plugin/plugin.json`**

```bash
mkdir -p .codex-plugin
```

```json
{
  "name": "api-doc-parser",
  "version": "2.0.0",
  "displayName": "API Doc Parser",
  "description": "Parse OpenAPI 3.x / Swagger 2.0 API documentation. Extract endpoint details by module.",
  "author": { "name": "summer-bwbb" },
  "license": "MIT",
  "keywords": ["openapi", "swagger", "api-docs", "documentation"],
  "category": "developer-tools",
  "skills": ["./skills/"],
  "commands": ["./commands/"]
}
```

- [ ] **Step 5: Commit**

```bash
git add .claude-plugin/ .cursor-plugin/ .codex-plugin/
git commit -m "feat: add plugin manifests for Claude Code, Cursor, and Codex

.claude-plugin/plugin.json + marketplace.json for Claude Code marketplace
.cursor-plugin/plugin.json for Cursor plugin installation
.codex-plugin/plugin.json for Codex plugin installation

All manifests reference skills/ and commands/ directories. Version 2.0.0."
```

---

### Task 11: Create NPM Packaging (package.json + scripts)

**Files:**
- Create: `package.json`
- Create: `scripts/postinstall.js`
- Create: `scripts/preuninstall.js`
- Create: `scripts/check-deps.sh`

- [ ] **Step 1: Create `package.json`**

```json
{
  "name": "api-doc-parser-skill",
  "version": "2.0.0",
  "description": "Parse OpenAPI 3.x / Swagger 2.0 API documentation. Extract endpoint details by module (tag) with dual-format output (Markdown + JSON). 5 sub-skills, 9-platform support.",
  "author": {
    "name": "summer-bwbb"
  },
  "license": "MIT",
  "keywords": [
    "openapi",
    "swagger",
    "api-docs",
    "documentation",
    "claude-code",
    "agent-skill",
    "api-parser"
  ],
  "files": [
    "skills/",
    "hooks/",
    "scripts/",
    "docs/",
    ".claude/",
    ".cursor/",
    ".codex/",
    ".gemini/",
    ".kimi/",
    ".qoder/",
    ".trae/",
    ".opencode/",
    ".github/",
    ".claude-plugin/",
    ".cursor-plugin/",
    ".codex-plugin/",
    "SKILL.md",
    "metadata.json",
    "README.md",
    "GEMINI.md",
    "AGENTS.md",
    "gemini-extension.json"
  ],
  "scripts": {
    "postinstall": "node scripts/postinstall.js",
    "preuninstall": "node scripts/preuninstall.js"
  }
}
```

- [ ] **Step 2: Create `scripts/postinstall.js`**

```javascript
#!/usr/bin/env node

/**
 * postinstall.js — Register api-doc-parser skills with detected AI coding assistants.
 *
 * Detects if Claude Code, Cursor, or Codex are installed by checking known
 * config directories. For each detected assistant, copies/links the skills
 * and commands into the appropriate directory.
 *
 * Skips registration if a plugin is already installed (avoids double-registration).
 */

const fs = require('fs');
const path = require('path');
const os = require('os');

const SKILL_NAME = 'api-doc-parser';
const VERSION = '2.0.0';

// Skills to register
const SKILLS = [
  'using-api-doc-parser',
  'doc-fetch',
  'doc-list',
  'doc-parse',
  'doc-help',
];

// Commands to register (per platform)
const COMMANDS = ['fetch', 'list', 'parse', 'help'];

// Platform config paths (relative to HOME)
const PLATFORM_DIRS = {
  'Claude Code': '.claude',
  'Cursor': '.cursor',
  'Codex': '.codex',
};

// Dependency requirements
const DEPS = [
  { name: 'jq', minVersion: '1.6', install: { darwin: 'brew install jq', linux: 'sudo apt install jq', win32: 'choco install jq' } },
  { name: 'curl', minVersion: '7.0', install: { darwin: 'brew install curl', linux: 'sudo apt install curl', win32: 'choco install curl' } },
];

/**
 * Get the package root directory (where skills/, commands/, etc. live).
 */
function getPackageRoot() {
  // When installed via npm, __dirname will be <node_modules>/api-doc-parser-skill/scripts/
  return path.resolve(__dirname, '..');
}

/**
 * Check if a command is available on PATH.
 */
function which(cmd) {
  try {
    const result = require('child_process').execSync(
      process.platform === 'win32' ? `where ${cmd}` : `which ${cmd}`,
      { encoding: 'utf8', stdio: ['pipe', 'pipe', 'pipe'] }
    );
    return result.trim().split('\n')[0];
  } catch {
    return null;
  }
}

/**
 * Get version string from a command.
 */
function getVersion(cmd, versionFlag) {
  try {
    const result = require('child_process').execSync(
      `${cmd} ${versionFlag}`,
      { encoding: 'utf8', stdio: ['pipe', 'pipe', 'pipe'] }
    );
    const match = result.match(/(\d+\.\d+(\.\d+)?)/);
    return match ? match[1] : null;
  } catch {
    return null;
  }
}

/**
 * Compare two semver strings. Returns -1 if a < b, 0 if equal, 1 if a > b.
 */
function compareVersions(a, b) {
  const pa = a.split('.').map(Number);
  const pb = b.split('.').map(Number);
  for (let i = 0; i < Math.max(pa.length, pb.length); i++) {
    const va = pa[i] || 0;
    const vb = pb[i] || 0;
    if (va < vb) return -1;
    if (va > vb) return 1;
  }
  return 0;
}

/**
 * Check if the plugin is already installed (e.g., via claude plugins install).
 */
function isPluginInstalled(platformDir) {
  // Look for a plugin manifest or installation marker
  const pkgRoot = getPackageRoot();
  // Plugin-installed packages live in the assistant's plugins directory
  // If we're running from node_modules, this is an NPM install, not a plugin install
  const isNpmInstall = pkgRoot.includes('node_modules');
  return !isNpmInstall; // If we're NOT in node_modules, assume plugin-installed
}

/**
 * Check dependencies and warn if missing or outdated.
 */
function checkDependencies() {
  let allOk = true;

  for (const dep of DEPS) {
    const installedPath = which(dep.name);
    if (!installedPath) {
      console.warn(`\x1b[33m⚠️  ${dep.name} not found. Install: ${dep.install[process.platform] || dep.install.linux}\x1b[0m`);
      allOk = false;
      continue;
    }

    const version = getVersion(dep.name, '--version');
    if (version && compareVersions(version, dep.minVersion) < 0) {
      console.warn(`\x1b[33m⚠️  ${dep.name} ${version} < ${dep.minVersion}. Please upgrade.\x1b[0m`);
      allOk = false;
    }
  }

  if (allOk) {
    console.log('\x1b[32m✓ All dependencies available\x1b[0m');
  }
}

/**
 * Copy directory recursively.
 */
function copyDir(src, dest) {
  if (!fs.existsSync(src)) return;

  fs.mkdirSync(dest, { recursive: true });

  const entries = fs.readdirSync(src, { withFileTypes: true });
  for (const entry of entries) {
    const srcPath = path.join(src, entry.name);
    const destPath = path.join(dest, entry.name);
    if (entry.isDirectory()) {
      copyDir(srcPath, destPath);
    } else {
      fs.copyFileSync(srcPath, destPath);
    }
  }
}

/**
 * Register skills to a platform's config directory.
 */
function registerToPlatform(platformName, platformDir) {
  const homeDir = os.homedir();
  const configPath = path.join(homeDir, platformDir);

  if (!fs.existsSync(configPath)) {
    console.log(`  ${platformName} config dir not found at ${configPath}, skipping.`);
    return false;
  }

  // Check for existing plugin registration
  const pluginSkillsPath = path.join(configPath, 'skills');
  const alreadyRegistered = SKILLS.every(skill =>
    fs.existsSync(path.join(pluginSkillsPath, skill, 'SKILL.md'))
  );

  if (alreadyRegistered) {
    console.log(`  ${platformName}: Plugin already registered, skipping NPM registration.`);
    return false;
  }

  // Register skills
  const pkgRoot = getPackageRoot();
  const skillsSrc = path.join(pkgRoot, 'skills');

  if (!fs.existsSync(skillsSrc)) {
    console.warn(`  Skills source not found at ${skillsSrc}, skipping.`);
    return false;
  }

  // Register commands if the platform supports them
  let commandsRegistered = 0;
  let skillsRegistered = 0;

  try {
    const targetSkillsDir = path.join(configPath, 'skills');
    fs.mkdirSync(targetSkillsDir, { recursive: true });

    for (const skill of SKILLS) {
      const srcSkillDir = path.join(skillsSrc, skill);
      const destSkillDir = path.join(targetSkillsDir, skill);

      if (fs.existsSync(srcSkillDir)) {
        copyDir(srcSkillDir, destSkillDir);
        skillsRegistered++;
      }
    }

    // Commands
    const commandsDest = path.join(configPath, 'commands', 'doc');
    const commandsSrc = path.join(pkgRoot, platformDir, 'commands', 'doc');
    if (fs.existsSync(commandsSrc)) {
      fs.mkdirSync(commandsDest, { recursive: true });
      copyDir(commandsSrc, commandsDest);
      commandsRegistered = fs.readdirSync(commandsDest).length;
    }
  } catch (err) {
    console.warn(`  Error registering to ${platformName}: ${err.message}`);
    return false;
  }

  console.log(`  ${platformName}: Registered ${skillsRegistered} skills, ${commandsRegistered} commands`);
  return true;
}

/**
 * Main entry point.
 */
function main() {
  console.log(`\napi-doc-parser v${VERSION} — postinstall\n`);

  // Skip if this is a plugin install (not NPM)
  if (isPluginInstalled()) {
    console.log('Plugin installation detected. NPM registration skipped.');
    console.log('Skills and commands are managed by the plugin system.\n');
    return;
  }

  // Check dependencies
  checkDependencies();

  // Detect and register to platforms
  console.log('\nDetecting AI coding assistants...');
  let registeredCount = 0;
  for (const [platformName, platformDir] of Object.entries(PLATFORM_DIRS)) {
    if (registerToPlatform(platformName, platformDir)) {
      registeredCount++;
    }
  }

  if (registeredCount === 0) {
    console.log('\nNo supported AI coding assistants detected.');
    console.log('For manual installation, see docs/INSTALL.md\n');
  } else {
    console.log(`\n\x1b[32m✓ Registered to ${registeredCount} platform(s)\x1b[0m`);
    console.log('Run /doc:help to verify installation.\n');
  }
}

main();
```

- [ ] **Step 3: Create `scripts/preuninstall.js`**

```javascript
#!/usr/bin/env node

/**
 * preuninstall.js — Remove api-doc-parser skills from AI coding assistant config dirs.
 *
 * Cleans up skills and commands that were registered by postinstall.js.
 * Only removes files that match our skill names — never touches user config.
 */

const fs = require('fs');
const path = require('path');
const os = require('os');

const SKILLS = [
  'using-api-doc-parser',
  'doc-fetch',
  'doc-list',
  'doc-parse',
  'doc-help',
];

const COMMANDS = ['fetch', 'list', 'parse', 'help'];

const PLATFORM_DIRS = {
  'Claude Code': '.claude',
  'Cursor': '.cursor',
  'Codex': '.codex',
};

function removeDir(dir) {
  if (!fs.existsSync(dir)) return false;
  try {
    fs.rmSync(dir, { recursive: true, force: true });
    return true;
  } catch {
    return false;
  }
}

function unregisterFromPlatform(platformName, platformDir) {
  const homeDir = os.homedir();
  const configPath = path.join(homeDir, platformDir);

  if (!fs.existsSync(configPath)) {
    return false;
  }

  let cleaned = 0;

  // Remove registered skills
  const skillsDir = path.join(configPath, 'skills');
  if (fs.existsSync(skillsDir)) {
    for (const skill of SKILLS) {
      const skillDir = path.join(skillsDir, skill);
      if (removeDir(skillDir)) cleaned++;
    }
  }

  // Remove registered commands
  const commandsDir = path.join(configPath, 'commands', 'doc');
  if (fs.existsSync(commandsDir)) {
    for (const cmd of COMMANDS) {
      // Try .md and .toml
      for (const ext of ['.md', '.toml']) {
        const cmdFile = path.join(commandsDir, cmd + ext);
        try {
          if (fs.existsSync(cmdFile)) {
            fs.unlinkSync(cmdFile);
            cleaned++;
          }
        } catch { /* ignore */ }
      }
    }

    // Remove empty commands/doc directory
    try {
      const remaining = fs.readdirSync(commandsDir);
      if (remaining.length === 0) {
        fs.rmdirSync(commandsDir);
        // Also remove parent commands dir if empty
        const parentDir = path.join(configPath, 'commands');
        const parentRemaining = fs.readdirSync(parentDir);
        if (parentRemaining.length === 0) {
          fs.rmdirSync(parentDir);
        }
      }
    } catch { /* ignore */ }
  }

  if (cleaned > 0) {
    console.log(`  ${platformName}: Removed ${cleaned} registered items.`);
  }
  return cleaned > 0;
}

function main() {
  console.log('\napi-doc-parser — preuninstall\n');

  let totalCleaned = 0;
  for (const [platformName, platformDir] of Object.entries(PLATFORM_DIRS)) {
    if (unregisterFromPlatform(platformName, platformDir)) {
      totalCleaned++;
    }
  }

  if (totalCleaned === 0) {
    console.log('No registered skills found to clean up.\n');
  } else {
    console.log(`\n\x1b[32m✓ Cleaned up from ${totalCleaned} platform(s)\x1b[0m\n`);
  }
}

main();
```

- [ ] **Step 4: Create `scripts/check-deps.sh`**

```bash
#!/bin/sh
# check-deps.sh — Verify jq and curl are installed with acceptable versions.
# Used by both install-time checks and runtime checks.

set -e

DEPS_OK=true

# Check jq
if ! command -v jq > /dev/null 2>&1; then
  echo "ERROR: jq is not installed."
  case "$(uname -s)" in
    Darwin*) echo "  Install: brew install jq" ;;
    Linux*)  echo "  Install: sudo apt install jq" ;;
    MINGW*|MSYS*|CYGWIN*) echo "  Install: choco install jq" ;;
  esac
  DEPS_OK=false
else
  JQ_VER=$(jq --version 2>&1 | grep -oP '\d+\.\d+' | head -1 || echo "0.0")
  if [ "$(printf '%s\n' "1.6" "$JQ_VER" | sort -V | head -1)" != "1.6" ]; then
    echo "ERROR: jq >= 1.6 required, found $JQ_VER"
    DEPS_OK=false
  else
    echo "✓ jq $JQ_VER"
  fi
fi

# Check curl
if ! command -v curl > /dev/null 2>&1; then
  echo "ERROR: curl is not installed."
  case "$(uname -s)" in
    Darwin*) echo "  Install: brew install curl" ;;
    Linux*)  echo "  Install: sudo apt install curl" ;;
    MINGW*|MSYS*|CYGWIN*) echo "  Install: choco install curl" ;;
  esac
  DEPS_OK=false
else
  CURL_VER=$(curl --version 2>&1 | head -1 | grep -oP '\d+\.\d+' | head -1 || echo "0.0")
  if [ "$(printf '%s\n' "7.0" "$CURL_VER" | sort -V | head -1)" != "7.0" ]; then
    echo "ERROR: curl >= 7.0 required, found $CURL_VER"
    DEPS_OK=false
  else
    echo "✓ curl $CURL_VER"
  fi
fi

if [ "$DEPS_OK" = false ]; then
  exit 1
fi

echo "All dependencies OK."
```

- [ ] **Step 5: Commit**

```bash
git add package.json scripts/
git commit -m "feat: add NPM packaging with postinstall/preuninstall scripts

package.json: name api-doc-parser-skill, version 2.0.0, files[] for npm publish
scripts/postinstall.js: detects AI assistants, registers skills/commands globally
scripts/preuninstall.js: cleans up registered skills on uninstall
scripts/check-deps.sh: cross-platform jq/curl version detection

NPM global install (npm install -g) auto-registers to all detected platforms."
```

---

### Task 12: Create SessionStart Hooks

**Files:**
- Create: `hooks/hooks.json`
- Create: `hooks/session-start.sh`

- [ ] **Step 1: Create `hooks/hooks.json`**

```bash
mkdir -p hooks
```

```json
{
  "SessionStart": [
    {
      "matcher": "startup|clear|compact",
      "hooks": [
        {
          "type": "command",
          "command": "bash \"$(dirname \"$0\")/session-start.sh\""
        }
      ]
    }
  ]
}
```

- [ ] **Step 2: Create `hooks/session-start.sh`**

```bash
#!/bin/sh
# session-start.sh — Injects using-api-doc-parser meta-skill at session start.
# Executed by hooks.json on startup, clear, and compact events.
# Claude Code captures stdout and injects it into the agent system prompt.

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# Check that using-api-doc-parser exists
META_SKILL="$SKILL_DIR/skills/using-api-doc-parser/SKILL.md"
if [ -f "$META_SKILL" ]; then
  cat "$META_SKILL"
else
  echo "# API Doc Parser"
  echo ""
  echo "api-doc-parser v2 is installed but could not find the using-api-doc-parser skill."
  echo "Please check your installation: docs/INSTALL.md"
fi
```

- [ ] **Step 3: Commit**

```bash
git add hooks/
git commit -m "feat: add SessionStart hook to auto-inject using-api-doc-parser meta-skill

hooks/hooks.json: fires on startup|clear|compact, executes session-start.sh
hooks/session-start.sh: reads and outputs using-api-doc-parser/SKILL.md

This mirrors the superpowers SessionStart mechanism — agent context is
automatically seeded with instructions for discovering doc-* sub-skills."
```

---

### Task 13: Create Documentation (INSTALL, USAGE, CHANGELOG)

**Files:**
- Create: `docs/INSTALL.md`
- Create: `docs/USAGE.md`
- Create: `docs/CHANGELOG.md`

- [ ] **Step 1: Create `docs/INSTALL.md`**

```bash
mkdir -p docs
```

```markdown
# API Doc Parser — Installation Guide

Three installation methods, pick the one that fits your workflow.

## Prerequisites

- **jq** ≥ 1.6 — JSON processor
- **curl** ≥ 7.0 — HTTP client (for URL-based sources only)

Check: `bash scripts/check-deps.sh`

## Method 1: Claude Code Plugin (Recommended)

```bash
# Install globally
claude plugins install api-doc-parser

# Verify
echo "/doc:help" | claude
```

### Update

```bash
claude plugins update api-doc-parser
```

### Uninstall

```bash
claude plugins uninstall api-doc-parser
```

## Method 2: NPM Global Install

```bash
# Install globally
npm install -g api-doc-parser-skill

# The postinstall script auto-detects your AI assistants and registers skills
```

### Update

```bash
npm update -g api-doc-parser-skill
```

### Uninstall

```bash
npm uninstall -g api-doc-parser-skill
# preuninstall script auto-cleans registered skills
```

## Method 3: Manual Install

### Global (all projects)

```bash
git clone https://github.com/summer-bwbb/api-doc-parser.git ~/.claude/plugins/api-doc-parser

# Add to .claude/settings.json (global):
{
  "skills": ["~/.claude/plugins/api-doc-parser/skills/"],
  "commands": ["~/.claude/plugins/api-doc-parser/commands/"]
}
```

### Per-project

```bash
# Copy into project
cp -r api-doc-parser/skills/ .claude/skills/
cp -r api-doc-parser/.claude/commands/ .claude/commands/

# OR add reference in .claude/settings.json:
{
  "requiredPlugins": ["api-doc-parser"]
}
```

## Verification

After installation, run:

```
/doc:help
```

Should display the help screen with command reference.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `/doc:fetch` not found | Check commands are in `.claude/commands/doc/` |
| Skills not loading | Verify `skills/` directory exists in plugin path |
| jq not found | Install jq: `brew install jq` (macOS), `sudo apt install jq` (Linux), `choco install jq` (Windows) |
| curl not found | Install curl: `brew install curl` (macOS), `sudo apt install curl` (Linux) |
| State file errors | Delete `/tmp/api-doc-parser/state.json` and re-run `/doc:fetch` |
| Permission denied | Check write permissions on `/tmp` (Unix) or `%TEMP%` (Windows) |
```

- [ ] **Step 2: Create `docs/USAGE.md`**

```markdown
# API Doc Parser — Usage Guide

## Quick Start (3 Steps)

```
/doc:fetch https://petstore3.swagger.io/api/v3/openapi.json
/doc:list
/doc:parse pet
```

That's it! Endpoint details are displayed in your conversation.

## Command Reference

### `/doc:fetch <source>`

Fetch API documentation from a URL or local file.

| Argument | Type | Example |
|----------|------|---------|
| URL | `https://...` | `/doc:fetch https://api.example.com/v3/api-docs` |
| Local JSON | `.json` | `/doc:fetch ./docs/openapi.json` |
| Local Markdown | `.md` | `/doc:fetch ./docs/api.md` |
| Local Text | `.txt` | `/doc:fetch ./docs/api.txt` |

**What happens:** The source is fetched/validated and metadata is saved to shared state. Ready for `/doc:list`.

### `/doc:list [query]`

List and select API modules (tags).

| Argument | Example | Result |
|----------|---------|--------|
| (none) | `/doc:list` | Show all modules in numbered table |
| Indices | `/doc:list 1,3,6` | Select modules at positions 1, 3, 6 |
| Keywords | `/doc:list pet,store` | Fuzzy match against tag names |
| Mixed | `/doc:list 1,user` | Union of both, deduplicated |
| All | `/doc:list all` | Select all modules |

**What happens:** Module selection is saved to shared state. Ready for `/doc:parse`.

### `/doc:parse [query] [options]`

Extract full endpoint details for selected modules.

| Argument | Example | Result |
|----------|---------|--------|
| (none) | `/doc:parse` | Parse all selected modules |
| Keyword | `/doc:parse pet` | Auto-select and parse matching modules |
| Mode A | `/doc:parse --display` | Display in conversation (no files) |
| Mode B | `/doc:parse --save` | Save `.md` + `.json` to `api-doc-parser/.output/` |

**What happens:** Endpoint details are extracted via jq, formatted, and output per the selected mode.

### `/doc:help`

Display this usage reference.

## Output Modes

### Mode A: Display (default)

Results shown directly in the conversation. Good for quick lookups.

```
/doc:parse --display
# or short form:
/doc:parse -a
```

### Mode B: Save Files

Results saved to `api-doc-parser/.output/<module>.md` + `.json`.

```
/doc:parse --save
# or short form:
/doc:parse -b
```

## Scenario Examples

### 1. Remote URL, Quick Browse

```
/doc:fetch https://petstore3.swagger.io/api/v3/openapi.json
/doc:list
/doc:parse pet --display
```

### 2. Local File, Save All

```
/doc:fetch ./docs/api-docs.json
/doc:list all
/doc:parse --save
```

### 3. Quick Keyword Parse (bypass listing)

```
/doc:fetch https://api.example.com/v3/api-docs
/doc:parse user
```

### 4. CI/CD Batch Export

```bash
# In a script:
echo "/doc:fetch ./openapi.json" | claude
echo "/doc:list all" | claude
echo "/doc:parse --save" | claude
# Output: api-doc-parser/.output/*.md + *.json
```

## Output File Structure (Mode B)

```
api-doc-parser/.output/
├── pet.md           ← Markdown, human-readable
├── pet.json         ← JSON, machine-readable
├── store.md
└── store.json
```

## Natural Language Usage

You don't need slash commands. The agent also recognizes:

| You say | Agent does |
|---------|------------|
| "Parse API docs from https://..." | Fetches, lists, asks for module selection |
| "Extract endpoints for user module" | Lists modules, parses matching ones |
| "Show me the API structure" | Lists all modules |
| "What are the store endpoints?" | Lists → selects store → parses |

## FAQ

**Q: Can I reuse results from a previous session?**
A: Yes. The project-level state at `.api-doc-parser/state.json` and output files at `api-doc-parser/.output/` persist across sessions.

**Q: What happens if I fetch a new source?**
A: The previous state is cleared. Module selections are reset. This prevents stale selections from one source applying to another.

**Q: How do I handle very large API docs (>10MB)?**
A: A warning is shown. You can still proceed, but parsing may take longer. For docs >50MB, processing is refused — consider using a smaller subset.

**Q: Can I use this in Cursor / Codex / Gemini / Copilot?**
A: Yes! All 9 platforms have command routing. Command syntax varies: `/doc:parse` (Claude Code), `/doc-parse` (Cursor/Codex), `doc-parse` (Gemini/Copilot).

**Q: Are `$ref` schemas expanded?**
A: No. Only the reference name is shown (e.g., `→ PetSchema`). This follows v1 behavior. Use Swagger UI or the original spec for full schema details.
```

- [ ] **Step 3: Create `docs/CHANGELOG.md`**

```markdown
# Changelog

All notable changes to api-doc-parser.

## [2.0.0] — 2026-06-15

### Added
- **Sub-skill architecture:** Split monolithic SKILL.md into 5 independent sub-skills:
  - `using-api-doc-parser` — Meta-instructions injected at session start
  - `doc-fetch` — Fetch and validate API docs from URL or local file
  - `doc-list` — List and select API modules by tag
  - `doc-parse` — Extract endpoints, generate Markdown + JSON output
  - `doc-help` — Display usage instructions and examples
- **9-platform command routing:** Slash commands for Claude Code, Cursor, Codex, Gemini, Kimi, Qoder, Trae, OpenCode, GitHub Copilot
- **Plugin packaging:** Claude Code Plugin (.claude-plugin/), Cursor Plugin (.cursor-plugin/), Codex Plugin (.codex-plugin/)
- **NPM packaging:** package.json with postinstall/preuninstall scripts for global install
- **SessionStart hook:** Auto-injects using-api-doc-parser meta-instructions at session start
- **Cross-phase state:** `/tmp/api-doc-parser/state.json` enables independent invocation of fetch → list → parse
- **Output mode parameter override:** `--display`/`-a` and `--save`/`-b` flags on doc-parse
- **Documentation:** docs/INSTALL.md, docs/USAGE.md, docs/CHANGELOG.md
- **Windows support:** Cross-platform temp directory detection (TMPDIR/TEMP/TMP)

### Changed
- **SKILL.md:** Preserved as backward-compatible entry point with sub-skill navigation header
- **metadata.json:** Version bumped to 2.0.0
- **README.md:** Updated with v2 architecture, sub-skills, and install methods
- **Output mode:** Now persisted in state.json, with command-line overrides

### Removed
- Cleaned up openspec-* skill files from all platform directories (unrelated to api-doc-parser)

### Fixed
- Dependency detection now checks both jq and curl versions at install time
- State file JSON validation prevents crashes on corrupted state

## [1.0.0] — 2026-06-15

### Added
- Initial release
- Single SKILL.md with 5-phase pipeline: Source Input → Module Listing → Endpoint Extraction → Output Generation → Output Mode
- Dual input source: URL (curl) and local file (.json/.md/.txt)
- jq-based context overflow protection
- Markdown (Mode A) and JSON file (Mode B) output
- $ref schema reference recording
- Module selection by index, keyword, mixed, and all
- Context overflow prevention rules
```

- [ ] **Step 4: Commit**

```bash
git add docs/
git commit -m "docs: add INSTALL.md, USAGE.md, and CHANGELOG.md

INSTALL.md: three installation methods (Plugin/NPM/Manual) with troubleshooting
USAGE.md: quick start, command reference, 4 scenario examples, FAQ
CHANGELOG.md: v1.0.0 baseline and v2.0.0 upgrade notes"
```

---

### Task 14: Update Root Files for Backward Compatibility

**Files:**
- Modify: `SKILL.md` — add sub-skill navigation at top, preserve v1 logic
- Modify: `metadata.json` — version 1.0.0 → 2.0.0
- Modify: `README.md` — v2 architecture documentation
- Create: `GEMINI.md`
- Create: `AGENTS.md`
- Create: `gemini-extension.json`

- [ ] **Step 1: Update `SKILL.md` — add navigation header, preserve v1 content**

Prepend this to the existing SKILL.md:

```markdown
<!--
  api-doc-parser v2.0.0
  This file is the backward-compatible natural language entry point.
  For fine-grained control, use slash commands:
    /doc:fetch <URL|file>  — Fetch and validate API documentation
    /doc:list [query]      — List and select API modules
    /doc:parse [query]     — Extract endpoint details
    /doc:help              — Display usage instructions
  
  The v1 5-phase pipeline below is fully preserved. Each phase can also
  be executed independently via the corresponding doc-* sub-skill.
-->
```

The rest of SKILL.md remains unchanged (all Phase 1-5 content).

- [ ] **Step 2: Update `metadata.json`**

Change version from `"1.0.0"` to `"2.0.0"` and update description:

```json
{
  "name": "api-doc-parser",
  "version": "2.0.0",
  "description": "Parse OpenAPI 3.x / Swagger 2.0 API documentation by module (tag), extract endpoint details, and output Markdown + structured JSON. Supports URL fetch and local file import with built-in context overflow protection via jq pipelines. v2 adds: 5 sub-skills, 9-platform slash commands, Plugin/NPM/Manual install, SessionStart hook, and cross-phase state persistence.",
  "author": "summer-bwbb",
  "date": "2026-06-15",
  "references": [
    "https://swagger.io/specification/",
    "https://spec.openapis.org/oas/v3.1.0",
    "https://springdoc.org/",
    "https://jqlang.github.io/jq/"
  ]
}
```

- [ ] **Step 3: Update `README.md` — reflect v2 architecture**

Replace current README.md with v2 version:

```markdown
# api-doc-parser v2

[![Agent Skill](https://img.shields.io/badge/Agent-Skill-6366f1)](SKILL.md)
[![OpenAPI](https://img.shields.io/badge/OpenAPI-3.x-6ba539)](https://spec.openapis.org/oas/v3.1.0)
[![Swagger](https://img.shields.io/badge/Swagger-2.0-85ea2d)](https://swagger.io/specification/v2/)
[![Version](https://img.shields.io/badge/version-2.0.0-blue)](package.json)

---

### Overview

**api-doc-parser** is a multi-platform Agent Skill for parsing OpenAPI 3.x and Swagger 2.0 API documentation. v2 introduces a modular sub-skill architecture, 9-platform slash command support, and Plugin/NPM distribution.

### Architecture

```
skills/              ← 5 canonical sub-skills (single source of truth)
├── using-api-doc-parser/   Meta-instructions
├── doc-fetch/              Phase 1: Source input
├── doc-list/               Phase 2: Module listing
├── doc-parse/              Phases 3-5: Extraction + Output
└── doc-help/               Usage help

.claude/ .cursor/ ... ← Platform proxies (@ redirects to skills/)
hooks/                ← SessionStart injection
scripts/              ← NPM postinstall/preuninstall
docs/                 ← INSTALL.md, USAGE.md, CHANGELOG.md
```

### Quick Start

```bash
# Install
claude plugins install api-doc-parser

# Use
/doc:fetch https://petstore3.swagger.io/api/v3/openapi.json
/doc:list
/doc:parse pet
```

### Installation

| Method | Command | Best for |
|--------|---------|----------|
| Plugin | `claude plugins install api-doc-parser` | Individual devs |
| NPM | `npm install -g api-doc-parser-skill` | Cross-agent users |
| Manual | `git clone` + copy | Teams, CI/CD |

See [docs/INSTALL.md](docs/INSTALL.md) for detailed instructions.

### Commands

| Command | Description |
|---------|-------------|
| `/doc:fetch <source>` | Fetch API docs from URL or local file |
| `/doc:list [query]` | List and select API modules |
| `/doc:parse [query]` | Extract endpoint details |
| `/doc:help` | Display usage instructions |

See [docs/USAGE.md](docs/USAGE.md) for full command reference and examples.

### Supported Platforms

| Platform | Skills | Slash Commands |
|----------|--------|----------------|
| Claude Code | ✓ | `/doc:fetch` `/doc:list` `/doc:parse` `/doc:help` |
| Cursor | ✓ | `/doc-fetch` `/doc-list` `/doc-parse` `/doc-help` |
| Codex | ✓ | `/doc-fetch` `/doc-list` `/doc-parse` `/doc-help` |
| Gemini CLI | ✓ | `doc-fetch` `doc-list` `doc-parse` `doc-help` |
| Qoder | ✓ | `/doc:fetch` `/doc:list` `/doc:parse` `/doc:help` |
| OpenCode | ✓ | `/doc:fetch` `/doc:list` `/doc:parse` `/doc:help` |
| GitHub Copilot | ✓ | `doc-fetch` `doc-list` `doc-parse` `doc-help` |
| Kimi | ✓ | (natural language only) |
| Trae | ✓ | (natural language only) |

### Output Formats

**Markdown** — Human-readable tables. Copy-paste ready.  
**JSON** — Structured, machine-readable. Cross-session referenceable.

### Output Modes

- **Mode A (display):** Results in conversation. No files.
- **Mode B (save):** Files to `api-doc-parser/.output/<module>.md` + `.json`

### Requirements

- `jq` ≥ 1.6
- `curl` ≥ 7.0 (for URL sources)

### Limitations

- `$ref` schema references show reference names only (not expanded)
- Non-OpenAPI formats (.md/.txt) use LLM extraction (less precise)

### File Structure

```
api-doc-parser/
├── skills/              ← 5 canonical sub-skills
├── hooks/               ← SessionStart hook
├── scripts/             ← NPM postinstall/preuninstall
├── docs/                ← INSTALL.md, USAGE.md, CHANGELOG.md
├── .claude-plugin/      ← Claude Code plugin manifest
├── .claude/ .cursor/ ...← Platform proxies
├── SKILL.md             ← Backward-compatible v1 entry point
├── README.md            ← This file
├── metadata.json        ← v2.0.0
└── package.json         ← NPM package
```
```

- [ ] **Step 4: Create `GEMINI.md`**

```markdown
@./skills/using-api-doc-parser/SKILL.md
```

- [ ] **Step 5: Create `AGENTS.md`**

```markdown
@./skills/using-api-doc-parser/SKILL.md
```

- [ ] **Step 6: Create `gemini-extension.json`**

```json
{
  "name": "api-doc-parser",
  "version": "2.0.0",
  "description": "Parse OpenAPI 3.x / Swagger 2.0 API documentation",
  "skills": [".skills/"],
  "commands": [".commands/"]
}
```

- [ ] **Step 7: Commit**

```bash
git add SKILL.md metadata.json README.md GEMINI.md AGENTS.md gemini-extension.json
git commit -m "feat: update root files for v2 backward compatibility

SKILL.md: added v2 navigation header, preserved v1 5-phase logic intact
metadata.json: version 1.0.0 → 2.0.0, updated description
README.md: rewritten for v2 architecture with sub-skills, platforms, install
GEMINI.md + AGENTS.md: @ redirect to using-api-doc-parser meta-skill
gemini-extension.json: Gemini CLI extension manifest"
```

---

### Task 15: Verification

**Scope:** Verify the full pipeline works end-to-end.

- [ ] **Step 1: Verify all skill frontmatter**

```bash
# Check all .md files have valid YAML frontmatter
for f in $(find skills/ .claude/skills/ .cursor/skills/ .codex/skills/ .gemini/skills/ .kimi/skills/ .qoder/skills/ .trae/skills/ .opencode/skills/ .github/skills/ -name "SKILL.md" 2>/dev/null); do
  echo "=== $f ==="
  head -5 "$f"
  echo ""
done

# Check all command files have valid frontmatter
for f in $(find . -path '*commands*' -name '*.md' 2>/dev/null); do
  echo "=== $f ==="
  head -5 "$f"
  echo ""
done
```

- [ ] **Step 2: Verify proxy files reference correct paths**

```bash
# All platform proxy files should contain @../../skills/<name>/SKILL.md
for platform in .claude .cursor .codex .gemini .kimi .qoder .trae .opencode .github; do
  for skill in using-api-doc-parser doc-fetch doc-list doc-parse doc-help; do
    proxy="$platform/skills/$skill/SKILL.md"
    if [ -f "$proxy" ]; then
      content=$(cat "$proxy")
      expected="@../../skills/$skill/SKILL.md"
      if [ "$content" != "$expected" ]; then
        echo "MISMATCH: $proxy"
        echo "  Expected: $expected"
        echo "  Got: $content"
      fi
    fi
  done
done
echo "All proxy references verified."
```

- [ ] **Step 3: Verify all manifest version consistency**

```bash
# Check version 2.0.0 across all manifests
for f in metadata.json package.json .claude-plugin/plugin.json .cursor-plugin/plugin.json .codex-plugin/plugin.json; do
  if [ -f "$f" ]; then
    ver=$(jq -r '.version' "$f")
    echo "$f: $ver"
    if [ "$ver" != "2.0.0" ]; then
      echo "  WARNING: Expected 2.0.0, got $ver"
    fi
  fi
done
```

- [ ] **Step 4: Verify no openspec files remain**

```bash
REMAINING=$(find . -path '*/openspec-*' -type f 2>/dev/null | wc -l)
if [ "$REMAINING" -eq 0 ]; then
  echo "✓ No openspec files remain — cleanup successful"
else
  echo "WARNING: $REMAINING openspec files still exist"
fi
```

- [ ] **Step 5: Verify file count (target: 5 canonical skills, 45 proxies, ~40 commands)**

```bash
echo "Canonical skills:" $(find skills/ -name "SKILL.md" | wc -l)
echo "Platform proxies:" $(find .claude .cursor .codex .gemini .kimi .qoder .trae .opencode .github -path '*/skills/*' -name 'SKILL.md' 2>/dev/null | wc -l)
echo "Command files:" $(find .claude .cursor .codex .gemini .qoder .opencode .github -path '*commands*' -o -path '*commands*/*.toml' -o -path '*/prompts/*' 2>/dev/null | wc -l)
```

- [ ] **Step 6: Commit verification results (if any changes)**

```bash
# If verification found issues and fixed them, commit
git add -A
git commit -m "chore: fix verification issues found in final check"
# If no changes: "Verification passed — no issues found."
```

---

## Self-Review Checklist

### 1. Spec Coverage

| Delta Spec Requirement | Covered by Task |
|------------------------|-----------------|
| api-doc-parser: Dual input source | Task 2 (doc-fetch SKILL.md) |
| api-doc-parser: Module listing and selection | Task 2 (doc-list SKILL.md) |
| api-doc-parser: Endpoint detail extraction | Task 2 (doc-parse SKILL.md) |
| api-doc-parser: Dual format output | Task 2 (doc-parse SKILL.md) |
| api-doc-parser: Output mode selection | Task 2 (doc-parse SKILL.md) |
| api-doc-parser: Context overflow prevention | Task 2 (doc-parse rules) |
| api-doc-parser: Cross-platform command registration | Tasks 3-9 |
| api-doc-parser: Help command | Task 2 (doc-help SKILL.md) |
| multi-platform-command-routing: All 9 platforms | Tasks 3-9 |
| plugin-packaging: Claude Code plugin | Task 10 |
| plugin-packaging: Marketplace listing | Task 10 |
| plugin-packaging: Cursor & Codex plugins | Task 10 |
| plugin-packaging: NPM package | Task 11 |
| plugin-packaging: Postinstall conflict avoidance | Task 11 |
| plugin-packaging: Version consistency | Task 15 (verification) |
| install-documentation: INSTALL.md | Task 13 |
| install-documentation: USAGE.md | Task 13 |
| install-documentation: CHANGELOG.md | Task 13 |
| subskill-architecture: 5 sub-skills | Task 2 |
| subskill-architecture: Backward compatibility | Task 14 |
| subskill-architecture: Output mode parameter override | Task 2 (doc-parse) |
| subskill-architecture: Runtime dependency check | Task 2 (doc-fetch/doc-list/doc-parse) |
| subskill-architecture: doc-list pagination | Task 2 (doc-list) |
| cross-phase-state: Shared state file | Task 2 (all sub-skills) |
| cross-phase-state: State file resilience | Task 2 (all sub-skills) |
| cross-phase-state: State file archival | Task 2 (doc-fetch) |
| cross-phase-state: Reading priority | Task 2 (doc-list/doc-parse) |
| cross-phase-state: State file schema | Task 2 (doc-fetch) |
| cross-phase-state: State file validation | Task 2 (doc-list/doc-parse) |
| cross-phase-state: Windows temp directory | Task 2 (all sub-skills use TMPDIR/TEMP) |
| cross-phase-state: Stale source detection | Task 2 (doc-list/doc-parse) |
| session-start-injection: Hook configuration | Task 12 |
| session-start-injection: using-api-doc-parser content | Task 2 |
| session-start-injection: Platform-agnostic injection | Task 12 |
```

- [ ] **Step 6: Run Petstore end-to-end test**

```bash
# Test: Fetch Petstore API
echo "=== Testing doc-fetch ==="
curl -s https://petstore3.swagger.io/api/v3/openapi.json -o /tmp/test-petstore.json
jq '.openapi' /tmp/test-petstore.json
# Expected: "3.0.3"

# Test: List tags
echo "=== Testing tag extraction ==="
jq -r '.tags[]? | "\(.name) — \(.description // "(no description)")"' /tmp/test-petstore.json
# Expected: pet, store, user

# Test: Count endpoints per tag
echo "=== Testing endpoint counts ==="
jq -r '[.paths | to_entries[] | .value | to_entries[]? | .value.tags[]?] | group_by(.) | .[] | "\(.[0]):\(length)"' /tmp/test-petstore.json

# Test: Filter by tag
echo "=== Testing tag filtering ==="
jq --arg tag "pet" '
  .paths | to_entries | map(
    select(.value | to_entries | .[].value.tags? // [] | contains([$tag]))
  ) | from_entries | keys
' /tmp/test-petstore.json

# Cleanup
rm -f /tmp/test-petstore.json
echo "✓ Petstore E2E pipeline verified"
```

- [ ] **Step 7: Final commit**

```bash
git add -A
git commit -m "chore: final verification and cleanup for v2 upgrade"
```