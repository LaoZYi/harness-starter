# 实现计划：通用文档场景脚手架（D 方案）

**目标**：让 `harness init --type document /tmp/test-doc` 生成完整文档场景脚手架（5 个 doc skill + 3 个 lfg-profiles 文件 + 1 个 doc 类型 preset），同时不破坏现有 `/lfg`（写代码）行为
**架构**：复用 `templates/superpowers/.claude/commands/` 现有渲染管道；新增 `templates/common/.agent-harness/lfg-profiles/` 子目录承载场景档案骨架；新增 `presets/document.json` + `templates/document/.claude/rules/` 类型专属规则
**技术栈**：Python 3 标准库（无新依赖）、Markdown 模板、JSON、YAML（产物形态，不被运行时读取）
**设计文档**：[2026-04-27-doc-scenario-skeleton-spec.md](./2026-04-27-doc-scenario-skeleton-spec.md)（18 R-ID，评分 94/100）

---

## 计划层细化决策（spec 之外的微调，需要用户拍板才进入执行）

| # | 决策 | 理由 | 影响哪些任务 |
|---|------|------|------|
| **P1** | `/lfg-doc.md.tmpl` 写成精简版（~250 行）而非复制 `/lfg.md.tmpl`（758 行） | `/lfg` 758 行里 ~500 行是代码场景特化（Issue 解析 / squad 通道 / GitLab CI）；下层 rules/ 文件自动加载，反偷懒门禁等不需要内联；精简版易维护、易让 `/lfg` 与 `/lfg-doc` 并行演化 | 任务 B.5 |
| **P2** | 4 个 doc skill 长度对齐源 skill：`/draft-doc` ≈ `/tdd`（~150 行）、`/review-doc` ≈ `/multi-review`（~400 行）、`/outline-doc` 新写（~120 行）、`/finalize-doc` 新写（~180 行） | 既不臃肿也不过简；评审多人格在 doc 场景需要保留分工，所以 `/review-doc` 较长 | 任务 B.1-B.4 |
| **P3** | profile yaml 用注释丰富（每个 stage 解释"这步在做什么"），让人读 yaml 就能看懂流水线 | 本期 yaml 不被运行时读取，**唯一用途就是给人看**，注释是产品本身 | 任务 C.1, C.2 |
| **P4** | `presets/document.json` 的 `default_done_criteria` 写文档场景特有（章节完整 / 术语统一 / 引用可追溯）而非套用 cli-tool 模板 | 项目类型预设的核心价值就是 default_done_criteria 与场景对齐 | 任务 D.1 |
| **P5** | 端到端验证（任务 G.3）放在临时目录 `/tmp/doc-scaffold-test-<timestamp>`，每次跑前清理 | 避免污染开发机；时间戳防 stale 状态 | 任务 G.3 |

---

## 阶段 A：准备 + 基线锁定

- [ ] **A.1 — 锁定 `/lfg.md.tmpl` 的 baseline 哈希**（R5 行为零退化）  ← 实现 **R5**
  - 文件：`tests/test_doc_scenario_scaffold.py`（新建）
  - 操作：在测试文件中写第一个测试 `test_lfg_template_unchanged_in_behavior`，逻辑：
    ```python
    LFG_TMPL = ROOT / "src" / "agent_harness" / "templates" / "superpowers" / ".claude" / "commands" / "lfg.md.tmpl"
    # baseline: 计划开始时 lfg.md.tmpl 的 stage 调用 skill 集合
    EXPECTED_LFG_SKILL_CALLS = {
        "/ideate", "/brainstorm", "/spec", "/write-plan", "/plan-check",
        "/agent-design-check", "/tdd", "/source-verify", "/execute-plan",
        "/use-worktrees", "/careful", "/debug", "/multi-review", "/verify",
        "/git-commit", "/finish-branch", "/compound", "/lint-lessons",
        "/health", "/retro", "/cso", "/doc-release", "/squad",
        "/dispatch-agents", "/subagent-dev", "/recall",
    }
    def test_lfg_skill_calls_unchanged(self):
        text = LFG_TMPL.read_text(encoding="utf-8")
        for skill in EXPECTED_LFG_SKILL_CALLS:
            self.assertIn(skill, text, f"/lfg.md.tmpl missing {skill}")
    ```
  - 验证：`PYTHONPATH=src .venv/bin/python -m unittest tests.test_doc_scenario_scaffold.DocScenarioTests.test_lfg_skill_calls_unchanged -v`
  - 预期：测试通过（确认 baseline 集合正确）
  - 注：R5 放宽决策已在 current-task 锁定 — 检查 skill 调用集合不变即可，不卡字节

- [ ] **A.2 — 写其余契约测试占位（全部跑失败）**  ← 实现 **R1-R4, R6-R14**（测试位）
  - 文件：`tests/test_doc_scenario_scaffold.py`（追加）
  - 操作：写 13 个测试方法，每个先 `self.fail("not implemented")` 让 RED：
    ```python
    def test_doc_skills_in_registry(self): ...        # R3
    def test_doc_skill_templates_exist(self): ...     # R1, R2
    def test_lfg_doc_does_not_call_code_skills(self): ... # R4
    def test_lfg_profiles_skeleton_files_exist(self): ... # R6
    def test_profile_yaml_has_required_fields(self): ...  # R7
    def test_code_profile_matches_lfg(self): ...      # R8
    def test_doc_profile_matches_lfg_doc(self): ...   # R9
    def test_document_preset_exists(self): ...        # R10
    def test_init_document_renders_full_scaffold(self): ... # R11
    def test_init_other_types_get_lfg_profiles(self): ...  # R12
    def test_no_superpowers_skips_doc_skills(self): ...    # R13
    def test_lfg_audit_score_not_regressed(self): ...      # R14
    def test_lfg_doc_does_not_call_git_or_finish_branch(self): ... # R4 子项
    ```
  - 验证：`PYTHONPATH=src .venv/bin/python -m unittest tests.test_doc_scenario_scaffold -v 2>&1 | tail -20`
  - 预期：1 通过（A.1）+ 13 失败（"not implemented"）= 14 总计
  - **R-ID 映射**：本任务建立测试骨架，R1-R14 都将在后续步骤被 GREEN

---

## 阶段 B：5 个 skill 模板（先注册再写内容）

- [ ] **B.0 — 注册 5 个新 skill 到 skills-registry.json**  ← 实现 **R3**
  - 文件：`src/agent_harness/templates/superpowers/skills-registry.json`
  - 操作：在 `"skills": [...]` 数组末尾追加 5 个对象：
    ```json
    {
      "id": "lfg-doc",
      "name": "LFG-Doc 文档场景流水线",
      "category": "process",
      "one_line": "从需求到定稿的全自动文档流水线",
      "triggers": ["写文档", "写标书", "写规范", "写白皮书"],
      "decision_tree_label": "要写文档（非代码）？",
      "lfg_stage": [],
      "expected_in_lfg": false
    },
    {
      "id": "outline-doc",
      "name": "拟文档大纲",
      "category": "process",
      "one_line": "根据 spec 拟章节大纲、字数估算、引用占位",
      "triggers": ["拟提纲", "文档结构"],
      "decision_tree_label": null,
      "lfg_stage": [],
      "expected_in_lfg": false
    },
    {
      "id": "draft-doc",
      "name": "写文档草稿",
      "category": "implementation",
      "one_line": "基于 outline 写草稿（先 outline-pass 后 draft-pass）",
      "triggers": ["写草稿", "起笔"],
      "decision_tree_label": null,
      "lfg_stage": [],
      "expected_in_lfg": false
    },
    {
      "id": "review-doc",
      "name": "文档评审",
      "category": "review",
      "one_line": "4 角度并行评审：准确性 / 可读性 / 术语统一 / 完整性",
      "triggers": ["评审文档", "审稿"],
      "decision_tree_label": null,
      "lfg_stage": [],
      "expected_in_lfg": false
    },
    {
      "id": "finalize-doc",
      "name": "文档定稿",
      "category": "review",
      "one_line": "定稿前检查（无占位符 / R-ID 全覆盖 / 术语一致）+ 产出最终文件",
      "triggers": ["定稿", "完成文档"],
      "decision_tree_label": null,
      "lfg_stage": [],
      "expected_in_lfg": false
    }
    ```
  - 验证：`python -c "import json; d=json.load(open('src/agent_harness/templates/superpowers/skills-registry.json')); ids=[s['id'] for s in d['skills']]; assert set(['lfg-doc','outline-doc','draft-doc','review-doc','finalize-doc']) <= set(ids), ids; print('OK', len(ids), 'skills')"`
  - 预期：`OK 41 skills`（原 36 + 5）
  - 同步刷 `make dogfood` 后 `make skills-lint`（孤儿检查会跑）—— 预期暂时报"注册但缺文件"5 个 skill，B.1-B.5 完成后消除

- [ ] **B.1 — 写 `/outline-doc.md.tmpl`**  ← 实现 **R2**
  - 文件：`src/agent_harness/templates/superpowers/.claude/commands/outline-doc.md.tmpl`（新建）
  - 操作：~120 行，章节结构：
    1. 头部：`# 拟文档大纲（Outline-Doc）` + 一句话铁律 "先列骨架再填肉"
    2. **何时使用**：列 3 类触发场景（新建文档 / 重构现有文档 / 章节重排）
    3. **输入**：spec 里的 R-ID 列表 + 文档目标读者
    4. **5 步流程**：
       - (1) 列章节标题（一级 + 二级，估字数 + R-ID 覆盖映射）
       - (2) 每章一句话说"这章解决读者什么问题"
       - (3) 标关键引用占位（[ref:doc-X], [data:source-Y]）
       - (4) 自检：每条 R-ID 至少出现在 1 章；每章至少有 1 个明确论点
       - (5) 产出：`outline.md` 写入项目根目录或当前任务目录
    5. **反偷懒**：3 条特定 anti-rationalization
       - 「先写完再补大纲」：草稿期被错章节拖累的成本远大于先列大纲
       - 「凭直觉写就行」：模糊的章节关系会让评审无从下手
       - 「字数估算太麻烦」：没有字数预算就没有 plan 拆分依据
    6. **完成标准**：可机械判断——所有 R-ID 在 outline 中被 grep 到 + 章节字数总和 ≥ 用户说的下限
  - 验证：`test -f src/agent_harness/templates/superpowers/.claude/commands/outline-doc.md.tmpl && wc -l src/agent_harness/templates/superpowers/.claude/commands/outline-doc.md.tmpl`
  - 预期：文件存在，行数在 100-150 范围

- [ ] **B.2 — 写 `/draft-doc.md.tmpl`**  ← 实现 **R2**
  - 文件：`src/agent_harness/templates/superpowers/.claude/commands/draft-doc.md.tmpl`（新建）
  - 操作：~150 行，章节结构：
    1. 头部：`# 写文档草稿（Draft-Doc）` + 铁律 "两段法：outline-pass + draft-pass"
    2. **前置条件**：outline.md 存在 + spec.md 存在（grep 检查）
    3. **outline-pass**（先填骨架）：每章只写 3-5 行——这章想说什么、关键论点、依据来源（不要展开句子）
    4. **draft-pass**（再展开）：每章按 outline-pass 的骨架展开成完整段落
       - 每章产出后立即跑 grep 自检（关键术语是否一致、是否有 TODO/TBD）
       - 一次只展开一章，不要并行多章——并行会丢上下文连贯
    5. **不要做的**（反偷懒）：
       - 「跳过 outline-pass 直接展开」→ 缺骨架的草稿会反复改写
       - 「全文一次写完」→ 第二章的措辞会脱离第一章的铺垫
       - 「凭印象引用」→ [ref:X] 占位必须先在 spec 里登记
    6. **完成标准**：所有章节对应的 outline 段落都有 ≥ 1 段展开内容；无 TODO/TBD/待补充字面量
  - 验证：`test -f src/agent_harness/templates/superpowers/.claude/commands/draft-doc.md.tmpl`
  - 预期：文件存在，行数 130-170

- [ ] **B.3 — 写 `/review-doc.md.tmpl`**  ← 实现 **R2**
  - 文件：`src/agent_harness/templates/superpowers/.claude/commands/review-doc.md.tmpl`（新建）
  - 操作：~400 行，对齐 `/multi-review.md.tmpl` 但**评审角度替换为文档专用**：
    - 沿用 `/multi-review` 的 SubAgent 并行隔离架构（门禁 2）
    - 沿用 R-ID 反向追溯
    - 4 个评审人格替换为：
      | 人格 | 检查内容 | 输出格式 |
      |------|---------|---------|
      | 准确性审查员 | 事实是否有出处？数字 / 日期 / 引用是否可追溯？专有名词大小写是否正确？ | P0/P1/P2 + 可定位行号 |
      | 可读性审查员 | 段落长短是否均衡？术语首次出现是否有定义？长难句是否过载？ | P0/P1/P2 |
      | 术语统一审查员 | 同义词是否在全文用同一种表达？大小写归一是否一致（HTTP / http / Http）？ | grep 出所有变体 + 建议规范 |
      | 完整性审查员 | spec 中的 R-ID 是否每条都被覆盖？章节自检每章一个论点是否到位？ | R-ID 映射表 + missing 清单 |
    - 反偷懒（沿用 `/multi-review` 门禁 1 数量门禁）：4 审查员逐条回应，不批量 dismiss
    - **不**做：代码可读性、安全、性能、依赖等 `/multi-review` 的代码维度
    - 输出：`docs/superpowers/reviews/doc-review-<timestamp>.md`，与 `/multi-review` 不同目录
  - 验证：`test -f src/agent_harness/templates/superpowers/.claude/commands/review-doc.md.tmpl && grep -c "审查员" src/agent_harness/templates/superpowers/.claude/commands/review-doc.md.tmpl`
  - 预期：文件存在；至少出现 4 次"审查员"

- [ ] **B.4 — 写 `/finalize-doc.md.tmpl`**  ← 实现 **R2**
  - 文件：`src/agent_harness/templates/superpowers/.claude/commands/finalize-doc.md.tmpl`（新建）
  - 操作：~180 行，章节结构：
    1. 头部：`# 文档定稿（Finalize-Doc）` + 铁律 "定稿前 8 项必检，差一项不算完成"
    2. **前置**：草稿存在 + 评审报告 P0/P1 全部 close
    3. **8 项必检（数量门禁，门禁 1）**：
       1. 无占位符（grep `TODO|TBD|待补充|XXX|FIXME`）
       2. 每条 R-ID 在文档中可定位
       3. 引用占位（`[ref:X]` `[data:Y]`）全部解析为真实出处
       4. 术语统一（grep 已知大小写易错词）
       5. 章节字数符合 outline 估算（±20%）
       6. 评审 P0/P1 反馈全部 close（grep review 报告）
       7. 文档输出格式正确（markdown 校验：标题层级不跳级、列表前后空行）
       8. 文档元信息完整（标题、作者、日期、版本号）
    4. **每项三态记录**：✅ passed / ⚠️ skipped（附理由 + 用户确认）/ ❌ failed
    5. **不做**（明确）：`git add` / `git commit` / `git push` / 创建 PR / 切分支
       - 写文档的人可能完全不用 git
       - 如果用户确实想 commit，引导调 `/git-commit`（手动调，不自动）
    6. **产出**：定稿文件 + 一份 finalize-report.md（8 项检查记录）
    7. **反偷懒** 4 条：
       - 「8 项太多，跳几个」→ 数量门禁不允许批量 dismiss，必须逐项给状态
       - 「这条本来就这样」→ 必须给具体行号或文件位置作证据
       - 「评审说 P2 我先不管」→ P0/P1 必 close；P2 列入 known-issues 段
       - 「没必要这么麻烦」→ 文档发布出去后改一条术语就要传遍所有读者，定稿门禁是对外契约
  - 验证：`test -f src/agent_harness/templates/superpowers/.claude/commands/finalize-doc.md.tmpl && grep -c "git" src/agent_harness/templates/superpowers/.claude/commands/finalize-doc.md.tmpl`
  - 预期：文件存在；"git" 字样仅出现在"不做"段或引导段（≤ 5 次，避免误判 R4）

- [ ] **B.5 — 写 `/lfg-doc.md.tmpl`（精简版，按 P1 决策）**  ← 实现 **R1, R4**
  - 文件：`src/agent_harness/templates/superpowers/.claude/commands/lfg-doc.md.tmpl`（新建）
  - 操作：~250 行，章节结构（**对齐 `/lfg` 的概念但更精简**）：
    1. 头部：`# LFG-Doc — 从需求到定稿的全自动文档流水线`
       - 铁律 "先有规格，再动手"
       - 标注：「与 `/lfg` 同源；适用文档场景（标书 / 规范 / 白皮书 / 报告）；不调 git/commit/finish-branch」
    2. **阶段 0：任务理解**（精简版的 `/lfg` 阶段 0）
       - 检查 current-task.md
       - 复述任务 + 明确验收标准（含 R-ID）
       - 加载 L1 memory-index（同 `/lfg`）
       - **跳过**：squad 通道判断（写文档不需要并行多角色）、Issue 解析（写文档场景多数没有 Issue 编号）
    3. **阶段 1：构思**（条件触发，可跳过）
       - 仅大类文档（如白皮书）触发 → `/ideate`、`/brainstorm`
       - 标书 / 规范 / 报告等结构相对固定的可跳过
    4. **阶段 2：规格**（必做）
       - `/spec` —— 文档场景下"验收标准"是 R-ID 章节映射 + 完成度断言
    5. **阶段 3：大纲 + 计划**（必做）
       - `/outline-doc` 拟章节大纲
       - `/write-plan` 把每章拆成可执行写作步骤
       - `/plan-check`（条件：文档涉及 ≥ 5 章或多个引用源）
    6. **阶段 4：草稿**（必做）
       - `/draft-doc` 两段法
       - 加载 references/（如本项目有"写作风格指南"放 references/ 下）
    7. **阶段 5：评审**（必做）
       - `/review-doc` 4 人格并行
       - P0/P1 必 close，循环到 close
    8. **阶段 6：定稿**（必做）
       - `/finalize-doc` 8 项必检
       - **不调** `/git-commit` / `/finish-branch` / `/verify`
    9. **阶段 7：沉淀**（必做）
       - `/compound` 把写作教训写进 lessons.md
    10. **不做的事**（明确列）：
        - 不做 `/tdd`（写代码概念）
        - 不做 `/git-commit` / `/finish-branch`（写文档不强制 git）
        - 不做 `/multi-review`（用 `/review-doc` 替代）
        - 不做 `/verify`（用 `/finalize-doc` 内嵌检查替代）
        - 不做 `/debug` / `/health` / `/cso` / `/squad`
    11. **复用的下层规则**（自动加载，不内联）：anti-laziness（7 道门禁）、context-budget（Think in Code、单任务预算）、task-lifecycle（StuckDetector、L0-L3 分层加载）、agent-design（如用 `/dispatch-agents` 派子代理收集资料）
  - 验证：
    ```bash
    test -f src/agent_harness/templates/superpowers/.claude/commands/lfg-doc.md.tmpl
    # R4 grep：8 个代码场景 skill 不出现在调用位（允许在"不做的事"段被列出）
    cd src/agent_harness/templates/superpowers/.claude/commands
    awk '/## 不做的事/,/^---|^## /' lfg-doc.md.tmpl > /tmp/skip-section.txt
    awk 'NR==FNR{skip[$0];next} 1' /tmp/skip-section.txt lfg-doc.md.tmpl > /tmp/main.txt
    for s in /tdd /git-commit /finish-branch /multi-review /verify /debug /health /cso /squad; do
      if grep -q "$s" /tmp/main.txt; then echo "FAIL: $s appears outside 不做段"; exit 1; fi
    done
    echo OK
    ```
  - 预期：文件存在，~250 行，R4 grep 全部不出现在主体（仅在"不做"段提到）

---

## 阶段 C：lfg-profiles 骨架

- [ ] **C.1 — 写 `lfg-profiles/code.yaml.tmpl`**  ← 实现 **R6, R7, R8**
  - 文件：`src/agent_harness/templates/common/.agent-harness/lfg-profiles/code.yaml.tmpl`（新建）
  - 操作：完整内容（执行时直接写入）：
    ```yaml
    # lfg-profiles/code.yaml — 写代码场景的 /lfg 流水线骨架描述
    #
    # 用途：本期仅作描述，不被任何命令运行时读取。
    # 未来：B 阶段会让 /lfg 在阶段 0 读取本文件，AI 推断匹配场景档案后用户确认。
    # 不要：手工编辑此文件来"配置 /lfg"——本期 /lfg 行为完全由 lfg.md.tmpl 决定。

    schema_version: 1
    name: code
    description: 写代码场景的流水线骨架（与 /lfg 阶段对齐）

    stages:
      - id: ideate
        skill: ideate
        description: 多角度构思（仅"大"复杂度触发）
        optional: true

      - id: spec
        skill: spec
        description: 把模糊需求转为含 R-ID 的可测试验收标准

      - id: plan
        skill: write-plan
        description: 2-5 分钟粒度的实施计划

      - id: plan-check
        skill: plan-check
        description: 8+1 维度计划质量校验
        optional: true

      - id: execute
        skill: tdd
        description: RED-GREEN-REFACTOR

      - id: verify
        skill: verify
        description: 完成前穷举验证（测试、lint、跨平台行为）

      - id: review
        skill: multi-review
        description: 6 人格并行评审

      - id: commit
        skill: git-commit
        description: 结构化原子 commit

      - id: compound
        skill: compound
        description: 沉淀教训到 lessons.md
    ```
  - 验证：
    ```bash
    test -f src/agent_harness/templates/common/.agent-harness/lfg-profiles/code.yaml.tmpl
    grep -E "^(schema_version|name|description|stages):" src/agent_harness/templates/common/.agent-harness/lfg-profiles/code.yaml.tmpl | wc -l
    # 必须 = 4
    ```
  - 预期：文件存在，4 个顶级字段 grep 命中

- [ ] **C.2 — 写 `lfg-profiles/doc.yaml.tmpl`**  ← 实现 **R6, R7, R9**
  - 文件：`src/agent_harness/templates/common/.agent-harness/lfg-profiles/doc.yaml.tmpl`（新建）
  - 操作：完整内容：
    ```yaml
    # lfg-profiles/doc.yaml — 写文档场景的 /lfg-doc 流水线骨架描述
    #
    # 用途：本期仅作描述，不被任何命令运行时读取。
    # 未来：B 阶段会让 /lfg 在阶段 0 读取本文件，AI 推断匹配场景档案后用户确认。
    # 不要：手工编辑此文件来"配置 /lfg-doc"——本期 /lfg-doc 行为完全由 lfg-doc.md.tmpl 决定。

    schema_version: 1
    name: doc
    description: 写文档场景的流水线骨架（与 /lfg-doc 阶段对齐）

    stages:
      - id: ideate
        skill: ideate
        description: 大类文档（白皮书等）才触发，标书/规范可跳过
        optional: true

      - id: spec
        skill: spec
        description: 文档验收标准 = R-ID 章节映射 + 完成度断言

      - id: outline
        skill: outline-doc
        description: 拟章节大纲、字数估算、引用占位

      - id: plan
        skill: write-plan
        description: 把章节拆成可执行写作步骤

      - id: draft
        skill: draft-doc
        description: 两段法 outline-pass + draft-pass

      - id: review
        skill: review-doc
        description: 4 人格评审（准确性 / 可读性 / 术语 / 完整性）

      - id: finalize
        skill: finalize-doc
        description: 8 项必检定稿；不调 git-commit / finish-branch

      - id: compound
        skill: compound
        description: 沉淀写作教训到 lessons.md
    ```
  - 验证：同 C.1
  - 预期：文件存在，4 个顶级字段 grep 命中

- [ ] **C.3 — 写 `lfg-profiles/README.md.tmpl`**  ← 实现 **R6**
  - 文件：`src/agent_harness/templates/common/.agent-harness/lfg-profiles/README.md.tmpl`（新建）
  - 操作：内容：
    ```markdown
    # LFG Profiles（场景档案）

    本目录存放"场景档案"骨架，描述不同场景下 `/lfg` / `/lfg-doc` 等流水线命令调用哪些 skill。

    ## 当前状态：纯描述

    本期（D 方案）这些 yaml 文件**不被任何命令运行时读取**。`/lfg` 的行为完全由 `.claude/commands/lfg.md.tmpl` 决定，`/lfg-doc` 同理。

    yaml 文件的唯一用途：让人读了知道"哪个流水线命令调了哪些 skill"，作为以后做"AI 推断场景档案 + 用户确认"（B 方案）的数据基础。

    ## 当前的档案

    - `code.yaml` — `/lfg`（写代码）流水线
    - `doc.yaml` — `/lfg-doc`（写文档）流水线

    ## Schema（最小可行版本）

    ```yaml
    schema_version: 1
    name: <profile-id>
    description: <一句话描述>
    stages:
      - id: <stage-id>
        skill: <skill-name>
        description: <这步在做什么>
        optional: true   # 默认 false
    ```

    ## 未来方向（B 阶段）

    1. `/lfg` 启动时读 `lfg-profiles/*.yaml`
    2. AI 根据任务描述猜匹配哪份档案
    3. 跟用户确认 → 按档案执行
    4. 用户用熟后自己加新档案（如 `video.yaml`、`presentation.yaml`）

    ## 不要做的事

    - **不要**通过编辑 yaml 来"配置 /lfg 的行为"——本期 /lfg 不读它
    - **不要**把档案当配置中心扩字段——schema 演化走 schema_version 升级（1 → 2）
    - **不要**手工生成与 `/lfg.md.tmpl` 实际调用 skill 不一致的档案——契约测试会失败
    ```
  - 验证：`test -f src/agent_harness/templates/common/.agent-harness/lfg-profiles/README.md.tmpl`
  - 预期：文件存在

---

## 阶段 D：document 项目类型

- [ ] **D.1 — 写 `presets/document.json`**  ← 实现 **R10**（按 P4 决策）
  - 文件：`src/agent_harness/presets/document.json`（新建）
  - 操作：完整内容：
    ```json
    {
      "behavior_change_definition": "任何会改变文档结构（章节）、术语规范、引用格式、定稿检查项的改动都算行为变化；下游读者和评审管道可能依赖这些约定。",
      "architecture_focus": "优先描述章节结构（一级/二级/三级）、术语表位置、引用源管理、版本与变更记录。",
      "release_checks": [
        "确认每条 R-ID 在文档中可定位",
        "确认无占位符（TODO / TBD / 待补充）残留",
        "确认术语全文一致（含大小写归一）",
        "确认引用占位全部解析为真实出处",
        "确认评审 P0 / P1 反馈全部 close"
      ],
      "workflow_notes": "文档项目的产出物是 markdown / docx 等而非可执行代码；review 角度以准确性/可读性/术语统一/完整性为主，不做代码可读性/安全/性能维度。",
      "default_done_criteria": [
        "所有章节按 outline 字数估算 ±20% 内完成",
        "每条 R-ID 在文档中至少出现 1 次且可定位",
        "review-doc 4 人格评审 P0/P1 全部 close",
        "finalize-doc 8 项必检全部 ✅ 或带理由 skipped",
        "无 TODO / TBD / 待补充等占位符残留"
      ],
      "workflow_skills_summary": "文档项目重点技能：`/lfg-doc`（端到端文档流水线）、`/outline-doc`（拟提纲）、`/draft-doc`（两段法草稿）、`/review-doc`（4 人格评审）、`/finalize-doc`（8 项必检定稿）",
      "exclude_rules": ["api.md", "database.md", "frontend.md"]
    }
    ```
  - 验证：`python -c "import json; d=json.load(open('src/agent_harness/presets/document.json')); print('OK' if all(k in d for k in ['behavior_change_definition','default_done_criteria','workflow_skills_summary']) else 'FAIL')"`
  - 预期：`OK`

- [ ] **D.2 — 写 `templates/document/.claude/rules/document-conventions.md.tmpl`**  ← 实现 **R10**（document 类型规则）
  - 文件：`src/agent_harness/templates/document/.claude/rules/document-conventions.md.tmpl`（新建，需先创建目录）
  - 操作：~80 行规则模板，含：
    1. **章节命名**：一级用 `# 标题`、二级用 `##`，不跳级
    2. **术语表**：根目录 `glossary.md`，首次出现的术语在术语表中定义
    3. **引用格式**：`[ref:doc-name#section]` 内部引用 / `[ext:url-or-citation]` 外部引用
    4. **版本与日期**：每个文档头部含 `---\nversion: 1.0\ndate: YYYY-MM-DD\nstatus: draft|review|final\n---`
    5. **变更记录**：长文档（≥ 1000 字）末尾有 changelog 段
    6. **评审痕迹**：评审反馈记录在 `.review/<doc>-<reviewer>-<ts>.md`，不混入正文
  - 验证：`test -f src/agent_harness/templates/document/.claude/rules/document-conventions.md.tmpl`
  - 预期：文件存在

- [ ] **D.3 — 把 `document` 加入项目类型白名单（如有硬编码）**  ← 实现 **R10**
  - 操作：先 grep 是否有硬编码白名单：
    ```bash
    grep -rn "backend-service\|cli-tool\|web-app" src/agent_harness/*.py | grep -v "test_\|templates/" | head -20
    ```
  - 如果有 → 在白名单里加 `"document"`；如果是动态从 `presets/*.json` 列表读 → D.1 完成自动生效
  - 验证：`PYTHONPATH=src .venv/bin/python -c "from agent_harness.cli import main; main(['init','--type','document','/tmp/test-doc-type-only','--non-interactive','--assess-only'])" 2>&1 | head -5`
  - 预期：不报"未知项目类型"错（assess-only 只走探测和评估，不写文件）

---

## 阶段 E：让所有契约测试 GREEN

- [ ] **E.1 — 让 R1, R2, R3 测试通过（template & registry 一致性）**  ← 实现 **R1, R2, R3**
  - 文件：`tests/test_doc_scenario_scaffold.py`（实现已占位的测试）
  - 操作：替换占位的 `self.fail("not implemented")` 为真实断言：
    ```python
    def test_doc_skill_templates_exist(self):
        for skill in ["lfg-doc", "outline-doc", "draft-doc", "review-doc", "finalize-doc"]:
            p = ROOT / "src/agent_harness/templates/superpowers/.claude/commands" / f"{skill}.md.tmpl"
            self.assertTrue(p.is_file(), f"missing {p}")

    def test_doc_skills_in_registry(self):
        import json
        reg = json.loads((ROOT / "src/agent_harness/templates/superpowers/skills-registry.json").read_text())
        ids = {s["id"] for s in reg["skills"]}
        for skill in ["lfg-doc", "outline-doc", "draft-doc", "review-doc", "finalize-doc"]:
            self.assertIn(skill, ids)
            entry = next(s for s in reg["skills"] if s["id"] == skill)
            self.assertFalse(entry["expected_in_lfg"], f"{skill} should be expected_in_lfg=false")
    ```
  - 验证：`PYTHONPATH=src .venv/bin/python -m unittest tests.test_doc_scenario_scaffold.DocScenarioTests.test_doc_skill_templates_exist tests.test_doc_scenario_scaffold.DocScenarioTests.test_doc_skills_in_registry -v`
  - 预期：2 通过

- [ ] **E.2 — 让 R4 测试通过（lfg-doc 不调代码 skill）**  ← 实现 **R4**
  - 文件：`tests/test_doc_scenario_scaffold.py`
  - 操作：
    ```python
    def test_lfg_doc_does_not_call_code_skills(self):
        p = ROOT / "src/agent_harness/templates/superpowers/.claude/commands/lfg-doc.md.tmpl"
        text = p.read_text(encoding="utf-8")
        # 拆出"不做的事"段（明示列举，不算违反）
        skip_section = ""
        in_skip = False
        for line in text.splitlines():
            if line.startswith("## ") and ("不做" in line or "禁止" in line):
                in_skip = True
            elif line.startswith("## ") and in_skip:
                in_skip = False
            elif in_skip:
                skip_section += line + "\n"
        main = text.replace(skip_section, "")
        for forbidden in ["/tdd", "/git-commit", "/finish-branch", "/multi-review",
                          "/verify", "/debug", "/health", "/cso", "/squad"]:
            self.assertNotIn(forbidden, main,
                f"/lfg-doc.md.tmpl 主体（非'不做'段）含禁用 skill {forbidden}")

    def test_lfg_doc_does_not_call_git_or_finish_branch(self):
        # 二级保险：再单独检查一次最关键的 git 相关
        p = ROOT / "src/agent_harness/templates/superpowers/.claude/commands/lfg-doc.md.tmpl"
        text = p.read_text(encoding="utf-8")
        # 允许在"不做的事"段提及，但不应在主流程调用
        self.assertLess(text.count("/git-commit"), 3,
                        "/git-commit 在 lfg-doc 主体中出现次数过多")
        self.assertLess(text.count("/finish-branch"), 3,
                        "/finish-branch 在 lfg-doc 主体中出现次数过多")
    ```
  - 验证：`PYTHONPATH=src .venv/bin/python -m unittest tests.test_doc_scenario_scaffold.DocScenarioTests.test_lfg_doc_does_not_call_code_skills tests.test_doc_scenario_scaffold.DocScenarioTests.test_lfg_doc_does_not_call_git_or_finish_branch -v`
  - 预期：2 通过

- [ ] **E.3 — 让 R6, R7, R8, R9 测试通过（profile yaml 骨架与一致性）**  ← 实现 **R6, R7, R8, R9**
  - 文件：`tests/test_doc_scenario_scaffold.py`
  - 操作：
    ```python
    PROFILE_DIR = ROOT / "src/agent_harness/templates/common/.agent-harness/lfg-profiles"

    def test_lfg_profiles_skeleton_files_exist(self):
        for fname in ["code.yaml.tmpl", "doc.yaml.tmpl", "README.md.tmpl"]:
            p = PROFILE_DIR / fname
            self.assertTrue(p.is_file(), f"missing {p}")

    def test_profile_yaml_has_required_fields(self):
        # grep 断言（不引 PyYAML，决策 P3 + spec 第 3 微决策）
        for yaml_name in ["code.yaml.tmpl", "doc.yaml.tmpl"]:
            text = (PROFILE_DIR / yaml_name).read_text(encoding="utf-8")
            self.assertIn("schema_version: 1", text)
            self.assertIn("name:", text)
            self.assertIn("description:", text)
            self.assertIn("stages:", text)

    def test_code_profile_matches_lfg(self):
        # code.yaml stages 列出的 skill 必须全部在 lfg.md.tmpl 中出现
        text = (PROFILE_DIR / "code.yaml.tmpl").read_text(encoding="utf-8")
        # 简易解析（提取 "skill: <name>" 行）
        import re
        skills_in_yaml = set(re.findall(r"^\s*skill:\s*([\w-]+)", text, re.MULTILINE))
        lfg_text = (ROOT / "src/agent_harness/templates/superpowers/.claude/commands/lfg.md.tmpl").read_text()
        for skill in skills_in_yaml:
            self.assertIn(f"/{skill}", lfg_text,
                f"code.yaml lists /{skill} but /lfg.md.tmpl does not call it")

    def test_doc_profile_matches_lfg_doc(self):
        text = (PROFILE_DIR / "doc.yaml.tmpl").read_text(encoding="utf-8")
        import re
        skills_in_yaml = set(re.findall(r"^\s*skill:\s*([\w-]+)", text, re.MULTILINE))
        lfg_doc_text = (ROOT / "src/agent_harness/templates/superpowers/.claude/commands/lfg-doc.md.tmpl").read_text()
        for skill in skills_in_yaml:
            self.assertIn(f"/{skill}", lfg_doc_text,
                f"doc.yaml lists /{skill} but /lfg-doc.md.tmpl does not call it")
    ```
  - 验证：`PYTHONPATH=src .venv/bin/python -m unittest tests.test_doc_scenario_scaffold -v 2>&1 | grep -E "(test_lfg_profiles|test_profile_yaml|test_code_profile|test_doc_profile)"`
  - 预期：4 通过

- [ ] **E.4 — 让 R10 测试通过（document preset）**  ← 实现 **R10**
  - 文件：`tests/test_doc_scenario_scaffold.py`
  - 操作：
    ```python
    def test_document_preset_exists(self):
        import json
        p = ROOT / "src/agent_harness/presets/document.json"
        self.assertTrue(p.is_file())
        d = json.loads(p.read_text())
        for k in ["behavior_change_definition", "architecture_focus", "release_checks",
                  "default_done_criteria", "workflow_skills_summary", "exclude_rules"]:
            self.assertIn(k, d)
    ```
  - 验证：`PYTHONPATH=src .venv/bin/python -m unittest tests.test_doc_scenario_scaffold.DocScenarioTests.test_document_preset_exists -v`
  - 预期：通过

- [ ] **E.5 — 让 R11, R12, R13 测试通过（端到端 init 渲染）**  ← 实现 **R11, R12, R13**
  - 文件：`tests/test_doc_scenario_scaffold.py`
  - 操作：
    ```python
    import tempfile, subprocess, os

    def _run_init(self, type_arg, target_dir, no_superpowers=False):
        cmd = [sys.executable, "-m", "agent_harness", "init",
               "--type", type_arg, str(target_dir), "--non-interactive"]
        if no_superpowers:
            cmd.append("--no-superpowers")
        env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
        subprocess.run(cmd, check=True, env=env, capture_output=True)

    def test_init_document_renders_full_scaffold(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "doc-proj"
            self._run_init("document", target)
            for skill in ["lfg-doc", "outline-doc", "draft-doc", "review-doc", "finalize-doc"]:
                self.assertTrue((target / ".claude/commands" / f"{skill}.md").is_file())
            for f in ["code.yaml", "doc.yaml", "README.md"]:
                self.assertTrue((target / ".agent-harness/lfg-profiles" / f).is_file())

    def test_init_other_types_get_lfg_profiles(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "code-proj"
            self._run_init("backend-service", target)
            # 现有 /lfg 仍存在
            self.assertTrue((target / ".claude/commands/lfg.md").is_file())
            # 新增的 lfg-profiles 也渲染（universally available）
            self.assertTrue((target / ".agent-harness/lfg-profiles/code.yaml").is_file())
            self.assertTrue((target / ".agent-harness/lfg-profiles/doc.yaml").is_file())

    def test_no_superpowers_skips_doc_skills(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "no-sp-doc"
            self._run_init("document", target, no_superpowers=True)
            # /lfg-doc 不渲染（与 /lfg 行为一致）
            self.assertFalse((target / ".claude/commands/lfg-doc.md").is_file())
            # 但 lfg-profiles 在 common/ 下，应仍渲染
            self.assertTrue((target / ".agent-harness/lfg-profiles/doc.yaml").is_file())
    ```
  - 验证：`PYTHONPATH=src .venv/bin/python -m unittest tests.test_doc_scenario_scaffold.DocScenarioTests.test_init_document_renders_full_scaffold tests.test_doc_scenario_scaffold.DocScenarioTests.test_init_other_types_get_lfg_profiles tests.test_doc_scenario_scaffold.DocScenarioTests.test_no_superpowers_skips_doc_skills -v`
  - 预期：3 通过

- [ ] **E.6 — 让 R14 测试通过（lfg audit 不退化）**  ← 实现 **R14**
  - 文件：`tests/test_doc_scenario_scaffold.py`
  - 操作：
    ```python
    def test_lfg_audit_score_not_regressed(self):
        result = subprocess.run(
            [sys.executable, "-m", "agent_harness", "lfg", "audit", "--json"],
            env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
            capture_output=True, text=True
        )
        # exit 0 = 通过门禁；exit 1 = 低于阈值；exit 2 = infra 失败
        self.assertEqual(result.returncode, 0,
            f"harness lfg audit failed: {result.stderr}")
        import json
        data = json.loads(result.stdout)
        self.assertGreaterEqual(data["score_total"], 7.0)
    ```
  - 验证：`PYTHONPATH=src .venv/bin/python -m unittest tests.test_doc_scenario_scaffold.DocScenarioTests.test_lfg_audit_score_not_regressed -v`
  - 预期：通过

---

## 阶段 F：文档同步 + dogfood

- [ ] **F.1 — 更新 `docs/product.md`**  ← 实现 **R16**
  - 文件：`docs/product.md`
  - 操作：
    1. 第 67-70 行「支持的项目类型（9 种）」改为 「（10 种）」，列表加 `document`
    2. 第 73-92 行「meta 项目类型」节后追加新节「document 项目类型」：
       ```markdown
       ### document 项目类型

       document 项目以文档（标书 / 规范 / 白皮书 / 报告等）为主要产物，不含可执行代码。

       初始化后用 `/lfg-doc` 端到端流水线：
       - `/outline-doc` — 拟章节大纲、字数估算、引用占位
       - `/draft-doc` — 两段法（outline-pass + draft-pass）写草稿
       - `/review-doc` — 4 人格并行评审（准确性 / 可读性 / 术语统一 / 完整性）
       - `/finalize-doc` — 8 项必检定稿；不调 git-commit / finish-branch

       与 `/lfg`（写代码）的关键区别：不调 `/tdd` / `/git-commit` / `/finish-branch` / `/multi-review` / `/verify` / `/debug` / `/health` / `/cso` / `/squad`。
       ```
    3. 第 17 行附近"持续演进"段插入新节 `0.（如有）` 简述本次新增（与现有按时间倒序的格式一致）
  - 验证：`grep -c "document" docs/product.md`
  - 预期：grep 命中 ≥ 5 次

- [ ] **F.2 — 更新 `docs/architecture.md`**  ← 实现 **R17**
  - 文件：`docs/architecture.md`
  - 操作：
    1. 「资源层」节加一行：
       ```
       - `src/agent_harness/templates/common/.agent-harness/lfg-profiles/`：场景档案骨架（code.yaml / doc.yaml / README.md），本期不被运行时读取，给将来 B 阶段 AI 推断匹配档案留位置。
       ```
    2. 「测试层」节"680 个回归测试" → 更新为新数字（约 680 + 14 = 694）
    3. 第 60 行附近，"templates/<type>/" 段加 `document` 类型描述
  - 验证：`grep -c "lfg-profiles\|document" docs/architecture.md`
  - 预期：grep 命中 ≥ 3 次

- [ ] **F.3 — 更新 `docs/runbook.md`**  ← 实现 **R18**
  - 文件：`docs/runbook.md`
  - 操作：在 `harness init` 用法段加一行：
    ```bash
    harness init <target> --type document   # 初始化以文档为主要产物的项目
    ```
  - 验证：`grep -c "type document" docs/runbook.md`
  - 预期：grep 命中 ≥ 1 次

- [ ] **F.4 — 跑 `make dogfood` 同步框架自身的产物**  ← 实现 **R15 间接**
  - 操作：`make dogfood` 把 templates/ 中的新增内容渲染到 dogfood 目录（即本仓库自身的 .claude/ 和 .agent-harness/ 反映模板变化）
  - 验证：
    ```bash
    make dogfood
    ls .claude/commands/ | grep -E "(lfg-doc|outline-doc|draft-doc|review-doc|finalize-doc)" | wc -l
    ls .agent-harness/lfg-profiles/ 2>/dev/null | wc -l
    ```
  - 预期：5 个 doc skill 在 .claude/commands/ 出现 + 3 个文件在 .agent-harness/lfg-profiles/

---

## 阶段 G：终验 + 沉淀

- [ ] **G.1 — `make ci` 全绿**  ← 实现 **R15**
  - 操作：`make ci`（= check + typecheck + skills-lint + deadcode + shellcheck-hooks + test）
  - 验证：退出码 0
  - 预期：全部通过；测试数从 632 涨到 ~646

- [ ] **G.2 — 端到端跑一次 `harness init --type document /tmp/...`**  ← 实现 **R11**
  - 操作（按 P5 决策）：
    ```bash
    rm -rf /tmp/doc-scaffold-test-* 2>/dev/null
    TARGET=/tmp/doc-scaffold-test-$(date +%s)
    PYTHONPATH=src .venv/bin/python -m agent_harness init --type document "$TARGET" --non-interactive
    echo "--- 5 个 skill ---"
    ls "$TARGET/.claude/commands/" | grep -E "(lfg-doc|outline-doc|draft-doc|review-doc|finalize-doc)" | sort
    echo "--- lfg-profiles ---"
    ls "$TARGET/.agent-harness/lfg-profiles/"
    echo "--- preset 元数据 ---"
    grep -E "project_type|workflow_skills" "$TARGET/.agent-harness/project.json" 2>/dev/null
    echo "--- /lfg 仍渲染 ---"
    ls "$TARGET/.claude/commands/lfg.md"
    ```
  - 预期：5 skill + 3 profile 文件 + project_type=document + lfg.md 仍存在

- [ ] **G.3 — `harness lfg audit` 验证不退化**  ← 实现 **R14**
  - 操作：`PYTHONPATH=src .venv/bin/python -m agent_harness lfg audit --json | python -c "import sys, json; d=json.load(sys.stdin); print(d['score_total'])"`
  - 预期：score ≥ 7.0（理想情况下与 9.9 持平或微涨——本次新增技能让"Skills 编排"维度可能轻微提升）

- [ ] **G.4 — 进入"待验证"状态，等用户拍板**
  - 操作：
    1. 在 `.agent-harness/current-task.md` 顶部状态改为 `## 状态：待验证`
    2. 更新所有 checkbox 为 [x]
    3. 写"如何验证"段：列 G.2 的命令 + 期望输出 + 用户应该自己跑一遍
    4. **不**自动写 task-log，**不**清空 current-task —— 等用户说"通过"
  - 验证：`grep "待验证" .agent-harness/current-task.md`
  - 预期：grep 命中

- [ ] **G.5 — 用户验证通过后归档（人工触发）**
  - 等用户回"可以" / "通过" 后才执行：
    1. 在 `.agent-harness/task-log.md` 末尾追加任务记录（含 R-ID 全表 satisfied 状态）
    2. 清空 `.agent-harness/current-task.md`（保留头部 + 空模板）
    3. 跑 `/compound` 沉淀本次教训（候选教训：「场景多样化的脚手架要走 D 方案而非 B」、「写 skill 时仍要复用下层 rules 不内联」等）
    4. 跑 `.agent-harness/bin/audit append --file task-log.md --op append --summary "..."`
    5. 跑 `.agent-harness/bin/memory rebuild .` 刷 memory-index 的"最近任务"段

---

## R-ID 覆盖表

| R-ID | 描述（一句话） | 实现 task | 验证位置 |
|------|--------------|----------|---------|
| R1 | `/lfg-doc` 模板存在 | B.5 | E.1 |
| R2 | 4 个 doc 专用 skill 模板存在 | B.1, B.2, B.3, B.4 | E.1 |
| R3 | 5 个新 skill 在 registry 注册 | B.0 | E.1 |
| R4 | `/lfg-doc` 不调 8 个代码场景 skill | B.5 | E.2 |
| R5 | `/lfg.md.tmpl` 行为零退化（skill 调用集合不变） | （隐含，A.1 baseline 守卫） | A.1 |
| R6 | 3 个 lfg-profiles 骨架文件存在 | C.1, C.2, C.3 | E.3 |
| R7 | profile yaml 含必填字段（schema_version / name / description / stages） | C.1, C.2 | E.3 |
| R8 | code.yaml stage→skill 与 /lfg 实际调用一致 | C.1 | E.3 |
| R9 | doc.yaml stage→skill 与 /lfg-doc 实际调用一致 | C.2 | E.3 |
| R10 | `presets/document.json` 存在并被白名单接受 | D.1, D.2, D.3 | E.4 |
| R11 | `harness init --type document` 端到端渲染完整脚手架 | B.0-D.3 全部完成后 | E.5, G.2 |
| R12 | `harness init --type backend-service` 现有行为零退化 + 新增 lfg-profiles 骨架 | C.1-C.3 | E.5 |
| R13 | `--no-superpowers` 跳过 5 个 doc skill | B.5 + initializer 行为（无需改代码，自动） | E.5 |
| R14 | `harness lfg audit ≥ 7.0` | （隐含，全部任务完成后跑一次） | E.6, G.3 |
| R15 | 现有 632 测试全通过 | 全程不动现有代码 | G.1 |
| R16 | `docs/product.md` 同步 | F.1 | F.1 grep |
| R17 | `docs/architecture.md` 同步 | F.2 | F.2 grep |
| R18 | `docs/runbook.md` 同步 | F.3 | F.3 grep |

**所有 R-ID 都有任务映射，无 out-of-scope 项**。

---

## 自审清单

- [x] 每个任务都有文件路径
- [x] 每个任务都有验证命令
- [x] 代码块没有占位符（仅 P1-P5 计划层决策需要用户拍板，不是占位）
- [x] 任务之间显式列出前置条件（B.0 在 B.1-B.5 前；E.* 在 B/C/D 后；G.* 在最后）
- [x] 计划与设计文档一致（spec 18 R-ID 全覆盖）
- [x] 总任务量合理（25 步，符合 10-30 步范围）
- [x] R-ID 覆盖表完整（18 / 18 全映射）
- [x] 文档爆炸门禁评估完成（7 项纯文档，未超 10 阈值）

## 预计工作量

按每步 2-5 分钟 + 测试调试余量：
- 阶段 A（2 步）：~15 分钟
- 阶段 B（6 步，包含 5 个 skill 模板编写）：~90 分钟
- 阶段 C（3 步）：~15 分钟
- 阶段 D（3 步）：~20 分钟
- 阶段 E（6 步）：~30 分钟
- 阶段 F（4 步）：~25 分钟
- 阶段 G（5 步）：~20 分钟（不含 G.5 等用户验证）

**合计 ~3.5-4 小时实现 + 等用户验证**
