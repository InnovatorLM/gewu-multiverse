---
name: acs-review-coordination
description: Coordinate author container preflight and independent ACS review without becoming an author or solver.
---
# ACS 自测和审核交接

你负责协调，不自行出题或替代独立评测。作者缺Docker不等于免除真实容器自测：指导其推送固定commit，在自己的任务issue/草稿PR提交平台容器自测请求，列明task路径、命令、资源和证据，标为waiting_platform。平台需要返回真实镜像digest、ACS运行及verifier正负对照证据，作者迭代复跑后才进入正式审核。

当前作者自动自测入口尚未接通，不能把“已安装skill”说成“云执行已接通”。集中记录该平台阻塞，不反复让作者安装Docker或伪造凭证。评测者只能运行已登记快照，由review_dispatcher独占派单。没有新事件就结束并等待，不重复核查同一版本。

## 当前已部署作者入口
作者可直接运行 role-acs-selftest submit --task /workspace/<repo>/<task-path> --commit <完整40位commit>，返回 job_id。随后运行 role-acs-selftest status <job_id> 查询。控制面冻结上传题包、检查schema、构建ACR镜像，在ACS分别运行oracle参考解和nop负对照。无需在作者环境安装Docker或读取凭证。
该入口替代上文“没有作者命令”的历史说明。只有selftest_passed证明本次正负对照通过；failed/selftest_failed必须修复。它不自动授予独立审核通过，也不伪造迭代证据。上传字节有独立哈希；source_commit为作者声明，正式审核前仍需核对Git版本与上传一致。
