# 写文档草稿（Draft-Doc）

铁律：**两段法——先 outline-pass 把骨架填满，再 draft-pass 展开。**

跳过 outline-pass 直接展开 = 全文重写 2 遍的开始。

---

## 前置条件

调用本 skill 前必须有：

1. `outline.md`（由 `/outline-doc` 产出，含 R-ID 覆盖、字数估算、引用占位）
2. `spec.md`（含 R-ID 列表，验收标准）
3. **任意写作风格指南**（如 `.agent-harness/references/writing-style.md` 或团队规范，可选但强烈推荐）

下游消费者门禁（参 `.claude/rules/anti-laziness.md` 门禁 4）：

```bash
test -f outline.md && test -s outline.md || { echo "outline.md missing or empty"; exit 1; }
grep -E "TODO|TBD|待补充" outline.md && { echo "outline 含未填占位符，先回 /outline-doc"; exit 1; }
```

---

## 两段法

### Outline-pass（先填骨架，每章 3-5 行）

对 outline.md 中每个二级标题，写 3-5 行：

1. **这章想说什么**（一句话主张）
2. **关键论点 1-3 条**（bullet）
3. **依据来源占位**（沿用 outline.md 中的 `[ref:X]` `[data:Y]`）

**不要**：

- 写完整段落
- 加修辞 / 引言 / 总结
- 跨章节引用其他章节内容

示例：

```markdown
## 2.2 关键能力

主张：本方案在三个关键维度上同时满足硬指标，竞品至少缺一项。

- 能力 A：单节点吞吐 ≥ 5000 QPS（[data:perf-benchmark-2026q1]）
- 能力 B：99.9% 可用性 SLA（[ref:client-sla-template]）
- 能力 C：支持 5 种主流协议（[ref:protocol-comparison]）
```

每章产出后立即 grep 自检：

```bash
grep -c "^主张：" current-chapter.md   # 必须 = 1
grep -c "^- " current-chapter.md       # 必须 ≥ 1
```

### Draft-pass（展开成段落）

按 outline-pass 的骨架，**一次只展开一章**。

每章产出后立即跑 4 项自检：

| 检查项 | 命令 | 通过 |
|---|---|---|
| R-ID 在本章出现 | `grep -c "R<n>" current-chapter.md` | ≥ 1 |
| 占位符未消失 | `grep "\[ref:\|\[data:" current-chapter.md` | 与 outline 一致 |
| 无 TODO / TBD | `grep -E "TODO\|TBD\|待补充"` | 无 |
| 关键术语首次出现有定义 | 手工 + grep 已知术语表 | 有 |

**不要**：

- 全文一次性写完——后章会脱离前章铺垫
- 多章并行展开——上下文连贯会丢
- 脱离 outline 自由发挥——遇到想加新章节先回 `/outline-doc`，不要原地扩

---

## 文风约束

- 用陈述句，不用反问 / 设问
- 段落 5-8 行为宜，超 12 行强制断段
- 长难句拆短：一句 ≤ 40 字，超长用顿号或分号断
- 术语首次出现给定义；后续直接用
- 数字 / 日期 / 百分比统一格式（参考项目 CLAUDE.md 全局规范）
- **不**用空泛形容（领先 / 强大 / 颠覆 / 重磅）
- **不**用第二人称（你 / 您）
- **不**写问候开场（Hello / Hi / 各位）

---

## 完成标准

- [ ] outline.md 中所有二级标题都有对应的 outline-pass + draft-pass 内容
- [ ] 每章字数 = outline 估算 ±20%（超出范围回头审章节定位）
- [ ] 全文无 TODO / TBD / 待补充
- [ ] 全文每条 R-ID 至少出现 1 次（grep 验证）
- [ ] outline 中的引用占位**全部保留**（finalize 阶段才解析为真实出处）

---

## 反偷懒

| 借口 | 驳斥 |
|---|---|
| 「跳过 outline-pass 直接展开」 | 缺骨架的草稿会反复改写；展开时发现章节关系不对再回头改，比按骨架重写贵 3 倍 |
| 「全文一次写完」 | 第 5 章的措辞会脱离第 1 章的铺垫——读者读起来跳跃，评审会扣"全文一致性"分 |
| 「凭印象引用，回头核实」 | `[ref:X]` 占位必须在 outline / spec 里登记过；没登记的不能临场加，否则 finalize 阶段卡死 |
| 「这段写得好，先扩展开」 | 你觉得"好"的段落往往是写得最快的——快说明你在熟练区，但熟练区不一定是论证最强区 |
| 「outline 里这章字数估算不对，我多写点」 | 字数偏移 > 20% → 回头审章节定位是不是偏了，不是直接超字数顶上 |

---

## 一句话总结

**草稿不是文档，是骨架的展开。骨架在 outline，展开就要尊重骨架，要变先变骨架。**
