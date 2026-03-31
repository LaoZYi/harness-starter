# 产品规则

`triage_bot` 是一个工单分流器。输入是一张待处理工单，输出是一个明确的队列、优先级和解释。

## 输入字段

- `title`：工单标题。
- `description`：工单正文。
- `customer_tier`：`free`、`pro`、`enterprise`。
- `channel`：`email`、`chat`、`web`。

## 输出字段

- `queue`：`billing`、`support`、`security`、`product`。
- `priority`：`low`、`medium`、`high`、`critical`。
- `reasons`：命中的规则说明，便于人工复核。

## 当前行为

1. 标题和正文会被统一转成小写后匹配关键词。
2. 出现 `breach`、`data leak`、`security`、`vulnerability` 之一时，直接进入 `security` 队列，优先级至少是 `high`。
3. 出现 `invoice`、`refund`、`payment`、`charge` 之一时，进入 `billing` 队列。
4. 出现 `feature`、`roadmap`、`integration` 之一时，进入 `product` 队列。
5. 出现 `outage`、`service down`、`unavailable`、`latency` 之一时，进入 `support` 队列，但默认优先级提升到 `high`。
6. 其他情况进入 `support` 队列。
7. `enterprise` 客户的优先级会提升一级，但不会超过 `critical`。
8. 通过 `chat` 渠道提交且正文长度超过 280 个字符时，优先级会提升一级，因为这通常意味着问题复杂且沟通成本高。

## 变更原则

- 只要改了匹配规则、优先级算法或输出结构，就要同步更新本文件。
- 新规则必须有至少一个测试样例。
