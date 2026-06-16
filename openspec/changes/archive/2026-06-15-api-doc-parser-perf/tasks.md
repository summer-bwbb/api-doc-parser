## 1. OpenSpec 文档

- [x] 1.1 创建变更目录 `openspec/changes/archive/2026-06-15-api-doc-parser-perf/`
- [x] 1.2 编写 `.openspec.yaml`
- [x] 1.3 编写 `proposal.md`
- [x] 1.4 编写 `design.md`
- [x] 1.5 编写 `tasks.md`（本文档）

## 2. 核心解析引擎

- [ ] 2.1 创建 `skills/doc-parse/parse.py`
  - 读取 `state.json` 获取 `sourcePath` 和 `selectedTags`
  - 加载 OpenAPI JSON（不进入 Agent 上下文）
  - 预索引 `components/schemas`
  - 按 tag 过滤 paths
  - 批量递归展开 `$ref`（depth ≤ 2，循环引用检测）
  - 生成 Markdown 和 JSON 输出
  - 直接写入 `.output/` 目录（Mode B）或输出到 stdout（Mode A）
- [ ] 2.2 创建 `skills/doc-parse/lib/schema_cache.py`
  - `SchemaCache` 类：按 name 索引 schema
  - `resolve(name, depth)` 方法：递归展开，返回字段列表和 nestedSchemas
  - 循环引用检测：记录已解析 name
  - 深度限制：超过 2 层返回占位符
- [ ] 2.3 创建 `skills/doc-parse/lib/formatter.py`
  - `to_markdown(module, endpoints)`：生成当前 SKILL.md 中定义的 Markdown 格式
  - `to_json(module, endpoints, meta)`：生成当前 SKILL.md 中定义的 JSON 格式
  - 文件名清理函数（替换文件系统非法字符）

## 3. SKILL.md 调用层改造

- [ ] 3.1 精简 `skills/doc-parse/SKILL.md`
  - 保留前置依赖检查（jq + python3）
  - 保留 state 读取和参数解析逻辑
  - 保留大模块保护提示
  - 把提取/格式化逻辑替换为调用 `parse.py`
  - 保留 Mode A/B 输出模式处理
- [ ] 3.2 支持 `-y` / `--auto` 标志
  - 检测到标志时跳过大型模块二次确认
  - 将标志传给 `parse.py`

## 4. 兼容性与降级

- [ ] 4.1 当 `python3` 不可用时，保留原 jq 路径作为 fallback
- [ ] 4.2 验证输出 JSON 字段命名与 v2 一致
- [ ] 4.3 验证 Markdown 结构与 v2 一致

## 5. 验证

- [ ] 5.1 使用 petstore OpenAPI JSON 进行端到端测试
- [ ] 5.2 使用一个 200KB+ 的 springdoc 风格文档测试大模块解析
- [ ] 5.3 对比优化前后耗时（粗略计时）
- [ ] 5.4 检查 `.output/` 文件生成是否正确
- [ ] 5.5 检查 Python 不可用时 fallback 路径是否正常工作
