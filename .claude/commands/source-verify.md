# Source-Driven Verification（源驱动验证）

写框架特定代码前，先从官方文档验证 API 和模式。防止 AI 凭训练数据（可能过时）编写表面正确但实际错误的代码。

当前项目：`Agent Harness Framework`（cli-tool / python）

## 核心原则

**训练数据会过时。APIs 会弃用。最佳实践会演进。** 用户应该能在每一段框架特定的代码旁边看到你的来源，可以自己去核实。

## 四阶段流程

```
DETECT（识别栈+版本）→ FETCH（抓官方文档）→ IMPLEMENT（按文档实现）→ CITE（标注来源）
```

## 适用场景

- 写任何框架特定代码（组件、路由、ORM 查询、表单、认证、状态管理）
- 升级依赖版本，新旧 API 可能差异大
- 跨语言/框架迁移（如 Vue 2 → Vue 3、Django → FastAPI）
- 生成脚手架、starter、模板代码——会被复制多处
- 用户明确要求"遵循当前最佳实践"或"文档验证过的实现"
- 审查/改进已有代码的框架特定部分

**不适用**：
- 语言内通用逻辑（循环、条件、数据结构，版本无关）
- 仅改名/格式/移文件，不涉及 API 调用
- 用户明确要快（"先能跑，后面再优化"）

## 第 1 步：DETECT（识别栈和版本）

读依赖文件获取精确版本：

| 文件 | 覆盖 |
|------|------|
| `package.json` | Node/React/Vue/Angular/Svelte/Next |
| `composer.json` | PHP/Symfony/Laravel |
| `requirements.txt` / `pyproject.toml` | Python/Django/Flask/FastAPI |
| `go.mod` | Go |
| `Cargo.toml` | Rust |
| `Gemfile` | Ruby/Rails |
| `pom.xml` / `build.gradle` | Java/Kotlin |

明确输出识别结果：

```
识别到的技术栈：
- React 19.1.0（package.json）
- Vite 6.2.0
- Tailwind CSS 4.0.3
→ 准备抓取官方文档
```

版本缺失或有歧义时 **问用户**，不要猜。版本决定了哪些模式是正确的。

## 第 2 步：FETCH（抓官方文档）

抓**具体的页面**，不是首页、不是全文档。

### 权威层级（按优先级）

| 优先级 | 来源 | 示例 |
|--------|------|------|
| 1 | 官方文档 | react.dev、docs.djangoproject.com、symfony.com/doc |
| 2 | 官方博客/变更日志 | react.dev/blog、nextjs.org/blog |
| 3 | Web 标准参考 | MDN、web.dev、html.spec.whatwg.org |
| 4 | 浏览器/运行时兼容 | caniuse.com、node.green |

### ❌ **绝不**作为主要来源：

- Stack Overflow 答案
- 博客、教程（哪怕是热门的）
- AI 生成的文档或总结
- 你自己的训练数据（正是本技能要验证的对象）

### 精准抓取

```
❌ 差：抓 React 首页
✅ 好：抓 react.dev/reference/react/useActionState

❌ 差：搜索 "django authentication best practices"
✅ 好：抓 docs.djangoproject.com/en/6.0/topics/auth/
```

抓完后，提取关键模式，注意弃用警告或迁移指引。

## 第 3 步：IMPLEMENT（按文档实现）

- 用文档里的 API 签名，不用记忆里的
- 文档有"新做法"就用新做法
- 文档标了弃用，就别用弃用版本
- 文档没覆盖的 → 标记为"未验证"

### 冲突处理

**docs 和现有代码冲突**：

```
发现冲突：
现有代码用 useState 管理表单 loading 状态，
但 React 19 docs 推荐 useActionState。
（来源：react.dev/reference/react/useActionState）

选项：
A) 用现代模式（useActionState）— 与最新 docs 一致
B) 匹配现有代码（useState）— 与代码库一致
→ 你倾向哪个？
```

**永远浮现冲突**，不要静默选一个。

## 第 4 步：CITE（标注来源）

每个框架特定模式都要有引用。用户能核实每个决策。

### 代码注释

```typescript
// React 19 表单处理用 useActionState
// Source: https://react.dev/reference/react/useActionState#usage
const [state, formAction, isPending] = useActionState(submitOrder, initialState);
```

### 对话中

```
这里我用 useActionState 替代手工 useState 管理表单提交状态。
React 19 用这个 hook 替换了手工 isPending/setIsPending 模式。

Source: https://react.dev/blog/2024/12/05/react-19#actions
引用："useTransition now supports async functions [...] to handle
pending states automatically"
```

### 引用规则

- 用完整 URL，不用短链
- 尽可能用带锚点的深链（`/useActionState#usage`），锚点对文档结构调整更 resilient
- 非显然的决策附上相关段落的引用文本
- 推荐平台特性时附带浏览器/运行时支持数据
- **找不到文档的** → 明确标注：

```
未验证：没找到此模式的官方文档。基于训练数据，可能过时。
投入生产前请核实。
```

诚实承认不确定 > 假装知道。

## 反合理化

| 你想说的 | 为什么不行 |
|---------|-----------|
| "这个 API 我很熟" | 自信不是证据。训练数据里的过时模式看起来正确但撞上当前版本就崩。验证它 |
| "抓文档浪费 tokens" | 瞎猜 API 浪费更多。用户调试 1 小时，发现函数签名变了。一次抓取省掉几小时返工 |
| "文档不会有我要的" | 如果文档没覆盖，那本身就是重要信号——这个模式可能不是官方推荐 |
| "我加句'可能过时'就行" | 免责声明没用。要么验证引用，要么明确标注未验证。含糊是最差选项 |
| "简单任务没必要检查" | 简单任务用了错模式会成为模板。用户复制你的过时 form handler 到 10 个组件里，才发现现代写法存在 |
| "SO 上的答案也算文档" | SO 答案是社区经验，可能早于当前版本。只作为补充，永不替代官方文档 |

## 红色信号

- 写框架代码前没看该版本文档
- 用"I believe"、"I think"谈 API，而不是给来源
- 实现某模式却不知道它适用于哪个版本
- 引用 SO 或博客当主源
- 用弃用 API（因为它们出现在训练数据里）
- 不读 `package.json` 等依赖文件就开写
- 交付框架特定代码却没有来源引用
- 抓整个文档站，而不是具体相关页面

## 与其它技能协同

- **/tdd** 写实现前：先用本技能验证 API
- **/execute-plan** Phase 实施：每个涉及外部 API 的步骤前先 fetch 文档
- **/multi-review** 评审时：发现框架代码无引用 → P1 返工
- **/spec** 规格阶段：已有 API 变更记录要写进规格风险段
- **/adr** 技术选型：若选项涉及具体版本，引用版本的官方文档

## 验证（自检 checklist）

在交付前：

- [ ] 框架和库版本从依赖文件识别
- [ ] 为框架特定模式抓取了官方文档
- [ ] 所有来源都是官方文档，非博客或训练数据
- [ ] 代码按当前版本文档的模式编写
- [ ] 非显然决策附上完整 URL 引用
- [ ] 不使用弃用 API（对照迁移指南）
- [ ] 文档与现有代码的冲突已浮现给用户
- [ ] 未能验证的部分明确标为"未验证"
