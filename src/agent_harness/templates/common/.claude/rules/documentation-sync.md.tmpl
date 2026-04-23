---
description: 代码变更后必须同步更新对应文档
---

# 文档同步规则

改了代码就必须改文档，禁止堆到任务结束批量更新。

## 映射表

| 代码变更类型 | 必须更新的文档 | 更新什么 | 由谁更新 |
|---|---|---|---|
| 新增、修改、移除功能 | `docs/product.md` | 功能列表和完成标准 checkbox | 执行改动的 agent |
| 改了文件结构或模块边界 | `docs/architecture.md`（dev-map） | 文件结构、模块职责 | **执行改动的 agent**（谁动代码谁改地图） |
| 改了运行、测试、部署方式 | `docs/runbook.md` | 对应命令和步骤 | 执行改动的 agent |
| 改了协作约束或硬规则 | `AGENTS.md` | 硬规则列表 | 改规则的 agent |

## dev-map（`docs/architecture.md`）的所有权约定

> 来源：腾讯 JK Launcher 团队《Harness Engineering 工程化落地》——开发导航地图必须由「动代码的 agent」顺手维护，而不是由 PM / 规划者单独维护，否则地图年久失修，AI 下次进项目会在已有模块上重复造轮子。

- **谁更新**：执行代码改动的 agent（/execute-plan 的执行者、/squad 的 builder、直接 `/tdd` 的开发者）——不是规划者、不是 PM
- **什么时候更新**：改动涉及**模块边界 / 文件结构 / 关键流程入口**时，**立即**更新。不许堆到任务结束批量改，也不许"下次再补"
- **更新什么**：
  - 新模块 → 加一个条目说它在哪、负责什么、主要入口函数 / 文件
  - 改了模块职责 → 改条目内容
  - 删了模块 / 合并了模块 → 同步删 / 合条目
- **反模式**：
  - ❌ "这次改动太小，地图不用动"——只要触及模块边界就要动
  - ❌ PM / 规划者替开发者改地图——他们没写代码，不知道真实长什么样
  - ❌ 把 architecture.md 当静态文档年度更新——它是活的索引，不是年报

## 执行要求

- 每完成 **1 个功能点**就立即更新，不是做完所有功能再更新
- 如果一次改动涉及多个文档，全部更新后再进入下一个功能点
- `docs/product.md` 中的 checkbox：实现完成改为 `[x]`，发现不可行改为 `[-]` 并注明原因

## 目录导航层（ABSTRACT.md / OVERVIEW.md）

> 来源：volcengine/OpenViking 的「文件系统即上下文」设计——每个目录用 L0 一句话摘要 + L1 导航视图承载语义，AI 进项目时按"先扫摘要 → 再读导航 → 最后读原文"的三段式定位，避免直接读全量文件挤爆上下文。

### 适用范围

下列目录**必须**维护 `ABSTRACT.md` + `OVERVIEW.md` 两个文件：

| 目录 | 为什么需要 |
|---|---|
| `.agent-harness/` | Agent 持久化状态根——current-task / memory-index / lessons / task-log / references / agents / squad / bin 等新进 AI 必读入口 |
| `.agent-harness/references/` | L2 温知识入口，多个 checklist 需要按场景索引 |

> 其它目录默认不强制。后续按需扩展（例如 `docs/decisions/` 累积 ADR 后可加），由提议者改本规则白名单。
>
> **注意**：不要把 `ABSTRACT.md` / `OVERVIEW.md` 放进 `.claude/commands/`——Claude Code 会把该目录下任何 `.md` 自动注册为 slash command。技能的分类导航已在 `.claude/rules/superpowers-workflow.md` 覆盖。

### 内容约束

- **`ABSTRACT.md`**：单段 ≤ 100 token（约 50 汉字 / 200 字符）。一句话说"这个目录是什么、为谁服务"。供 `/recall --map` 全项目导航
- **`OVERVIEW.md`**：≤ 2k token（约 1000 汉字 / 4000 字符）。包含：
  1. 目录职责（一段话展开 ABSTRACT）
  2. 关键文件列表（每条 1 行 `- 文件名 — 一句话用途`）
  3. 推荐阅读顺序或触发场景
  4. 下级目录指针（如有）

### 所有权

- **谁维护**：动这个目录下任何文件的 agent 顺手维护——和 dev-map 同源
- **什么时候**：新增 / 删除 / 重命名 / 合并目录下的文件时**立即**更新 OVERVIEW；目录职责变化时更新 ABSTRACT
- **守卫**：`scripts/check_repo.py` 的 `check_directory_maps()` 自动校验存在性 + 长度上限

### 反模式

- ❌ 把 README.md 当 OVERVIEW.md 用——README 给人看，OVERVIEW 给 AI 导航，长度和结构不同
- ❌ ABSTRACT 写成营销文案——只描述是什么，不写"强大 / 高效"等空泛词
- ❌ OVERVIEW 列出文件后不写一句话用途——AI 还是要逐个打开才知道，等于没建索引
