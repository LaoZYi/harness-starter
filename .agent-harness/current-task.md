# Current Task

## 状态: 待验证

## 任务目标

操作 3:把 4 条 SSOT/枚举类改动同主题 lesson 合并为带 `when:` 条件分支的单条。

合并源:
1. 2026-04-08 [流程] 新增技能时文档散布计数需全量扫描
2. 2026-04-13 [架构设计] 抽 SSOT 时必须清单化所有下游消费方
3. 2026-04-16 [流程] plan 阶段判 out-of-scope 前必须 grep 硬编码数字
4. 2026-04-20 [测试] 改模板文本前必须 grep 现有测试是否锁定具体字符串

## 假设清单

- 假设:**保留 4 条原条目并加 deprecated 标注**,而非物理删除 | 依据:T3 不删任一信息原则 + delete 决策也是 deprecated 不物理删
- 假设:新合并条目放在 lessons.md 顶部新条目区,index 表新增 anchor | 依据:4 个 when: 分支需要顶部位置便于检索
- 假设:索引表旧 anchor 加 deprecated 标记不删 | 依据:旧 anchor 仍指向有效但已废弃条目,删除会让历史链接失效

## 完成标准

- [x] step 1: 合并稿已展示给用户(4 个 when: 分支 + 元规则 + 反合理化表)
- [x] step 2: 合并稿已写入 lessons.md 顶部(紧邻 T6 晋升 5 步清单上方)
- [x] step 3: 4 条原 lesson 末尾全部加 ⚠️ deprecated → 指向合并条目对应 when: 分支
- [x] step 4: 索引表新 anchor 加在流程行首位;旧 4 个 anchor 文本加 ⚠️deprecated 前缀
- [x] step 5: memory rebuild ok;audit 已写;638/638 测试全过
- [x] step 6: 已进入待验证状态

## LFG 进度

- 复杂度:小 | 通道:轻量 | 基线 commit:135d570
- 历史参考:knowledge-conflict-resolution.md T3 处理路径 + dedup decision merge 语义
