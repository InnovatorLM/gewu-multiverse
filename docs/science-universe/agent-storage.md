# 多出题实例存储

当前设计按实例隔离，而非按角色共享。所有宿主路径在 workspace 下。

## 布局与生命周期

实例根：`universes/my-terminal-bench-science/.config/gewu-multiverse/agents/author-NN/`。

| 实例内路径 | 语义 |
| --- | --- |
| `/workspace` | 持久项目文件；各实例独立 Git clone，不使用跨实例 Git worktree 或共享 .git |
| `/home/role` | 私有持久 HOME、Git 配置；禁止复制其他实例 HOME 或 API 密钥 |
| `/tmp` | 实例私有临时数据；停止并确认无进程后才可清理 |
| `/cache` | 实例私有缓存；不得通过共享可写缓存传递代码或凭证 |
| `/runs` | 实例产生的运行记录；按 run id 分目录并归属 agent id |
| `/references` | 控制面发布的只读公共资料快照；角色不可修改 |

系统工具当前独立复制，避免可写硬链接污染其他实例。公共参考资料从同一公开源发布为只读副本，暂不挂载共享可写目录。未来大规模部署可使用真正只读挂载，不能用指向宿主机路径的 symlink 冒充挂载。

协作通过 Forgejo 仓库、PR、issue、经验帖与各自分支进行。每个新实例应有独立 Forgejo 身份及最小权限凭证；存储创建器不自动复制旧 author 的 token。Git 中可以共享已提交成果，不共享未提交工作文件、凭证、原始私有证据。

ACS 每次 trial 使用独立临时文件系统；控制面在删除前回收 sessions、trajectory、verifier 与结果，持久保存到 `acs-harbor-test/runs/<job>/`。运行元数据需要关联 author instance、task commit、image digest、job/trial id。ACR 仅存镜像，不保存运行数据。

## 创建与启用边界

运行 `deploy/science/provision_author_storage.py --name author-01 --uid 22001`；为下一实例选择独立且未使用 UID。脚本拒绝覆盖已有实例，也拒绝重复 UID。不创建模型或 Git 凭证、不启动 agent、不改写现有 author 或生产 broker 配置。

`storage.json` 记录已创建目录与未完成的启用状态。正式启用还需独立 Git 身份、engine agent 注册、broker 的实例映射与重载，并确认命令、HOME/TMPDIR/cache 都指向该实例。不能仅凭目录存在宣称多个生产 agent 已运行。broker 校验支持 author-NN 名称；旧三角色仍保留。

## 保留与容量

停止或重新启动不删除工作区和 HOME。当前没有强制磁盘配额，不设每个 agent 的任务数或模型调用额度。临时目录与缓存可在实例停止后由控制面清理；工作区、Git 未推送提交和轨迹不自动删除。禁止清理其他实例或尚未回收证据的 ACS 资源。所有实例当前仍共享宿主存储容量，目录隔离不等于磁盘容量隔离。

这是 Unix UID/chroot 文件隔离，不是独立内核或网络隔离；控制面可以管理所有目录，agent 不应拥有宿主 root 权限。
