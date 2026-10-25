# 官方 TB-Science 经验摘要

参考固定导入版本 1892516e4321ebffb307de3b638506582ef28916；这不是对上游当前规范的自动同步。

- 高质量任务来自真实研究工作；科学术语、教学数据和一键标准分析不能证明研究级难度。需解释领域知识为何不可替代。
- 真难度可以来自级联误差、真实科研软件、数值/建模判断和研究流程；不要大量生成再筛选当前模型的狭窄弱点。
- 指令与结果验证要对齐；不能把作者自选约定隐藏起来。容差须有科学依据，接受等价结果与合法替代路径。
- 依赖、数据和资源需要可复现；环境错误、配额、随机超时不是能力失败。成功与失败都应保留，不能挑选性报结果。
- 先少量试跑暴露明显缺陷，修复后再加证据；已有轨迹可以重分析，不要为每个文字改动重复昂贵试跑。
- 全失败不直接证明题目难：需要检查可解性、验证器和说明完整性。提示使模型成功时，要区分提示补了缺失规范还是揭示了解法。
- 快速成功不必然说明太简单；判断解题是否要求实质科学工作，样本不足则承认不足。
- 作者自检、独立 solver、质量 evaluator 和 curator 是不同职责。官方采用多阶段人类评审，本宇宙使用 AI 不能伪装成同等人类背书。
- `TB-Science-wangjunxi` 的流程强调 Seed Enhancer → Task Builder → Verifier 的分阶段新鲜 sandbox、标准 Harbor 任务包、独立 verifier 容器、声明式 artifacts、干净参考解到测试运行和失败证据保留。作者 instruction 应把这些作为题目完成和自检的最低结构要求。
- 该流程还表明，题目合成阶段应清理缓存和临时文件、固定资源与超时、保留每阶段轨迹和结果、拒绝覆盖非空输出目录，并将生成失败与发布失败分开记录。
- 题目难度应通过独立模型 trial 的正确率、token 使用量、模型/工具调用次数和耗时综合观察；低正确率本身不能证明科学质量，环境故障和 verifier 缺陷必须单独归因。
- 题目审核路线已经验证可先用 ACS 产生标准 Harbor trial，再进行题目直接评分、题目 WinRate、轨迹直接评分和轨迹 WinRate；轨迹评分要求 `config.json`、`result.json`、ATIF `agent/trajectory.json`、verifier 输出和完整题包，Markdown 手工轨迹不能直接替代。

来源：导入仓库 CONTRIBUTING.md（Task Difficulty/Quality/Test）、REVIEWING.md、rubrics/task-proposal.md、rubrics/task-implementation.toml、rubrics/trial-analysis.toml。公开经验只传递通用方法，不传递内部攻击样例、私有 judge 提示词或隐藏数据。
