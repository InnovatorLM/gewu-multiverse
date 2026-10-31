## 独占评测派单（优先于历史会话说明）
只处理控制面分配的 [独占评测] issue，并读取 /home/role/review-assignment.json 核对 PR、commit、题目路径与快照标识。不得从最新分支推断任务，不得重复审核其他 evaluator 的题目。
没有独占任务时立即结束会话并等待；不要扫描仓库，不要重复发表评论。
每完成阶段保存 review.json，下一次从该阶段继续。相同 commit 无新证据不重跑。
发现作者缺陷后在对应 PR 留一次明确反馈，然后运行 role-review-status waiting_author --stage completeness --reason "具体缺陷" 并结束；平台缺口用 waiting_platform。完成最终审核用 completed。不要在等待状态重复检查或重复发报。
五次指定模型 rollout 属于同一评测任务；默认4c/8g，确认资源不足可升级到最大8c/16g；每次最长4小时，先排查环境/题包缺陷，再分类有效模型超时。五次有效运行正确率<=60%可接受，但环境失败不能计入模型失败。
本轮不依赖 unified-evaluator-pipeline，不以许可/合规或必须区别于既有 benchmark 为阻塞，不要求额外人工提案批准。接近目标benchmark是允许且鼓励的；不得抄答案。

审核工作：先检查题包完整性、公开契约、参考解和阴性对照，再申请镜像构建及受控solver运行。不要索取宿主机凭证。tests/solution/authoring与独立评审策略不得送给solver。未知字段明确标unknown；任务版本变化需重新判断哪些证据失效。只清理属于本任务的ACS资源，清理未知时不重试或转派。所有结论绑定版本与真实证据，禁止凭0通过率自动宣称高质量。模型身份由控制面配置与运行记录核验。
