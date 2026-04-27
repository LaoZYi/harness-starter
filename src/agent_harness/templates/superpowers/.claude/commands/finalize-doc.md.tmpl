# 文档定稿（Finalize-Doc）

铁律：**8 项必检，差一项不算完成。**

定稿是文档对外的契约——一旦发出去，改一条术语就要传遍所有读者。把成本留在定稿前。

---

## 何时使用

- `/review-doc` 4 人格评审 P0/P1 全部 close 后
- 准备发给评委 / 客户 / 监管 / 公开发布 之前

不适用：
- 草稿评审还有 P0 未 close（先回 `/review-doc` 改）
- 文档还在 outline 阶段（用 `/finalize-doc` = 浪费）

---

## 前置条件

1. 草稿存在且非空
2. `outline.md` 存在（用于字数估算对比）
3. `spec.md` 存在（含 R-ID 列表）
4. 评审报告存在（`docs/superpowers/reviews/doc-<topic>-review-<ts>.md`）
5. 评审 P0/P1 状态在报告中可定位

---

## 8 项必检（数量门禁，门禁 1）

每项必须给三态之一：✅ passed / ⚠️ skipped（附理由 + 用户确认）/ ❌ failed

### 检查 1：无占位符残留

```bash
grep -nE "TODO|TBD|待补充|XXX|FIXME|占位" "$DOC"
```

通过：无输出。
失败：列出所有命中行号 → 修。

### 检查 2：每条 R-ID 在文档中可定位

```bash
for r in R1 R2 R3 R4 R5; do
  count=$(grep -c "$r" "$DOC")
  echo "$r: $count occurrences"
  [ "$count" -ge 1 ] || echo "  ❌ MISSING"
done
```

通过：每条 R-ID 至少出现 1 次。

### 检查 3：引用占位全部解析为真实出处

```bash
# 应无未解析的占位
grep -nE "\[ref:|\[data:" "$DOC"
```

通过：无输出（所有 `[ref:X]` 都被替换为脚注 / 文末参考文献 / 内嵌链接 / 内嵌作者注）。
失败：列出未解析的占位 → 解析或显式声明 known-issue。

### 检查 4：术语统一（已知大小写易错词）

```bash
# 项目 CLAUDE.md 全局规范的术语清单
for term in "HTTP" "OAuth 2.0" "Kubernetes" "JavaScript" "TypeScript" "Python" \
            "GitHub" "GitLab" "Node.js" "PostgreSQL" "MongoDB" "Redis" "Nginx" "JWT"; do
  variants=$(grep -ioE "$(echo $term | tr '[:upper:]' '[:lower:]')|$(echo $term | sed 's/.*/\u&/')" "$DOC" \
             | sort -u | tr '\n' ' ')
  echo "$term -> $variants"
done
```

通过：每个已知术语全文用同一种大小写。
失败：grep 出变体 → 全文统一。

### 检查 5：章节字数符合 outline 估算（±20%）

```bash
# 解析 outline.md 中的章节字数估算，比对实际
.venv/bin/python -c "
import re, sys
outline = open('outline.md').read()
doc = open('$DOC').read()
# 简易解析（项目可按需细化）
estimates = re.findall(r'^#+\s+(.+?)\s+~(\d+)\s*字', outline, re.MULTILINE)
for chapter, est in estimates:
    est = int(est)
    # ... 按章节定位实际字数
    print(f'{chapter}: estimate {est}')
"
```

通过：每章实际 = 估算 ±20%。
失败：偏离过大 → 回头审章节定位是不是偏了，不是直接超字数顶上。

### 检查 6：评审 P0/P1 反馈全部 close

```bash
# 在评审报告里找未 close 的项
grep -nE "P0|P1" "$REVIEW_REPORT" | grep -vE "✅|已改|接受"
```

通过：所有 P0/P1 都标 ✅ 或"已改"或"质疑保留（附理由）"。
失败：列出未 close 项 → close 后才能继续。

### 检查 7：Markdown 格式正确

- 标题层级不跳级（`#` → `##` → `###`，不允许 `#` → `###`）
- 列表前后空行
- 代码块用 ``` 闭合
- 表格列对齐（可选 `markdownlint` 等工具，可选）

```bash
# 简易检查：标题跳级
.venv/bin/python -c "
import re
prev_level = 0
for line in open('$DOC'):
    m = re.match(r'^(#+)\s', line)
    if m:
        level = len(m.group(1))
        if prev_level and level > prev_level + 1:
            print(f'标题跳级: {line.strip()}')
        prev_level = level
"
```

### 检查 8：文档元信息完整

文档头部必须有 frontmatter（项目类型 `document` 默认约定）：

```yaml
---
title: <文档标题>
version: 1.0
date: 2026-04-27
status: final
authors: [<作者>]
---
```

```bash
head -10 "$DOC" | grep -E "^title:|^version:|^date:|^status:" | wc -l
# 必须 ≥ 4
```

---

## 不做的事（明示 R4）

`/finalize-doc` **不**做以下事情：

- 不调 `/git-commit` —— 写文档的人可能完全不用 git；如果你确实想 commit，**手动**调 `/git-commit`，本 skill 不自动触发
- 不调 `/finish-branch` —— 同上
- 不创建 PR —— 文档不一定走代码评审管道
- 不切分支 —— 文档项目可能就在主分支线性提交
- 不调 `/verify` —— `/verify` 跑测试 / lint / 跨平台验证，不适用于文档；本 skill 内嵌的 8 项必检就是文档版"verify"
- 不调 `/multi-review` —— 用 `/review-doc` 替代

---

## 产出

1. **定稿文件**：写入用户指定路径（如 `bid-2026-q2/final.md`）
2. **finalize-report.md**：8 项检查记录
   ```markdown
   # Finalize Report

   日期: 2026-04-27
   文档: bid-2026-q2/final.md

   | 检查 | 状态 | 备注 |
   |---|---|---|
   | 1. 占位符 | ✅ | 无 TODO/TBD |
   | 2. R-ID 覆盖 | ✅ | R1-R5 全部 ≥ 1 |
   | 3. 引用解析 | ✅ | 12 个占位全解析为参考文献 |
   | 4. 术语统一 | ⚠️ skipped | "HTTP" 在引用文献原文中保留小写（用户确认 OK） |
   | 5. 字数符合 | ✅ | 偏差 ±15% |
   | 6. 评审 close | ✅ | 8 个 P0 + 12 个 P1 全 close |
   | 7. Markdown 格式 | ✅ | 无标题跳级 |
   | 8. 元信息 | ✅ | frontmatter 完整 |

   known-issues（P2 推迟）:
   - L42 「近期」措辞偏模糊（推迟到 v1.1 修）
   ```
3. **known-issues.md**（可选）：列入 P2 推迟项 + 理由 + 修复时间窗

---

## 反偷懒（扩展门禁 3）

| 借口 | 驳斥 |
|---|---|
| 「8 项太多，跳几个」 | 数量门禁不允许批量 dismiss——每项给状态：✅ / ⚠️ skipped（附理由 + 用户确认）/ ❌ |
| 「这条本来就这样」 | 必须给具体行号或文件位置作证据；空口"本来就这样"违反门禁 5 不确定性输出 |
| 「评审说 P2 我先不管」 | P0/P1 必 close；P2 列入 known-issues 段，不是直接忽略 |
| 「8 项都过了再走 git-commit」 | 错——本 skill 完成等于"文档定稿"。git 是另一回事，由用户决定要不要做 |
| 「这文档不重要，没必要这么麻烦」 | 文档发布出去后改一条术语就要传遍所有读者。定稿门禁是对外契约，不是内部仪式 |
| 「8 项一次过太难，分两次过」 | 8 项是同一个时间点的快照——你今天改了占位符明天又新加 5 个，定稿状态会回退。一次性过完才能保证一致性 |
| 「我手工 review 一遍就行，不用跑 grep」 | 手工 review 漏行率 > 30%。机械检查的成本是几条命令，比手工漏的代价低几个量级 |

---

## 完成标准

- [ ] 8 项必检全部 ✅ 或带理由 ⚠️ skipped
- [ ] 定稿文件落盘（路径在产出报告中明确）
- [ ] finalize-report.md 落盘
- [ ] known-issues.md（如有 P2 推迟）落盘
- [ ] **不**触发任何 git 操作（除非用户**显式**调 `/git-commit`）

---

## 一句话总结

**定稿不是发文档前最后一步，是文档对外的契约。8 项必检是契约的内容，差一项契约就漏了。**
