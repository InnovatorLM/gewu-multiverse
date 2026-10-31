---
name: acs-quality-rollout-review
description: Independently evaluate a frozen Harbor task with five ACS rollouts and inspect trajectories and verifier evidence.
---
# 五次独立 ACS 质量评测

仅 evaluator 使用，先阅读 /skills/harbor-acs-evaluation/SKILL.md。依据 /home/role/review-assignment.json 中的具体任务和 commit 工作；无派单时等待，不选择任意旧题试跑。

使用 /evaluation/catalog.json 中对应本次版本的已注册项；向 /evaluation/inbox 写请求，通过 /evaluation/results 读取结果。请求 schema 为 job_id、evaluation_id、snapshot_sha256，job_id 为32位小写十六进制。注册目录没有本次版本时报告 waiting_platform，请求注册，不猜测 ID，不伪造结果。

先做完整性与 runtime/工具调用 smoke。之后用指定 dawnfm / deepseek-v4.1-flash-1017 独立运行五次，默认4c/8Gi、资源不足最高8c/16Gi、不限解题步数、每次4小时。检查实际返回配置，不能只因本文件写了就认为生效。

保存每次 result、agent轨迹、verifier输出、镜像digest、run ID及清理证据。基础设施/适配器失败或无verifier结果不能算模型答错；先修复补跑。四小时超时先查题目缺失与环境缺陷；排除后确属难题才计模型失败。有效通过率<=60%可接收，但必须结合科学正确性、题意/测试一致性、捷径检查和轨迹审查，不能用五次全错自动证明高质量。

作者自测不等于独立评测。只对所派不可变版本输出结论；用 role-review-status 记录状态（先看 --help），平台问题与作者问题分开交接。
