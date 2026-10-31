# 2026-10-31 启动验收记录

## 现象

停止宇宙后通过真实终端启动 `universes/my-terminal-bench-science/start`。四个后台服务均成功启动：role broker、evaluation queue、review dispatcher、author selftest worker。主 `gewu-multiverse` 控制器随后进入 Linux `D+` 状态，约 90 秒内没有创建新的 agent run，也没有产生新的轨迹。

按 Ctrl-C 结束终端后，后台服务随启动器一起退出，没有留下角色进程。

## 证据

- 工作区 `/mnt/data` 位于 `fuse.aliyun-alinas-efc`，挂载源为上海 CPFS。
- 本地 NVMe `/tmp` 为 ext4，约 732 GB 可用。
- 控制器进程状态为 `D+`，表示在不可中断的内核 I/O 等待中；这不是模型请求或 ACS 返回错误。
- 角色目录中只有历史 `run-*`，启动观察窗口内没有新的 run。

## 判断

当前启动阻塞点是控制器访问 CPFS 上的热状态/轨迹目录。不能把这次启动视为生产闭环通过，也不能据此判断 ACR、ACS 或 dawnfm 有故障。

## 后续修复方向

1. 将 controller 的高频状态、锁、会话临时文件和轨迹 append 缓冲迁移到本地 NVMe；CPFS 只保存最终归档和周期性快照。
2. 给启动器增加启动探针：若控制器连续进入不可中断 I/O 或在规定窗口内没有心跳，自动停止服务并留下诊断，而不是继续等待。
3. 迁移后重新执行 broker、队列、reset、selftest 和实际 ACS 评测验收，再启动宇宙。
