# 人工干预与角色重置

提供运维CLI；不自动判定死胡同后直接kill。耗时、错误计数只是复查线索，负对照、长计算、ACS等待须单独判断。

只读复查：PYTHONPATH=deploy/science python3 deploy/science/role_progress_review.py author-02

预览：PYTHONPATH=deploy/science python3 deploy/science/role_reset.py author-02 --reason '人工确认需要转向' --next-action '保留原型，检查交接记录后转向指定思路'

添加 --apply 才生效。生产操作必须先暂停控制器及自动重启监督器，确认无并发调度；CLI锁只防并发reset，尚未与控制器原子协调。运维恢复控制器后须核对新run、指令、skill及首次有效动作。在线回路尚未验收。

核对PID、启动时刻和专属UID；停止指定模型与该UID本地命令；保留文件、Git分支和轨迹；备份instruction并写入原因和下一步。同题五小时预算不清零。独立ACS作业不会自动停止，须另行按精确作业身份处理。

2026-10-30：reset及诊断10项测试通过，包含临时sleep进程终止。没有对已停止的author-02做无必要kill。
