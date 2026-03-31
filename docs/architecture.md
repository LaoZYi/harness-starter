# 架构约束

## 模块职责

- `src/agent_harness/discovery.py`：扫描目标项目并给出第一版画像。
- `src/agent_harness/assessment.py`：根据画像给出接入评分、缺口和建议。
- `src/agent_harness/initializer.py`：整合探测结果、预设和用户输入，生成文件。
- `src/agent_harness/templating.py`：模板渲染和落盘。
- `templates/common/`：真正会写入目标项目的模板。
- `presets/`：按项目类型提供默认文案和关注点。
- `scripts/*.py`：命令行封装层。
- `tests/`：框架级回归测试。
- `scripts/check_repo.py`：框架仓库的守卫脚本。

## 约束

1. 模板内容必须尽量通用，不能再引入样例业务。
2. 脚本逻辑和模板文本分离，不要把长文案塞进 Python 代码里。
3. 长期规则必须写回仓库文件，不要只留在某个工具的 memory 里。
4. Claude 适配层只做薄封装，不能演化成第二套真规则。
5. 自检脚本要优先检查“模板是否存在”“脚本是否连通”“文档是否指向真实入口”。

## 推荐扩展方式

- 想增加新项目类型：先加 `presets/*.json`，再补模板、评估逻辑和测试。
- 想增加新生成文件：先加模板，再补初始化测试和仓库自检。
- 想增加新命令：先改 `Makefile`，再补脚本和 `docs/runbook.md`。
