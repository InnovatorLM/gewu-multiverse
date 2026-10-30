---
name: harbor-acs-evaluation
description: Prepare a Harbor task for real ACS container execution, request platform execution, and inspect version-bound evidence.
---
# Harbor 真实容器自测

作者完成题包实现后、正式提交审核前必须使用本流程；评测者用它核查环境和基础运行证据。本 skill 是隔离角色版本，不要求访问宿主凭证或旧 unified-evaluator-pipeline 仓库。

1. 固定题目仓库、分支、commit 和 task 相对路径。核对 instruction.md、task.toml、environment/Dockerfile、tests/test.sh、solution/solve.sh 及其引用文件；做 schema、shell 语法、输入输出和依赖检查。尚未实现的提案不要求提前拥有完整题包。
2. 本地原型可以辅助调试，但改写绝对路径的目录模拟不能证明镜像可构建或 ACS 可运行。隔离工作区没有 Docker 不表示应跳过真实容器自测。
3. **作者执行入口**：当前尚无作者可直接调用的自动 ACS 自测命令。将固定 commit 推送到自己的候选分支，使用已有 Forgejo 工具在自己的任务 issue 或草稿 PR 提交一次“平台容器自测请求”，列出 task 路径、commit、参考解命令、verifier 命令、资源及本地证据路径。明确标为 waiting_platform，不作为正式独立审核申请。不要自行编造 CLI、job ID 或成功凭证；没有新反馈时不重复请求。
4. 平台应执行：格式校验→构建并发布 ACR 镜像→记录不可变 digest→ACS 启动→作者参考解→verifier 正对照及空/错误答案负对照→结果驱动修复→新版本复跑。请求默认 4c/8Gi，确认不足才最高 8c/16Gi；不使用 cn-beijing-f。
5. 等待返回 commit、镜像 digest、run ID、日志、verifier 输出、轨迹和清理记录。只接受与本次版本一致的实际证据；缺证据标为 incomplete/waiting_platform，不能写“容器通过”。ACS 运行时间不计入五小时主动迭代预算，但必须有真实 run ID 才可扣除。
6. 完成作者自解、反思修改及复跑后，再主动申请独立审核。作者自测不能替代 evaluator 五次独立评测。

评测者已有入口为 /evaluation/catalog.json、/evaluation/inbox 和 /evaluation/results，只允许使用已登记 evaluation_id 与 snapshot_sha256；不能把旧题登记项用于新题。需要注册新版本时明确请求平台注册。

任何角色都不得读取宿主 kubeconfig、ACR/模型密钥，或把密钥写进题包、镜像、issue、日志。保留工作区原始证据；清理只针对本次 run 的资源。
