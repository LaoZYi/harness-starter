---
description: 反过度工程化——防 AI 写 200 行能搞定 50 行 / 顺手改邻居代码,与 anti-laziness 反向互补
---

# Simplicity 规则(反过度工程化)

> **来源**:吸收自 [forrestchang/andrej-karpathy-skills](https://github.com/forrestchang/andrej-karpathy-skills)(87.8k stars),基于 Andrej Karpathy 关于 LLM 编码陷阱的观察(2026)。
>
> Karpathy 原话:「They really like to overcomplicate code and APIs, bloat abstractions...implement a bloated construction over 1000 lines when 100 would do」。

## 与其他规则的边界

| 规则 | 防什么 |
|---|---|
| **本规则 (simplicity)** | **过度膨胀**——AI 写 200 行能搞定 50 行 / 顺手"改进"邻居代码 / 加无用抽象 |
| `anti-laziness.md` | **跳步偷懒**——AI 跳验证 / 缩范围 / 假判不适用 |
| `safety.md`「改一处查所有同类」 | **bug 修复时漏修同类**(扩散场景) |

三者目标都是"刚刚好"——既不偷懒也不过度也不漏修。**simplicity 与 anti-laziness 反向互补**,不冲突。

## 准则 1:Simplicity First — 写最少能解问题的代码

**原则**:「No features beyond what was asked. Nothing speculative.」

具体准则:

- **禁止**:超出用户要求的功能(为"以后可能用到"加 flag / config / option)
- **禁止**:单次使用代码加抽象(为"将来可能复用"提取 base class / interface)
- **禁止**:加未要求的"灵活性 / 可配置性"
- **禁止**:为不可能场景加错误处理(参数已是非空类型还检查 None)
- **测试**:如果 200 行能压成 50 行,**重写**

**自检问题**:"一个资深工程师看这段代码会不会说`这写复杂了`?" 如果会 → 简化。

## 准则 2:Surgical Changes — 改最少必要

**原则**:「Touch only what you must. Clean up only your own mess.」

具体准则:

- **禁止**:"顺手改进"邻居代码 / 注释 / 格式
- **禁止**:重构没坏的代码("我看着不顺眼")
- **禁止**:替换已有 style("我习惯写 X,这里写 Y 看着不舒服")—— **匹配现有 style,即使你会用不同方式**
- **禁止**:删除你没改过的 dead code(可以**提一句**让用户决定,但别动)

**追溯测试**:每行改动都能直接追溯到用户的请求 → 通过;否则 = 越界。

## 准则 3:孤儿清理 — 仅清自己造成的

**原则**:你的改动让某个 import / function / variable 变孤儿了 → 你清。

但**不**清以下:

- 改动前就存在的 dead code
- 改动前就存在但你没改的过时注释
- 跟你改动无关的 lint warning

如果发现这类 → **提一句**让用户决定,不主动改。

## 准则 4:可验证目标驱动

**原则**:模糊任务转换为可验证目标。「Define success criteria. Loop until verified.」

转换模板见 `.agent-harness/references/requirement-mapping-checklist.md` 末尾「模糊需求 → 可验证目标转换模板」节。

## 反合理化(扩展 anti-laziness 门禁 3)

| 借口 | 驳斥 |
|---|---|
| 「我看着这段代码不顺眼,顺手改一下」 | 越界。Surgical Changes 第 1 条:不动你没在改的代码。**提**一句让用户决定 |
| 「这个抽象将来可能用到,先放着」 | YAGNI。Simplicity First 第 2 条:单次使用不抽象。等真的用到再提 |
| 「200 行多写几行也无所谓,反正能 work」 | 错。代码的成本不是写,是**读**——后续每个读者每次都付。50 行能解决就 50 行 |
| 「邻居那段代码风格跟我不一样,统一一下」 | Surgical Changes 第 3 条:匹配现有 style 即使你不喜欢。统一不是你这次任务 |
| 「删掉这段 dead code 让代码更干净」 | 不是你引入的不动。**提**一句让用户决定。不知道为什么留着的代码不要删 |
| 「为以后扩展加个 config 选项更灵活」 | Simplicity First 第 3 条:不要未要求的灵活性。需要时再加 |

## 适用边界(框架 vs 业务)

**框架级**抽象(分层记忆 / Trust Calibration / Context Budget 等核心设计)是经过设计的,**不在本规则约束范围内**。本规则约束的是:

- ✅ 业务逻辑代码
- ✅ 工具脚本
- ✅ 一次性数据处理
- ✅ 测试代码(测试不要无意义抽象)

**例外:修反模式**——当你识别出代码使用了项目已经记录的反模式(见 `architecture-patterns.md` 反模式 1 等),修复反模式不算"违反 Surgical Changes 的匹配现有 style"。这种情况:

- 修反模式时,在 commit 消息中**显式说明**对照的反模式 / lesson 标题
- 修反模式应单独 commit,不混入本次主任务

## 与 /lfg 的接入

- 阶段 0.1 第 3 步「明确验收标准」引用本规则的「转换模板」
- 阶段 4.2「需要做计划外的改动」表格行扩展:`unplanned: 邻居清理` 默认禁止,需走 unplanned commit 流程
- 阶段 4.3 自检表加 `simplicity` 列:回顾是否有越界改动 / 过度抽象 / 200 行能压成 50 行

## 违反检测

`/multi-review` 评审员视角:
- diff 中出现"看似无关"的修改 → 询问"为什么改这里?能追溯到用户请求吗?"
- 单次使用的 helper class / interface → 询问"这个抽象将来谁会用?"
- 行数显著超过类似功能 → 询问"能压缩吗?"

`/verify` 阶段 4.3 自检:
- 把 diff 过一遍,问"每行改动追溯到用户请求了吗?"
