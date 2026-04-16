# Current Task

## 任务目标

新增 `/digest-meeting` 技能，把多人讨论的原始语音转文字记录转化为框架可消费的结构化产物。覆盖研发流程中"需求讨论→任务输入"的源头缺口。

**为什么做**：框架现有 `/process-notes` 处理的是单人已整理的笔记，无法应对"多人对话、决策散落、有分歧有共识"的原始讨论记录。讨论记录是研发最早一环，没有专门入口意味着用户要人工整理一遍才能喂给框架。

**使用场景**：
- 新项目启动：idea 讨论记录 → 填充 product.md / architecture.md 作为第一版需求
- 产品迭代：需求评审讨论记录 → 产出 current-task.md，交给 /lfg 开发

## 假设清单

- **假设：讨论记录放在 `notes/` 下**（与 `/process-notes` 一致） | 依据：已有约定，避免再造目录
- **假设：输入格式主要是飞书妙记导出，但要兼容纯文本/带说话人/带时间戳** | 依据：用户明确说 "最好支持的广一点"
- **假设：两种模式通过自动检测（product.md 是否占位符）判定，不强制用户传 flag** | 依据：减少用户心智负担
- **假设：`/digest-meeting` 不直接串 `/spec`，iterate 模式只写 current-task.md，由 `/lfg` 自己决定是否触发 `/spec`** | 依据：避免与 `/lfg` 阶段 2.5 的触发逻辑重复判断
- **假设：meta 项目自动委托给 `/meta-create-task`** | 依据：用户选 A；meta 已有专属路由
- **假设：处理后的结构化产物放 `notes/digested/`，原始记录不动** | 依据：用户选 C；原始记录是一手资料需要保留
- **假设：放 common 层不是 superpowers** | 依据：用户明确选 common；这是"原材料处理"而非结构化工作流技能
- **假设：已处理的原始文件在头部插 `<!-- processed: YYYY-MM-DD -->` 标记** | 依据：与 `/process-notes` 一致，避免重复处理

## 计划步骤

### 阶段 A：模板和规则

- [ ] A1. 新建 `src/agent_harness/templates/common/.claude/commands/digest-meeting.md.tmpl`（完整的 7 步执行指令）
- [ ] A2. 更新 `src/agent_harness/templates/common/.claude/rules/superpowers-workflow.md` 添加 `/digest-meeting` 到技能清单和"何时使用哪个技能"段
- [ ] A3. 更新 `src/agent_harness/templates/common/.claude/commands/process-notes.md.tmpl`，在开头加"如果是多人讨论原始记录，考虑先用 `/digest-meeting`"的引导

### 阶段 B：skills-registry 注册

- [ ] B1. 在 `src/agent_harness/templates/superpowers/skills-registry.json` 添加 `digest-meeting` 条目（category=process，expected_in_lfg=false，因为它是 lfg 的前置源头）
- [ ] B2. 更新 `src/agent_harness/skills_lint.py` 的"common 层技能白名单"（如果有的话），让 digest-meeting 被识别为 common 技能

### 阶段 C：/lfg 接合

- [ ] C1. 更新 `src/agent_harness/templates/superpowers/.claude/commands/lfg.md.tmpl` 阶段 0.1，在判断"普通文本描述"之前加一条：**如果用户输入是文件路径且指向 `notes/` 下的原始讨论记录，建议先跑 `/digest-meeting`**

### 阶段 D：文档同步

- [ ] D1. 更新 `docs/product.md`：在"框架提供什么"下新增一项 `/digest-meeting`，并在 common 命令计数处同步（从 3 个 → 4 个）
- [ ] D2. 更新 `docs/architecture.md`：在模板结构段落补充 digest-meeting 命令文件的位置
- [ ] D3. 更新 `src/agent_harness/templates/superpowers/.claude/commands/use-superpowers.md.tmpl`（如影响决策树）

### 阶段 E：测试

- [ ] E1. 在 `tests/` 下新增 `test_digest_meeting.py`，覆盖：
  - 命令文件存在且格式正确
  - 命令引用的变量占位符齐全
  - init 生成后 `.claude/commands/digest-meeting.md` 存在
  - skills-registry 包含该条目
  - common 命令计数契约更新
- [ ] E2. 更新既有的 common 命令计数测试（如 `test_common_commands.py` 之类的，按实际名字定位）

### 阶段 F：Dogfood 同步

- [ ] F1. 跑 `make dogfood`，同步到本仓库的 `.claude/commands/`
- [ ] F2. 跑 `make ci` 全部通过

## 测试场景清单

### 正常路径
- 飞书妙记导出的讨论记录 → 能识别说话人 + 时间戳 + 章节结构 → 产出 6 类结构化信息
- 纯文本（无说话人标记）的讨论记录 → 按段落分割 → 仍能提取决策/需求/待办
- init 模式：产品文档为占位符 → 产出 notes/digested/xxx.md → 提示用户跑 /process-notes
- iterate 模式：产品文档已填充 → 产出 current-task.md → 提示用户跑 /lfg
- meta 项目：检测到 services/registry.yaml → 自动提示委托 /meta-create-task

### 边界情况
- `notes/` 目录不存在或为空 → 报错退出不创建空文件
- 讨论记录特别短（< 100 字）→ 提示用户补充，不强行提取
- 讨论记录混合多种格式（有的带说话人有的不带）→ 按行启发式判定
- 同一话题散落在讨论多处 → 合并到同一提取项
- 讨论中有分歧但最终达成共识 → 决策字段要保留分歧过程和最终结论
- 已有 `<!-- processed -->` 标记的文件 → 默认跳过（除非用户加 --force）

### 错误路径
- 文件编码异常（非 UTF-8）→ 给出清晰错误提示
- 讨论记录全是无关闲聊没有有效信号 → 展示"未提取到任何信号"并退出
- 用户在展示摘要阶段拒绝确认 → 不写入任何文件
- meta 检测失败（registry.yaml 存在但格式坏）→ 降级到普通流程而非崩溃
- 升级既有项目时 digest-meeting 命令文件已存在 → 走 upgrade 三方合并路径，不强覆盖

## 完成标准

- [ ] `harness init /tmp/test` 能在新项目生成 `.claude/commands/digest-meeting.md`
- [ ] 命令内容正确替换了 `{{project_name}}`、`{{project_type}}` 等占位符
- [ ] skills-registry.json 的 digest-meeting 条目可被 `harness skills lint` 检测通过
- [ ] `make ci` 全部通过（含新增 `test_digest_meeting.py`）
- [ ] `/digest-meeting` 在 init 模式下能正确串联到 `/process-notes`
- [ ] `/digest-meeting` 在 iterate 模式下产出的 current-task.md 能被 `/lfg` 正常识别
- [ ] meta 项目能检测并提示委托给 `/meta-create-task`
- [ ] `docs/product.md`、`docs/architecture.md` 同步更新
- [ ] `make dogfood` 后本仓库也有 `/digest-meeting` 命令可用
- [ ] `.agent-harness/bin/audit append` 每次修改关键文件后都有记录

## 风险与注意

- **风险 1**：discover 格式的启发式判定可能误判飞书妙记 vs 纯文本。**缓解**：在模板中写清楚"不确定就展示给用户看解析结果"
- **风险 2**：iterate 模式判定"文档是否占位符"会依赖具体文案字符串。**缓解**：用"功能列表"段下是否有非占位符行作为判定，而非字符串匹配某个特定词
- **风险 3**：讨论记录中的决策提炼有主观性。**缓解**：所有提取项必须标注"来自讨论第 N 段原话"vs"AI 综合推断"，方便用户校对
