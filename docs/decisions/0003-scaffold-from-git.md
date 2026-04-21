# ADR 0003：`harness init --scaffold` 支持远端 git 仓库

- **状态**：Accepted
- **日期**：2026-04-21
- **接受日期**：2026-04-21
- **决策者**：LFG scaffold-from-git 任务
- **相关文档**：`docs/superpowers/specs/2026-04-21-scaffold-from-git-spec.md`

## 背景和问题

`harness init --scaffold <local_path>` 当前只接本地目录。团队若把模板托管到 GitHub / GitLab / 内部 git，用户必须手动 clone 一次再传本地路径，三步走。常用场景诉求：一步从 git 拉模板 + 初始化。

**问题**：如何在不引入第三方依赖、不破坏向后兼容的前提下，扩展 `--scaffold` 接受 git URL？

## 考虑过的方案

| 方案 | flag 数 | 向后兼容 | 依赖 | 评估 |
|---|---|---|---|---|
| **A. 单 flag 自动检测** | 1（复用 `--scaffold`）| ✅ | stdlib `subprocess + git` | **候选** |
| B. 独立 `--scaffold-git <url>` | 2 | ✅ | 同上 | 否：flag surface 翻倍；用户需记两个；互斥校验成本 |
| C. 引入 GitPython | 1 | ✅ | GitPython（重） | 否：违反零依赖原则；子进程调 git 够用 |
| D. 自己实现 HTTPS + auth | 1 | ✅ | urllib（但鉴权复杂）| 否：重造轮子；token 管理是安全坑 |
| E. 全量 clone（不 shallow）| 1 | ✅ | stdlib | 否：默认大仓慢；模板用不到历史 |

## 决策

**采纳方案 A + shallow clone + 委托鉴权给 git 配置**。

### 关键设计点

1. **自动检测规则**：`http(s)://` / `git@` / `ssh://` / `git://` 前缀，或以 `.git` 结尾 → git URL；否则本地路径
2. **shallow clone**（`git clone --depth 1`）：模板用不到历史，省流量和时间
3. **鉴权委托**：用户的 SSH key / credential helper / `~/.netrc` / GIT_ASKPASS 自动生效；本命令**不**处理 token 传递——token 放命令行是常见泄密路径
4. **`--scaffold-ref`** 支持 branch / tag（`git clone --branch` 的能力上限）；**不**承诺任意 commit SHA（需要 fetch + checkout 两步，复杂度升级）
5. **`--scaffold-subdir`** 支持 monorepo 模板仓；双保险校验：拒绝 `..` 和绝对路径 + `os.path.commonpath` 检测不逃逸 clone 目录
6. **tmpdir 复用 `copy_scaffold`**：clone 到 `tempfile.TemporaryDirectory()`，再用现有 `copy_scaffold(tmp, target)` 复制——一处实现两种入口（local / git）共用

## 后果

### 正面

- 用户一步从远端 git 到初始化完成
- `.git` 目录不残留在 target（SCAFFOLD_SKIP + tmpdir 双层清理）
- 保持零第三方依赖（违反项目核心约束的方案已排除）

### 负面

- **新增网络依赖**（用户机器需装 git + 能访问目标仓）
- **`--scaffold-ref` 只支持 branch/tag**，不支持任意 commit SHA——文档显式说明以免用户失望
- **鉴权失败的错误消息**依赖 git 本身输出（不做额外翻译）

### 中性

- 增加 `_scaffold_git.py`（~60 行）+ 2 个 CLI flag
- 现有本地路径行为不变

## 参考

- `docs/superpowers/specs/2026-04-21-scaffold-from-git-spec.md`（规格）
- `docs/superpowers/specs/2026-04-21-scaffold-from-git-plan.md`（实施计划 + /cso 分析）
- `lessons.md 2026-04-20 测试脚手架起 git subprocess 必须 env 隔离用户全局配置`（测试 git 子进程的 env 要隔离）
