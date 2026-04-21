# ADR 0004：`harness init --scaffold-cmd` 支持脚手架命令

- **状态**：Accepted
- **日期**：2026-04-21
- **接受日期**：2026-04-21
- **决策者**：LFG scaffold-from-cmd 任务
- **相关文档**：`docs/superpowers/specs/2026-04-21-scaffold-from-cmd-spec.md`

## 背景和问题

`harness init --scaffold` 现支持两种来源：本地目录路径、远端 git URL（ADR 0003）。实际使用中遇到第三种情况——主流前端/后端脚手架（vite / next / remix / nuxt / django / rails / cargo / poetry 等）通常通过一条命令初始化项目，如：

```bash
npm create vite@latest my-app -- --template react
npx create-next-app@latest my-app
django-admin startproject mysite
cargo new my-app
```

现状下用户必须先手工在别处跑脚手架生成目录，再 `harness init <生成目录>`，两步走。目标：一步到位。

**问题**：在 `harness init` 中如何引入「脚手架命令」这一来源类型，不破坏现有 `--scaffold` 行为，不引入第三方依赖？

## 考虑过的方案

| 方案 | 互斥关系 | UX | 实现复杂度 | 评估 |
|---|---|---|---|---|
| **A. 独立 `--scaffold-cmd "<cmd>"`** | argparse 互斥组强制与 `--scaffold` 互斥 | ✅ 清晰 | ✅ 低 | **候选** |
| B. 复用 `--scaffold`，按启发式（空格、开头关键字如 `npm`/`npx`）判别命令 vs 路径 | 单 flag | ⚠️ 模糊，容易误判 | ⚠️ 中 | 否：`npm-monorepo` 目录名就可能误判；用户心智负担 |
| C. 预设清单 `--scaffold-preset vite-react` + 内置脚手架命令映射 | 独立 flag | ⚠️ 受限 | ❌ 高 | 否：预设集维护成本高、易过时（vite 版本升级就失效）；用户灵活度低 |
| D. 维持现状，让用户先手工跑脚手架再 init | N/A | ❌ 两步走 | 0 | 否：与任务目标冲突 |

## 决策

**采纳方案 A：独立 `--scaffold-cmd` flag + argparse 互斥组**。

### 关键设计点

1. **互斥组**：`--scaffold` 和 `--scaffold-cmd` 由 argparse `add_mutually_exclusive_group()` 强制二选一，同时给两个 flag 时 argparse 直接报错
2. **`shlex.split` + argv list**：命令字符串拆成 argv 列表传给 `subprocess.run(..., shell=False)`
   - 防 shell 元字符（`;` `&` `|` `$()`）被解释为运算符
   - 命令的参数保留 shell 引号语义（`"my app"` 被视为一个参数）
3. **stdio 继承父进程**：不捕获 stdout/stderr/stdin
   - 多数主流脚手架默认交互式（询问 template、features）
   - 捕获会导致死锁或空白卡死
4. **cwd = target**：命令在 target 目录执行
   - 不做参数改写（不自动插 `.` 作脚手架 target）
   - 用户自己负责把命令写成「在当前目录初始化」的形式，例：
     - `npm create vite@latest . -- --template react`
     - `cargo init`（而非 `cargo new`）
     - `django-admin startproject . mysite`
   - 文档里列出常见脚手架的「在当前目录初始化」写法
5. **`shutil.which` 预检**：命令程序不存在时直接 `SystemExit` 给中文错误，比直接跑 `subprocess.run` 让 OSError 冒出去更友好

## 后果

### 正面

- UX 清晰：用户一眼看出「这是运行一条命令」vs「这是指定一个路径」
- 零第三方依赖：`shlex` / `shutil` / `subprocess` 全是 stdlib
- 交互式脚手架可用（vite / next 等在终端正常问答）
- 安全可预测：argv list 让 shell 元字符不会被意外解释

### 负面

- 用户需懂脚手架自身「在当前目录初始化」的写法（文档举例缓解）
- 子进程的 stdio 继承导致 harness init 的输出会被脚手架输出穿插（不是 bug，但视觉上不如单纯 harness 输出整齐）
- 脚手架若生成到子目录（如 `cargo new my-app` 会生成 `./my-app/` 而非 `./`）后续 `harness init` 会把 agent 文件放到 target 根而非子目录——属于用户命令写错，文档和报错一起引导

### 中性

- 新增 `_scaffold_cmd.py` ~80 行 + 1 个 CLI flag
- `ask_scaffold` 交互菜单从 3 项扩到 4 项
- 现有 `--scaffold` / `--scaffold-ref` / `--scaffold-subdir` 行为完全不变

## 安全考量

- **命令注入**：用户自愿运行的命令，不是外部输入；argv list 避免元字符被解释
- **任意代码执行**：等同用户手工在 shell 里跑命令，是用户主动行为，不是 harness 创造的攻击面
- **资源耗尽**：脚手架可能下载 GB 级依赖（npm install），不做限制——用户知情
- **Ctrl-C 传递**：POSIX 默认行为，子进程会收到 SIGINT；harness 读 returncode 报错退出

## 参考

- `docs/superpowers/specs/2026-04-21-scaffold-from-cmd-spec.md`（规格）
- `docs/superpowers/specs/2026-04-21-scaffold-from-cmd-plan.md`（实施计划）
- ADR 0003（远端 git 支持，姊妹特性）
- `lessons.md 2026-04-20 测试脚手架起 git subprocess 必须 env 隔离用户全局配置`
