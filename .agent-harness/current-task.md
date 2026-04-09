# Current Task

## 状态：待验证

任务：升级三方合并策略 — 让 harness upgrade 保留用户内容

### 验收标准
1. [x] skip 文件升级时不被覆盖
2. [x] three_way 文件用户编辑在升级后保留
3. [x] json_merge 文件用户自定义 key 不丢失
4. [x] 冲突时 CLI 醒目红色提示
5. [x] init 时存储基线到 .agent-harness/.base/
6. [x] 老项目（无 .base/）升级时退化为备份+覆盖
7. [x] make ci 全绿（104 tests）
