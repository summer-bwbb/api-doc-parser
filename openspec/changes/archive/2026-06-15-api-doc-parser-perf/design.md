## Context

`api-doc-parser` v2 已经支持递归展开 `$ref` schema、多模块选择和 Markdown/JSON 双输出。但在实际使用中发现，当文档较大（100-500KB）、模块接口较多（>30）或 Schema 嵌套较深时，解析耗时明显增加。主要原因是：

1. `doc-parse` 的 `SKILL.md` 超过 500 行，每次调用都完整进入模型上下文，token 开销大。
2. 解析逻辑通过大量独立 jq 调用实现，每个 tag、每个 schema 都产生一次 shell 调用，反复读取 `components/schemas`。
3. Markdown/JSON 格式化依赖 LLM 逐段生成，大模块下上下文消耗高。

本次优化的目标是在**不改变用户接口、不破坏上下文溢出保护、不修改输出格式**的前提下，把核心解析逻辑下沉到本地脚本，实现一次性批量处理。

## Goals / Non-Goals

**Goals:**
- 显著降低 `doc-parse` 阶段的耗时和 token 消耗
- 保持 `doc-fetch` / `doc-list` / `doc-parse` 三阶段流程不变
- 保持输出格式、字段命名、文件结构向后兼容
- 保持上下文溢出保护：原始 OpenAPI JSON 不进入 Agent 上下文
- 支持 Python 不可用时的优雅降级（保留原 jq 路径）

**Non-Goals:**
- 不重构 `doc-fetch` 和 `doc-list`
- 不改变命令名称、参数语义和状态文件格式
- 不引入外部依赖包（仅使用 Python 标准库 + jq）
- 不修改输出目录结构 `.output/`

## Decisions

### 决策 1: Python 脚本作为解析核心

**选择**: 新增 `skills/doc-parse/parse.py`，由 `SKILL.md` 调用

**理由**: Python 标准库即可处理 JSON、递归展开、Markdown/JSON 生成，单次脚本调用替代数十次 jq/Bash/LLM 调用，速度提升最大。

**备选方案**: 继续用 jq，但写一个超复杂的聚合 filter。优点是无需 Python，缺点是 filter 难以维护，且仍需要多次 LLM 格式化。不可取。

### 决策 2: SKILL.md 仅作为调用层

**选择**: `skills/doc-parse/SKILL.md` 只负责依赖检查、读取 state、解析参数、调用 `parse.py`、展示结果

**理由**: 缩短 Skill 文件长度，减少每次调用的上下文开销；同时保留跨平台命令路由不变。

### 决策 3: 保持 jq/curl 依赖，新增 python3 为软依赖

**选择**: `parse.py` 需要 `python3`，但 `SKILL.md` 先检测 Python 可用性；不可用时回退到原 jq 路径

**理由**: 大多数运行环境已有 Python，但不能假设 100% 可用。降级保证兼容性。

### 决策 4: Schema 预索引 + 缓存

**选择**: `parse.py` 启动时一次性把 `components/schemas` 读入内存，按 name 索引；递归展开时直接查内存

**理由**: 避免反复读取磁盘和反复 jq 查询。递归展开 depth=2，带循环引用检测。

### 决策 5: 输出文件由脚本直接写入

**选择**: Markdown 和 JSON 文件由 `parse.py` 直接写入磁盘，而不是 LLM 生成后再用 Write 工具保存

**理由**: 减少模型上下文消耗，提高大模块输出速度。

## Data Flow

```
Shell Layer (no context)        Agent Context             Output
═══════════════════════        ════════════════        ════════════

state.json
    │
    ▼
parse.py ──读取 OpenAPI JSON────┐
    │                            │
    ├─ 批量展开 $ref schema       │
    ├─ 生成 Markdown            ──→ 展示摘要 / 文件路径
    └─ 生成 JSON                 │   → .output/*.md
                                 │   → .output/*.json
```

## File Structure

```
skills/doc-parse/
├── SKILL.md          ← 调用层（精简）
├── parse.py          ← 核心解析引擎
└── lib/
    ├── __init__.py
    ├── schema_cache.py   ← Schema 预索引与递归展开
    └── formatter.py      ← Markdown/JSON 格式化
```

## Risks / Trade-offs

- **python3 不可用**: 检测后回退到原 jq 路径，性能不变差但也不优化。
- **Windows 路径问题**: `parse.py` 使用 `pathlib`，避免硬编码 `/tmp/`。
- **Schema 展开深度**: 保持 depth=2，与 v2 一致，防止上下文爆炸。
- **大模块输出**: 仍保留 >30 接口警告，但 `-y` 标志可自动确认。
