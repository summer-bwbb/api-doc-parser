---
change: upgrade-api-doc-parser-v2
role: technical-design
canonical_spec: openspec
topic: api-doc-parser-v2-技术实现设计
date: 2026-06-15
status: approved
---

# api-doc-parser v2 技术实现设计

## 1. 整体架构

```
api-doc-parser/                    ← 项目根
├── SKILL.md                       ← v1 向后兼容入口（保留原 5-Phase 逻辑，顶部加导航说明）
├── metadata.json                  ← version: 2.0.0
├── package.json                   ← NPM 发布清单
├── README.md                      ← v2 架构说明
├── AGENTS.md                      ← @./skills/using-api-doc-parser/SKILL.md
├── GEMINI.md                      ← @./skills/using-api-doc-parser/SKILL.md
├── gemini-extension.json          ← Gemini 扩展清单
│
├── skills/                        ← 【唯一真身】5 个子技能
│   ├── using-api-doc-parser/SKILL.md
│   ├── doc-fetch/SKILL.md
│   ├── doc-list/SKILL.md
│   ├── doc-parse/SKILL.md
│   └── doc-help/SKILL.md
│
├── hooks/
│   ├── hooks.json                 ← SessionStart: startup|clear|compact
│   └── session-start.sh           ← cat skills/using-api-doc-parser/SKILL.md
│
├── scripts/
│   ├── postinstall.js             ← 检测平台 + 注册 skills/commands 到全局或项目配置目录
│   ├── preuninstall.js            ← 清理注册
│   └── check-deps.sh              ← jq/curl 版本检测
│
├── docs/
│   ├── INSTALL.md                 ← 三种安装方式（Plugin / NPM / 手动）
│   ├── USAGE.md                   ← 命令参考 + 场景示例
│   └── CHANGELOG.md               ← v1.0.0 + v2.0.0
│
├── .claude-plugin/
│   ├── plugin.json                ← Claude Code plugin manifest
│   └── marketplace.json           ← marketplace 上架信息
├── .cursor-plugin/plugin.json     ← Cursor plugin manifest
├── .codex-plugin/plugin.json      ← Codex plugin manifest
│
├── .claude/                       ← Claude Code 平台适配
│   ├── skills/{5 子技能}/SKILL.md  ← 代理：@../../skills/<name>/SKILL.md
│   └── commands/doc/{fetch,list,parse,help}.md
├── .cursor/                       ← Cursor 平台适配
│   ├── skills/{5 子技能}/SKILL.md
│   └── commands/doc/{4 命令}.md
├── .codex/                        ← Codex 平台适配
│   └── skills/{5 子技能}/SKILL.md   ← 仅 skills（Codex 命令目录为全局 ~/.codex/prompts/）
├── .gemini/                       ← Gemini CLI
│   ├── skills/{5 子技能}/SKILL.md
│   └── commands/doc/{4 命令}.toml   ← TOML 格式，必填 prompt 字段
├── .kimi/skills/{5 子技能}/SKILL.md ← Kimi（仅 skills，无 commands）
├── .qoder/                        ← Qoder（兼容 Claude Code frontmatter 格式）
│   ├── skills/{5 子技能}/SKILL.md
│   └── commands/doc/{4 命令}.md
├── .trae/skills/{5 子技能}/SKILL.md ← Trae（仅 skills，无 commands）
├── .opencode/                     ← OpenCode
│   ├── skills/{5 子技能}/SKILL.md
│   └── commands/{4 命令}.md
└── .github/                       ← GitHub Copilot
    ├── skills/{5 子技能}/SKILL.md
    └── prompts/{4 命令}.prompt.md   ← .prompt.md 格式，参数语法 ${input:name}
```

---

## 2. 数据流

```
/doc:fetch <URL>
  → .claude/commands/doc/fetch.md → 引用 skills/doc-fetch/SKILL.md（@ 重定向）
  → curl 抓取 → jq 校验 → 写入 /tmp/api-doc-parser/state.json
  → 会话结束 → 归档到 <project>/.api-doc-parser/state.json

/doc:list [keywords|indices|all]
  → 读 state.json（/tmp 优先 → 项目级回退）
  → jq 提取 tags → 用户选择 → 更新 state.json selectedTags

/doc:parse [--mode A|B]
  → 读 state.json 中的 selectedTags + sourcePath
  → jq 按 tag 过滤 → 提取详情 → 按输出模式输出
```

---

## 3. 核心组件设计

### 3.1 Skills 代理机制

**策略：`@` 内容重定向引用**

所有平台 skills 目录下的 `SKILL.md` 为薄代理文件，内容为：

```markdown
@../../skills/<skill-name>/SKILL.md
```

- 单一数据源在 `skills/` 目录
- 各平台仅保留引用，不做副本
- Agent 调用 Skill 工具时自动解析 `@` 引用并加载真实内容

### 3.2 跨 Phase 状态管理

**策略：tmp 优先 + 会话结束后归档到项目级**

#### 状态文件位置
- **会话级**：`/tmp/api-doc-parser/state.json`（优先读取）
- **项目级**：`<project>/.api-doc-parser/state.json`（归档持久化）

#### 完整 Schema

```json
{
  "sourcePath": "/tmp/api-doc-parser/fetched.json",
  "sourceType": "url",
  "sourceUrl": "https://petstore3.swagger.io/api/v3/openapi.json",
  "openapiVersion": "3.0.3",
  "fetchedAt": "2026-06-15T10:30:00Z",
  "selectedTags": ["pet", "store"],
  "outputMode": "B"
}
```

#### 生命周期

```
doc-fetch 完成
  → 写入 /tmp/api-doc-parser/state.json（sourcePath/Type/Url/Version/fetchedAt）
  → 清空 selectedTags（新源，旧模块选择失效）

doc-list 完成
  → 读取优先级：/tmp（优先）→ 项目级（回退）
  → 追加 selectedTags → 写回 /tmp

doc-parse 运行
  → 读取优先级：/tmp（优先）→ 项目级（回退）
  → 消费 selectedTags 和 sourcePath

会话结束
  → hook 或 shell trap 触发归档
  → cp /tmp/api-doc-parser/state.json → <project>/.api-doc-parser/state.json
```

#### 读取优先级逻辑（伪代码）

```
read_state():
  1. if /tmp/api-doc-parser/state.json exists → use it
  2. elif <project>/.api-doc-parser/state.json exists → use it, copy to /tmp 恢复会话状态
  3. else → 提示用户提供源（交互式回退，询问 URL 或文件路径）
```

#### 状态缺失时的交互式回退

当 `doc-list` 或 `doc-parse` 发现无 state.json：
1. 提示用户："No source fetched yet. Please provide an OpenAPI URL or local file path."
2. 用户提供后，自动执行内部 fetch → 再回到原命令逻辑
3. 整个流程在一个对话回合内完成

### 3.3 输出模式管理

**策略：配置预设 + 可覆盖参数**

- `state.json` 中存储 `outputMode` 字段（首次运行时询问并缓存）
- `doc-parse` 读取预设，用户可通过参数临时覆盖：
  - `/doc:parse` → 使用预设或询问
  - `/doc:parse -a` 或 `/doc:parse --display` → 临时使用 Mode A
  - `/doc:parse -b` 或 `/doc:parse --save` → 临时使用 Mode B

### 3.4 依赖检测

**策略：安装时 + 运行时双重检测**

#### 安装时（postinstall.js）

```javascript
// 伪代码
const deps = [
  { name: 'jq', minVersion: '1.6', install: { darwin: 'brew install jq', linux: 'apt install jq', win32: 'choco install jq' } },
  { name: 'curl', minVersion: '7.0', install: { darwin: 'brew install curl', linux: 'apt install curl', win32: 'choco install curl' } }
];

for (const dep of deps) {
  const installed = checkWhich(dep.name);
  if (!installed) {
    console.warn(`⚠️  ${dep.name} not found. Install: ${dep.install[process.platform]}`);
    continue;
  }
  const version = getVersion(dep.name);
  if (compareVersions(version, dep.minVersion) < 0) {
    console.warn(`⚠️  ${dep.name} ${version} < ${dep.minVersion}. Please upgrade.`);
  }
}
```

#### 运行时（doc-fetch SKILL.md 开头）

```bash
# 检测 jq
if ! command -v jq &> /dev/null; then
  echo "ERROR: jq is required. Install:"
  case "$(uname -s)" in
    Darwin*) echo "  brew install jq" ;;
    Linux*)  echo "  sudo apt install jq" ;;
    MINGW*)  echo "  choco install jq" ;;
  esac
  exit 1
fi

# 检测版本
JQ_VER=$(jq --version | grep -oP '\d+\.\d+' | head -1)
if (( $(echo "$JQ_VER < 1.6" | bc -l) )); then
  echo "ERROR: jq >= 1.6 required, found $JQ_VER"
  exit 1
fi

# 同理 curl
```

### 3.5 SessionStart Hook

**策略：模仿 superpowers — hook 执行 command 输出 skill 内容到 stdout**

`hooks/hooks.json`：
```json
{
  "SessionStart": [
    {
      "matcher": "startup|clear|compact",
      "hooks": [
        {
          "type": "command",
          "command": "cat \"$(dirname \"$0\")/session-start.sh\" | sh"
        }
      ]
    }
  ]
}
```

`hooks/session-start.sh`：
```bash
#!/bin/sh
# 读取 using-api-doc-parser 内容，Claude Code 将 stdout 注入 Agent 系统提示
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cat "$SKILL_DIR/skills/using-api-doc-parser/SKILL.md"
```

### 3.6 NPM 安装后注册

**策略：全局 + 项目级，按安装上下文选择行为**

`scripts/postinstall.js` 逻辑：

```
if (全局安装: npm_config_global 或路径在全局 node_modules)
  → 注册到 ~/.claude/skills/、~/.cursor/skills/、~/.codex/skills/
  → 同时注册 commands 到对应全局目录
else (项目级安装)
  → 不操作（项目文件已在 node_modules/<pkg>/ 下，用户需手动引用）
  → 打印指导：如何将 skills 引用到项目配置中
```

注册方式：
- 检测 `~/.claude/` 存在 → 创建 skills/ 软链接或复制代理文件
- 检测 `~/.cursor/` 存在 → 同上
- 检测 `~/.codex/` 存在 → 同上
- 如果 Plugin 已安装检测到则跳过（避免重复注册）

`scripts/preuninstall.js`：
- 清理上述目录中已注册的 skills/commands
- 仅删除由 postinstall 记录的文件（不误删用户自己的配置）

---

## 4. 跨平台命令格式适配

### 4.1 各平台格式总表

| 平台 | 命令文件格式 | Frontmatter | 关键差异 |
|------|-------------|-------------|---------|
| **Claude Code** | `.md` + YAML frontmatter | 有 | 命名空间用 `:`，参数 `$ARGUMENTS` / `$1` |
| **Cursor** | `.md`（纯 Markdown） | 无（官方），可加 YAML 兼容 | 命名用 `-`，无标准参数变量 |
| **Gemini CLI** | `.toml` | TOML 格式 | **唯一非 .md 平台**，必填 `prompt`，参数 `{{args}}` |
| **GitHub Copilot** | `.prompt.md` + YAML frontmatter | 有 | 命名用 `-`，参数 `${input:name}` |
| **Codex CLI** | `.md` + YAML frontmatter | 有 | **只有全局目录 `~/.codex/prompts/`**，无项目级命令目录 |
| **Qoder** | `.md` + YAML frontmatter | 有 | 兼容 Claude Code 格式 |
| **OpenCode** | `.md` + YAML frontmatter | 有（可选） | 参数 `$ARGUMENTS` / `$1`，支持内联 `!`cmd`` |
| **Kimi** | 无 commands 目录 | — | 仅 skills |
| **Trae** | 无 commands 目录 | — | 仅 skills |

### 4.2 命令文件模板

#### Claude Code — `.claude/commands/doc/fetch.md`

```markdown
---
name: "DOC: Fetch"
description: "Fetch API documentation from URL or local file"
argument-hint: "<URL or file path>"
---

Read the instructions in `skills/doc-fetch/SKILL.md` and execute them for: $ARGUMENTS
```

#### Gemini CLI — `.gemini/commands/doc/fetch.toml`

```toml
description = "Fetch API documentation from URL or local file"

prompt = """
Read the instructions in skills/doc-fetch/SKILL.md and execute them for the provided URL or file path.
"""
```

#### GitHub Copilot — `.github/prompts/doc-fetch.prompt.md`

```markdown
---
description: "Fetch API documentation from URL or local file"
---

Read the instructions in `skills/doc-fetch/SKILL.md` and execute them for the provided source.
```

#### Kimi / Trae — 仅 `skills/` 目录

无命令路由文件。Agent 通过自然语言触发。

---

## 5. 错误处理矩阵

### 5.1 doc-fetch 错误

| 条件 | 行为 |
|------|------|
| URL 不可达（curl 非 2xx） | 报错 + 显示 curl 退出码 + 提示重试或手动输入 |
| 本地文件不存在 | 报错 + 提示检查路径 + 建议使用绝对路径 |
| 文件非有效 JSON | `jq 'type'` 失败 → 报错 + 显示前 200 字符 |
| 文件 >10MB | 警告大文件 + 建议裁剪 + 仍允许继续 |
| 非 OpenAPI 格式 | jq 检测无 `openapi` 或 `swagger` 字段 → 报错 |
| OpenAPI 2.x（Swagger） | 警告部分功能受限 + 仍允许继续 |
| jq 未安装或版本 < 1.6 | 报错 + 按 OS 给出安装指令 |
| curl 未安装或版本 < 7.0 | 报错 + 按 OS 给出安装指令 |
| state.json 写入权限不足 | 回退到内存模式，提示输出不会持久化 |

### 5.2 doc-list 边界条件

| 条件 | 行为 |
|------|------|
| 文档无 tag | 显示 "1 个默认模块（未分类端点）" |
| tags >50 个 | 分页显示（每页 20），提示翻页方式 |
| 用户输入无效索引 | 报错 + 显示有效范围 "1-15" |
| 关键词无精确匹配 | 模糊匹配 + 提示最接近的 3 个候选 |
| state.json missing | 交互式回退 → 询问 URL 或文件路径 |
| state.json 有 sourcePath 但源文件被删 | 检测 → 提示重新 fetch |

### 5.3 doc-parse 边界条件

| 条件 | 行为 |
|------|------|
| state.json missing | 交互式回退 → 自动内联 fetch + list |
| 空模块（0 endpoints） | 报告 + 跳过 + 继续其他模块 |
| 单模块 >30 endpoints | 摘要警告 + 确认后再全量解析 |
| $ref 循环引用 | 记录引用名 + 最多展开 1 层（保持 v1 行为） |
| 输出目录无写权限 | 回退到 Mode A（仅显示） |
| Mode B 文件名冲突 | 追加时间戳后缀避免覆盖 |

---

## 6. 平台适配细节

### 6.1 Plugin Manifest 关键字段

`.claude-plugin/plugin.json`：
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

**注意**：`skills` 和 `commands` 字段**必须为数组**，不接受字符串。不要添加 `agents` 字段（会被验证器拒绝）。不要添加指向默认路径 `hooks/hooks.json` 的 `hooks` 字段（会自动加载）。

### 6.2 Windows 兼容性

- 状态文件路径：`$TMPDIR` 或 `$TEMP` 环境变量，Unix 回退 `/tmp`
- 文件名清理：替换非法字符 `\/:*?"<>|` → `_`
- 路径分隔符：内部分用 `/`，系统调用时适配
- 符号链接：不使用（C 方案已否决），全部用内容代理

### 6.3 openspec 旧文件清理

升级前清理的目录（与原项目无关的 openspec 插件文件）：
- `.claude/skills/openspec-*/`
- `.claude/commands/opsx/`
- `.cursor/skills/openspec-*/`
- `.cursor/commands/opsx-*.md`
- `.codex/skills/openspec-*/`
- `.gemini/skills/openspec-*/`
- `.kimi/skills/openspec-*/`
- `.qoder/skills/openspec-*/`
- `.qoder/commands/opsx/`
- `.trae/skills/openspec-*/`
- `.opencode/skills/openspec-*/`
- `.opencode/commands/opsx-*.md`
- `.github/skills/openspec-*/`
- `.github/prompts/opsx-*.prompt.md`

---

## 7. 测试策略

### 7.1 测试分层

```
E2E（端到端）
  └── Petstore API 全管道（fetch → list → parse）× 3 种安装方式

集成测试
  └── 单平台命令路由 × 9 平台 × 4 命令

单元测试
  └── jq 提取逻辑 / state 读写 / 依赖检测 / 错误路径
```

### 7.2 测试场景矩阵

| 维度 | 覆盖 |
|------|------|
| 输入源 | URL（JSON）、本地 .json、.md、.txt |
| OpenAPI 版本 | 2.x（Swagger）、3.0.x、3.1.x |
| 模块选择 | 索引、关键词、混合、all、无效输入 |
| 输出模式 | A（显示）、B（文件）、参数切换/覆盖 |
| 错误路径 | 网络断开、文件缺失、格式错误、超大文件 |
| 跨平台 | Claude Code、Cursor、Gemini 等 |
| 安装方式 | Plugin、NPM、手动 |
| 跨会话 | fetch → 退出 → 重进 → list → parse |
| 向后兼容 | 自然语言触发 SKILL.md |
| Windows 路径 | TEMP 非 /tmp、反斜杠路径 |

---

## 8. 技术风险

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| 9 平台 × 5 skills 代理文件维护 | 45 个代理文件需保持引用路径正确 | 代理文件内容仅 1 行 `@` 引用，无维护负担 |
| `@` 引用在某些平台上不被解析 | 特定平台 agent 无法加载真实 skill | 对不确定平台（Kimi、Trae），准备回退方案：代理文件内联简短指令 + `@` 引用 |
| Windows TEMP 路径与 Unix `/tmp` 不同 | state.json 路径错误 | 使用 `$TMPDIR`/`$TEMP` env var，跨平台统一 |
| NPM postinstall 与 Plugin 安装冲突 | 重复注册或文件覆盖 | postinstall 先检测已有注册，冲突时跳过并警告 |
| state.json 被手动篡改导致 jq 语法错误 | doc-list/doc-parse 崩溃 | 读取 state.json 前用 jq 校验 JSON 有效性 |
| 超大 OpenAPI 文档（>50MB）导致 jq 内存溢出 | doc-fetch 或 doc-parse 卡死 | 添加文件大小阈值检查（10MB 警告，50MB 拒绝） |
| Claude Code Plugin 验证器拒绝 manifest | 插件无法安装 | 严格遵循已知 schema，不使用额外字段 |
