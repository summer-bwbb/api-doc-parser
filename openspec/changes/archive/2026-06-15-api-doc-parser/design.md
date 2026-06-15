## Context

本项目是一个 Agent Skills 工作区，当前使用 OpenSpec spec-driven 工作流管理变更。已有的 skill 通过 `skills/<name>/SKILL.md` 定义，平台命令通过 `.claude/commands/`、`.cursor/commands/`、`.codex/commands/` 进行路由。本次需要新增 `api-doc-parser` 技能，支持从 OpenAPI 文档中按模块提取接口详情。

目标接口文档格式为 springdoc-openapi 生成的 OpenAPI 3.x JSON，数据量中等（100-500KB），需防范上下文溢出。

## Goals / Non-Goals

**Goals:**
- 解析 OpenAPI 3.x / Swagger 2.0 格式的接口文档
- 支持 URL（curl 抓取）和本地文件（.json/.md/.txt）双输入源
- 按 tags（模块）筛选，支持多选和关键词模糊匹配
- 生成 Markdown（可复制）和 JSON（可引用）双格式输出
- 内置上下文溢出保护（jq 管线，原始 JSON 不进 Agent 上下文）
- 跨平台命令注册（Claude Code / Cursor / Codex）

**Non-Goals:**
- v1 不展开 `$ref` 引用的 Schema 详情（仅显示引用名称）
- 不修改 OpenAPI 文档本身
- 不提供接口测试/调用功能
- 不支持非 OpenAPI/Swagger 格式的文档自动解析（.md/.txt 走 LLM 提取）

## Decisions

### 决策 1: jq 管线过滤 vs Agent 直接读取

**选择**: 使用 jq 在 shell 层预过滤原始 JSON

**理由**: springdoc-openapi 生成的文档可达数百 KB，直接进入 Agent 上下文会导致溢出或高昂的 token 消耗。使用 `curl <url> | jq '.tags'` 和 `jq 'paths filtered by tag'` 管线，在 shell 层完成过滤，只有精简后的结果进入 Agent。

**备选方案**: 让 Agent 直接 Read 整个 JSON。优点是不依赖 jq，缺点是大型 JSON 必然溢出，且 token 消耗巨大。不可取。

### 决策 2: $ref 不展开 (v1)

**选择**: v1 版本仅记录 `$ref` 引用名称（如 `ResultDTOOdmTaskListResponse`），不递归解析 `components/schemas`

**理由**: `components/schemas` 通常是文档中最大的部分，可包含数十个复杂嵌套 Schema。展开后上下文极易溢出。作为 v1，提供引用名称已足够前端开发者查找对应 DTO，需要详细字段时可手动在 Swagger UI 查看。

**备选方案**: 按需展开——用户指定某个 $ref 时才解析。这是 v2 候选方案。

### 决策 3: SKILL.md 为核心，平台命令仅做路由

**选择**: 所有执行逻辑放在 `skills/api-doc-parser/SKILL.md`，各平台命令文件仅包含 frontmatter + 调用指令

**理由**: 参考 superpowers 插件模式——一份 SKILL.md 被多个平台共享，避免多份重复逻辑产生不一致。命令文件 (`commands/doc/parse.md`) 只负责注册斜杠命令，内容极简。

### 决策 4: 输出模式可选

**选择**: 两种模式——A. 直接展示到对话（快速引用）；B. 保存文件到 `.output/`（持久化跨对话）

**理由**: 用户场景不同。快速查询一个接口时，不需要文件残留（模式 A）；完整解析一个模块并需要后续对话继续使用时，需要持久化（模式 B）。

### 决策 5: 大模块保护策略

**选择**: 超过 30 个接口的模块先显示摘要列表，询问是否全量解析

**理由**: 某些粗粒度 tag（如"通用接口"）可能包含大量接口。全量解析这部分会塞满上下文。先摘要让用户判断是否需要全量。

## Data Flow

```
Shell Layer (no context)        Agent Context             Output
═══════════════════════        ════════════════        ════════════

curl → /tmp/api-doc.json
         │
    ┌────┴────┐
    jq '.tags'  ──────────────────→ 模块列表
    (tags only)                      (≤500B)
         │                                       → Markdown 展示
    ┌────┴────┐                                   (对话输出)
    jq filter  ──────────────────→ 目标模块接口
    paths by tag                   (JSON 片段)    → .output/*.md
         │                                       → .output/*.json
         │                                       (文件持久化)
    临时文件不入上下文 ✓
    原始 paths 全量不入上下文 ✓
```

## OpenAPI JSON Mapping

```
tags[] → 模块列表
  ├─ name         → 模块名称
  └─ description  → 模块描述

paths: {/api/xxx} → API 接口
  ├─ get/post/put/delete/patch → HTTP 方法
  ├─ tags[]                    → 所属模块
  ├─ summary                   → 接口名称
  ├─ description               → 接口描述
  ├─ operationId               → 操作ID
  ├─ parameters[]              → 查询/路径参数
  │   ├─ name / in / description
  │   ├─ required / schema.type
  │   └─ schema.default
  ├─ requestBody               → 请求体
  │   ├─ required
  │   └─ content → schema.$ref
  └─ responses{}               → 响应
      ├─ status code
      ├─ description
      └─ content → schema.$ref
```

## File Structure

遵循项目惯例，Skill 作为独立文件夹放在项目根目录下（参考 `vue-gis-perf-practices/`）：

```
api-doc-parser/                  ← Skill 独立目录（项目根目录）
├── SKILL.md                     ← 核心技能逻辑（所有平台共用）
├── README.md                    ← 用户使用说明
├── metadata.json                ← Skill 元数据
└── .output/                     ← 输出归档
    ├── {module}.json
    └── {module}.md

.claude/commands/doc/
├── parse.md                     ← /doc:parse 命令路由
└── help.md                      ← /doc:help 命令路由

.cursor/commands/doc/
├── doc-parse.md                 ← Cursor 路由
└── doc-help.md

.codex/commands/doc/
├── doc-parse.md                 ← Codex 路由
└── doc-help.md
```

## Risks / Trade-offs

- **jq 依赖**: 需要在运行环境中有 jq 可用（Git Bash / WSL / 系统中安装）。→ 降级方案：轻量 JSON 文档（<256KB）直接用 Read
- **远程 URL 不可达**: 内网地址在沙箱环境可能无法访问。→ 提示用户改用本地文件导入
- **模块名模糊匹配歧义**: 关键词可能与多个 tag 部分匹配。→ 展示匹配结果让用户确认
- **.md/.txt 解析依赖 LLM 理解**: 非结构化文本的提取准确性不如结构化 JSON。→ 仅作辅助输入源，推荐优先使用 .json
