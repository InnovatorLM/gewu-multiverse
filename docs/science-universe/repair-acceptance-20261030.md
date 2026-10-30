# 宇宙修复与重建验收记录

用户目标保持完整：停止旧宇宙，逐项解决46项清单，充分测试，备份代码，确认后创建新宇宙。当前不宣称全部修复。

## 已取得证据

- 已读取指定 pasted-text-1.txt。
- 旧 supervisor、控制器、launcher、自测worker与watchdog 已按进程身份验证后SIGTERM，shutdown.json记录均已退出。派单和评测worker随launcher退出。
- 开始修改前已备份 tracked＋untracked source 到 workspace/.state/universe-repair-20261030/pre-repair-source.tar.gz，0600。
- 自测队列：已修复未终态任务因workdir存在而静默忽略，改为保留证据并签发 interrupted终态，要求新提交和cleanup核查；不将不确定云任务直接自动重放。
- 自测构建：移除任意FROM改写，保留题包语义，暂对非digest基础镜像明确拒绝；原始镜像自动解析与可信内容绑定仍待完成。
- 自测worker：增加退出信号处理和子进程组超时回收；实际云端cleanup仍需验收。
- nop不再被误认为需要LLM凭证的模型agent。
- 预装包清单补齐探针要求的库，测试marker版本改为读取实际常量。
- 本批局部测试：生命周期4项、构建provenance3项、非模型control2项、预装2项全部通过。不能据此宣称真实ACS链路成功。

## 必须继续完成

对46项逐项建立当前证据与验收，尤其自测真实镜像构建和ACS oracle/nop、五次模型评测、新角色能力回执、独占派单与唤醒、reset完整行为、上下文摘要/增量轨迹、原生脱敏、时间预算/长任务、软件环境、存储、监控和发布。

完成必要本地/集成/真实云测试并保留结果，保存最终代码并验证远端备份和合并状态，再创建隔离的新宇宙。旧宇宙保持停止；不得因局部单测通过提前上线。
