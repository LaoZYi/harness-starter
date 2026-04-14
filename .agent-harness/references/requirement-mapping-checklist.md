# 需求 ↔ 测试 ↔ Plan Step 三元映射检查清单

L2 参考资料。灵感自 `gsd-build/get-shit-done` 的 Nyquist 合规理念 — 写任何代码前，每条需求必须有对应的自动化测试信号（或明确标 out-of-scope）。

当前项目：`Agent Harness Framework`（cli-tool / python）

## 核心理念

**每一条需求在整个开发生命周期中都是可追踪的**：

```
/spec 产出 R-ID → /write-plan 标注 task 实现哪些 R-ID → /verify 硬检查每个 R-ID 的 satisfied/missed 状态
```

违反这个链条的典型反模式：**Scope Reduction** — spec 里写了 R3，实施时默默跳过，验证时装作 R3 不存在。结果是需求分析和交付之间形成盲区。

## Spec 阶段（/spec）

- [ ] 每条验收标准分配了唯一 **R-ID**（R1, R2, ..., Rn 连续编号）
- [ ] 需求矩阵表存在且四列齐全：R-ID / 需求描述 / 验证方式 / 测试信号
- [ ] 「验证方式」具体到四类之一：自动化测试 / 性能测试 / 手动验证 / UI 截图
- [ ] 「测试信号」不能写"整体测试"——必须是具体测试名或可识别的验证动作
- [ ] 模糊需求（"更快" / "更好用"）已转化为可测量的标准

## Plan 阶段（/write-plan）

- [ ] 每个 task 的描述末尾标注了实现的 R-ID（如 `← 实现 R2, R5`）
- [ ] 计划末尾有「R-ID 覆盖表」：R-ID → task 编号的映射
- [ ] 每条 R-ID 至少映射到一个 task **或**明确标 `out-of-scope` 且给出理由
- [ ] 不存在"悬空 R-ID"（spec 里有但 plan 里既不实施也不标 out-of-scope）

## Verify 阶段（/verify）

- [ ] 生成了「R-ID 覆盖核验表」，逐条列出 R-ID
- [ ] 每条 R-ID 状态是以下三态之一：
  - ✅ **satisfied**（有测试 / 有证据）
  - ⚠️ **out-of-scope**（明确推迟 + 注明追踪 Issue）
  - ❌ **missed**（遗漏 → 必须回到实施或与用户确认转 out-of-scope）
- [ ] 没有 `❌ missed` 状态才允许宣告完成
- [ ] `⚠️ out-of-scope` 条目写清了"追踪 Issue #N" 或 "follow-up task"

## 反模式对照

| 看到这种描述 | 实际问题 |
|---|---|
| "全部验收标准通过" 但没列 R-ID | Scope Reduction — 可能漏了某条 |
| R-ID 从 R1 直接跳到 R4 | 编号不连续 — 有人偷偷删了需求 |
| 某 R-ID 的测试信号是"集成测试覆盖" | 信号不可识别 — 哪个测试？失败时怎么知道是哪条需求？ |
| plan 里某 task 没标 R-ID | 这个 task 是什么驱动的？不在 spec 里？还是 spec 漏了？ |
| `⚠️ out-of-scope` 没给 Issue 编号 | 推迟 ≠ 消失 — 没追踪等于丢失 |

## 与 /plan-check 的关系

`/plan-check` 会把上述检查项作为"需求覆盖维度"的校验标准。/plan-check 发现 `❌ missed` 或"悬空 R-ID"时会触发最多 3 轮修订循环，超过则升级到用户确认。
