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

## 第二批进展

- 核心引擎57项回归通过。题包Git提交逐文件与执行权限绑定新增2项测试通过。
- 增加模型历史摘要：达到240KB上下文阈值后，用同一已配置provider/model生成持久检查点，保留原始instruction与完整最近工具交换。摘要失败不静默丢弃历史。2项上下文边界测试通过；真实API摘要和中断恢复仍待验收。
- 监控改为有限尾部读取，避免每次刷新读取完整大轨迹；简报过滤十分钟前事件，并追加持久历史。4项监控测试通过；部署与网页行为仍待验收。
- 消除ACS skill“无入口”与“已有入口”矛盾说明，明确真实CLI和Git校验。技能安装测试2项通过，新会话技能加载仍待验收。
- 修正模型所见120秒命令上限说明；实际执行使用会话上限，尚待统一单命令剩余时间与长任务机制。
- 完整Rust单元测试正在运行：日志为workspace/.state/universe-repair-20261030/all-rust-tests.log。
- 旧宇宙仍停止，新宇宙未创建。本阶段尚未证明真实ACS oracle/nop、五次模型评测和最终merge。

## 第二批补充验证

- 原始基础镜像可解析为digest：在独立effective context修改FROM引用，保留source snapshot、平台参数、多阶段别名与其他Dockerfile指令。解析映射写入build receipt。2项解析测试和3项构建provenance回归通过。真实构建仍待验证。
- 完整Rust root运行结果342通过、2失败；两项失败是权限fixture在root可绕过限制。以生产controller UID65534单独运行两项均通过，未跳过断言；完整非特权344项重跑进行中。
- ACS当前API可达，节点列表包含cn-beijing-i；Docker服务28.1.0可达。仅为当前只读连通证据，不代表题目运行成功。

## 全量回归与真实构建

生产controller身份UID65534完整Rust测试344通过、0失败，含两项权限边界测试。当前已启动既有TB2 openssl-selfsigned-cert任务的真实构建，源码冻结提交f64efc6cdf097edd5df306fb16be544d08e384e6，Codex0.164.0和ripgrep15.2.0；不是新增自编题。构建目录及日志在workspace/.state/universe-repair-20261030/openssl-build-v1。镜像构建、发布与ACS结果仍待最终回执；不可根据作业启动宣称通过。

## 第三批修复与当前在运行测试

- 平台等待／会话暂停计时已实现，保留单题累计有效预算；8项计时测试通过。需继续接入会话生命周期自动暂停，不能把CLI状态机等同自动执行。
- worker正常退出的包装进程也回收同组子进程，防止退出0后后台继续写；生命周期5项测试通过。
- Docker Hub直拉返回unknown；相同版本官方Python镜像从public.ecr.aws/docker/library拉取成功。仅在显式GEWU_DOCKER_LIBRARY_MIRROR配置下映射官方library镜像，原始引用与digest映射留在receipt。解析3项测试通过。
- 真实openssl构建v2已启动，仍在运行；不得并行重试同一job。会话12417，日志openssl-build-v2.log。
- 修正run_guard启动时扫描即删除其他旧run的问题，改为只读观察；本次release仅清理自己的run资源，需补回归。
- native system prompt嵌入已安装SKILL.md内容，避免只有路径而模型无技能正文；目标回归编译/执行中，会话35013。
