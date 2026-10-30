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

## 已完成真实控制测试

openssl-selfsigned-cert冻结源码f64efc6cdf097edd5df306fb16be544d08e384e6；Codex0.164.0／rg15.2.0镜像已发布上海ACR。北京ACS cn-beijing-i实际oracle reward1，nop reward0；两次trial均无exception，控制器退出0，已知Pod404和两次空资源检查确认清理。

同一镜像Codex／dawnfm／deepseek-v4.1-flash-1017真实做题smoke reward1，无exception，cleanup confirmed，agent/trajectory.json为52013字节，codex.txt为27258字节。五次独立模型运行已启动但尚未全部完成，不作为新题质量结论。

最新非特权完整Rust回归345通过，Python组合回归25通过。新增能力回执实际探针发现author02缺pydantic，说明环境仍未全通过；已开始停机角色离线补包。启动器增加启用角色能力门检，不能因安装marker存在就开工。

## 五次真实模型链路验收

2026-10-30，同一已冻结openssl-selfsigned-cert测试题，指定dawnfm／deepseek-v4.1-flash-1017，Codex0.164.0，4c/8Gi，在北京ACS cn-beijing-i独立顺序运行5次。5/5均reward1、exception为空、控制器退出0；5份agent/trajectory.json存在并逐份计算SHA256，5次cleanup confirmed。私有证据：workspace/.state/universe-repair-20261030/five-model-trials-v1/summary.json及各trial原始产物。

这是既有简单题的基础设施回归，不能作为新科学题质量接收；五次全对也不满足目标新题<=60%的难度口径。作者自测队列自身端到端、作者迭代凭证、独占评审、新角色启动、reset及计时联动仍须继续验收。

作者自测增加脱敏日志回传（有限尾部、不暴露原始运维凭证），子进程回收及损坏中断回执恢复；10项相关测试及后续9项恢复回归通过。author02完整依赖导入和C++编译运行通过；evaluator独立环境副本仍在配置，不宣称全部环境就绪。

## 自测上传与实际worker验收

上传请求和tar使用O_NOFOLLOW／O_NONBLOCK打开后按文件描述符校验普通文件、UID、长度及读取前后mtime／ctime，冻结输出0600且不可覆盖；避免检查后换成链接／FIFO或增长文件。上传、Git内容绑定、Codex构建入口、中断恢复、子进程清理和脱敏日志组合16项回归通过。

新增accept_author_selftest.py，以冻结的既有openssl题创建隔离上传并调用真实worker，实际构建发布和ACS oracle／nop，不替代作者自解与迭代签发。已启动worker-acceptance-v1，job a48379ab304f427da5482897d326fc7a，上传15个文件与fixture Git树绑定通过；完整构建与云端终态尚在验收。证据目录workspace/.state/universe-repair-20261030/worker-acceptance-v1。

reset与新版部署通过共享／独占生命周期锁互斥，15项相关回归通过；仍要求先停监督器和控制器，尚未实现生产在线单角色reset。旧宇宙保持停止。

## 2026-10-31 生命周期与策略修复

- command_watchdog纳入启动器持有的子进程，退出时TERM并wait，启动控制器前检查所有服务PID；不再依赖人工独立启动。真实启动行为尚须新部署验收。
- 一小时本地命令干预先TERM再按UID／启动时刻／进程组身份核验后KILL，避免忽略TERM的命令持续占用。真实临时进程忽略TERM的回归通过；不干预独立ACS作业，不自动判定题目死胡同。
- 初始化不再复制旧pilot评审反馈到活跃工作区；已有副本保留在.historical-feedback并注明由当前instruction／skill取代，拒绝符号链接和冲突覆盖。该变更及watchdog／启动就绪共8项回归通过。
- worker实际构建发布完成，oracle reward1、exception为空、cleanup confirmed；nop仍在运行，完整worker终态尚未取得，不能写成全部通过。
- 评审环境复制tar进程仍存活且归档持续增长；没有重复启动。旧宇宙未恢复，新宇宙未创建。

### 真实worker终态已取得

worker-acceptance-v1／a48379ab304f427da5482897d326fc7a进程退出0，result.json状态selftest_passed。真实上传15个文件与Git树绑定，实际构建并发布official／Codex runtime／verifier；ACS oracle reward1、nop reward0，两次控制器均退出0、exception为空、cleanup_confirmed=true。作者可见回执及diagnostics文件已生成。该测试使用运维隔离fixture，不是生产角色亲自提交的行为验收，不签发作者自解／迭代凭证，也不表示科学题被接收。

后续仍须证明：角色身份提交和读取回执、作者基于结果迭代后复跑、正式审核资格签发及独占评测；会话计时自动联动、在线reset、新角色环境和上下文摘要；最终备份合并及新宇宙行为验收。不得将本节成功扩写为46项全部完成。
