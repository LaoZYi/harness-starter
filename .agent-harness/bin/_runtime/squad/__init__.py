"""Squad — tmux + worktree 多 agent 常驻协作（MVP 阶段 1）。

子模块：
- spec: YAML 规格解析、依赖环检测、名称白名单校验
- capability: scout/builder/reviewer 的 settings.local.json 渲染
- tmux: tmux 命令构造、可用性探测
- state: manifest/status 文件读写（fcntl 文件锁）
- cli: harness squad create|status|attach|stop 子命令入口
"""
