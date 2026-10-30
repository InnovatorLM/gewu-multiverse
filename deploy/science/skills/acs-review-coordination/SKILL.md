---
name: acs-review-coordination
description: Coordinate author container preflight and independent ACS review without becoming an author or solver.
---
# ACS 自测和审核交接

你负责协调，不自行出题或替代独立评测。作者缺Docker不等于免除真实容器自测：指导其推送固定commit，在自己的任务issue/草稿PR提交平台容器自测请求，列明task路径、命令、资源和证据，标为waiting_platform。平台需要返回真实镜像digest、ACS运行及verifier正负对照证据，作者迭代复跑后才进入正式审核。

当前作者自动自测入口尚未接通，不能把“已安装skill”说成“云执行已接通”。集中记录该平台阻塞，不反复让作者安装Docker或伪造凭证。评测者只能运行已登记快照，由review_dispatcher独占派单。没有新事件就结束并等待，不重复核查同一版本。
