"""Copy pure-stdlib runtime modules into target project's .agent-harness/bin/.

目的：让用户 **clone 一个 init 过的项目 + 开 Claude Code** 就能跑所有 AI 工作流
命令（如 /lfg 阶段 9 的 audit append、memory rebuild），无需装 harness CLI。

设计：
- 运行时模块是**框架资产**（无用户数据）→ init 和 upgrade 时总是覆盖
- 不纳入 save_base / three-way merge（和 AGENTS.md 等用户可编辑文件区别对待）
- Entry 脚本（`.agent-harness/bin/audit` / `memory`）同为框架资产，强制覆盖
- `_runtime/` 下为纯 stdlib 的 Python 源码副本；由 `ast` 层面的契约测试守护

Issue #24。
"""
from __future__ import annotations

import shutil
from pathlib import Path

from ._shared import PKG_DIR

# 需要整体复制到 _runtime 的源码文件（均为纯 stdlib、无顶层副作用）
_RUNTIME_MODULES: tuple[str, ...] = (
    "audit.py",
    "audit_cli.py",
    "memory.py",
    "memory_search.py",  # Issue #29: BM25 fallback used by /recall + memory search
    "security.py",  # Issue #25: squad.spec 用 NAME_PATTERN
)

# squad 子包（所有文件都是纯 stdlib；PyYAML 依赖已在 Issue #25 去掉）
_SQUAD_MODULES: tuple[str, ...] = (
    "__init__.py", "capability.py", "cli.py", "coordinator.py", "mailbox.py",
    "spec.py", "state.py", "tmux.py", "watchdog.py", "worker_files.py",
)

# _shared.py 不能直接复制：原文件顶层读取 VERSION、检查 templates/ 目录，
# 这些在内嵌运行时场景下都不存在。提供只含 audit/memory 需要的函数的精简版。
_SHARED_EMBEDDED = '''\
"""Embedded runtime _shared — only utilities audit/memory need (no framework deps)."""
from pathlib import Path


def require_harness(target: Path) -> None:
    """Raise SystemExit if target hasn't been initialized with harness."""
    if not (target / ".agent-harness").is_dir() and not (target / "AGENTS.md").exists():
        raise SystemExit(
            f"错误：{target} 尚未初始化 harness。请先运行 harness init {target}"
        )
'''

_AUDIT_ENTRY = """\
#!/usr/bin/env python3
\"\"\"Project-embedded audit runtime — equivalent to `harness audit`.

此文件由 harness 生成，请勿手工修改（下次 upgrade 会覆盖）。
\"\"\"
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _runtime.audit_cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
"""

_MEMORY_ENTRY = """\
#!/usr/bin/env python3
\"\"\"Project-embedded memory runtime — equivalent to `harness memory`.

此文件由 harness 生成，请勿手工修改（下次 upgrade 会覆盖）。
\"\"\"
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _runtime.memory import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
"""

_SQUAD_ENTRY = """\
#!/usr/bin/env python3
\"\"\"Project-embedded squad runtime — equivalent to `harness squad` (Issue #25).

此文件由 harness 生成，请勿手工修改（下次 upgrade 会覆盖）。
\"\"\"
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _runtime.squad.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
"""

_INIT_PY = '"""Embedded runtime package (harness-managed, do not edit)."""\n'

_README = """\
# .agent-harness/bin/

项目内嵌运行时脚本。**无需安装 harness CLI** 即可执行——clone 仓库 + 开 Claude Code 立即可用。

- `audit` — 等价于 `harness audit`（关键文件变更审计）
- `memory` — 等价于 `harness memory`（分层记忆索引）
- `squad` — 等价于 `harness squad`（多 agent 常驻协作，Issue #25）
- `_runtime/` — 纯 stdlib 运行时源码副本，由 harness 自动管理。**请勿手工修改**
  （下次 `harness upgrade apply` 会覆盖任何改动）

## 用法

```bash
.agent-harness/bin/audit append --file lessons.md --op append --summary "新沉淀一条教训"
.agent-harness/bin/audit tail --limit 10
.agent-harness/bin/memory rebuild . --force
.agent-harness/bin/squad create spec.json
.agent-harness/bin/squad status
```

无执行权限时可用 python 直接跑：

```bash
python3 .agent-harness/bin/audit tail
```

## 与 harness CLI 的关系

- **harness CLI**（`pipx install agent-harness-starter`）：**项目维护者**的脚手架工具，
  用于 init / upgrade / doctor / export 等**元命令**
- **.agent-harness/bin/**：**项目使用者**（clone 仓库的人）的运行时，AI 工作流中所有
  需要调用的命令都通过这里，不依赖用户机器装了 harness
"""


def install_runtime(target_root: Path) -> list[Path]:
    """Copy runtime modules + write entry scripts. Returns list of written files.

    Called by:
    - `initializer.initialize_project` (after save_base)
    - `upgrade.execute_upgrade` (after save_base)
    """
    bin_dir = target_root / ".agent-harness" / "bin"
    runtime_dir = bin_dir / "_runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []

    # 1. 复制 stdlib 运行时源码副本
    for mod in _RUNTIME_MODULES:
        src = PKG_DIR / mod
        dst = runtime_dir / mod
        shutil.copyfile(src, dst)
        written.append(dst)

    # 2. 写精简版 _shared.py（原文件有框架顶层副作用，不适合内嵌）
    shared = runtime_dir / "_shared.py"
    shared.write_text(_SHARED_EMBEDDED, encoding="utf-8")
    written.append(shared)

    # 3. package marker
    init_file = runtime_dir / "__init__.py"
    init_file.write_text(_INIT_PY, encoding="utf-8")
    written.append(init_file)

    # 3a. 复制 squad 子包（Issue #25）
    squad_src = PKG_DIR / "squad"
    squad_dst = runtime_dir / "squad"
    squad_dst.mkdir(exist_ok=True)
    for mod in _SQUAD_MODULES:
        src = squad_src / mod
        if src.is_file():
            shutil.copyfile(src, squad_dst / mod)
            written.append(squad_dst / mod)

    # 3b. squad 在源码里用 `from ..security import NAME_PATTERN`；bin 场景里
    # _runtime/ 作为 package（顶层 __init__.py 存在），security 是它的 sibling
    # 模块 → 改写成绝对 `from _runtime.security import`，entry 脚本只需把 bin/
    # 加到 sys.path
    spec_py = squad_dst / "spec.py"
    if spec_py.is_file():
        txt = spec_py.read_text(encoding="utf-8")
        spec_py.write_text(
            txt.replace("from ..security import", "from _runtime.security import"),
            encoding="utf-8",
        )

    # 4. Entry 脚本（shebang + 可执行）
    for name, content in (("audit", _AUDIT_ENTRY), ("memory", _MEMORY_ENTRY),
                          ("squad", _SQUAD_ENTRY)):
        entry = bin_dir / name
        entry.write_text(content, encoding="utf-8")
        entry.chmod(0o755)
        written.append(entry)

    # 5. README
    readme = bin_dir / "README.md"
    readme.write_text(_README, encoding="utf-8")
    written.append(readme)

    return written
