# 作者正式提交凭证登记

`deploy/science/register_author_preflight.py`补上已有门检验证器到独占派单器之间的发布入口。它仅供运维使用，不是新的用户上线审批环节，也不是自动科学质量接收。

先审阅真实执行证据：冻结提交及镜像digest、作者亲自完成的解题过程、根据运行结果所作修改、修改后复跑、正负对照，以及同一思路累计有效迭代时间。不得用简单题基础设施验收、oracle执行、作者自行填写的布尔值替代作者自解和迭代证据。现阶段这一步仍需运维核实原始产物，尚未自动接入生产作者会话。

整理为root所有、不可被角色写入的JSON，字段服从`author_submission_gate.validate_receipt`；`evidence_files`包含私有真实产物路径与SHA256。预检示例：

```bash
PYTHONPATH=deploy/science python3 deploy/science/register_author_preflight.py \
  --receipt /mnt/data/zhanglinfeng/workspace/.state/reviewed-preflight.json \
  --commit '<40位提交号>' --task 'tasks/<题目>'
```

不带`--apply`不创建资格。运维核对证据后，同一命令添加`--apply`，将验证通过的凭证以0600原子发布到`.state/science-author-preflight`。已有同提交同题目凭证不覆盖；凭证来源哈希和登记时间保留。派单器每次仍验证源提交、证据哈希与预算，证据变化立即导致拒绝，而不是永久缓存成功。

测试用合成凭证验证发布机制，不代表任何生产题目已获资格。生产作者自主调用自测、证据审核与派单行为仍需整体验收。

## Codex 评测配置生成

不要直接复用历史 Mini-SWE-Agent 的 600 秒／40 步模板。使用已发布的 Codex 构建回执生成新配置：

```bash
PYTHONDONTWRITEBYTECODE=1 \
  /mnt/data/zhanglinfeng/workspace/acs-harbor-test/.venv/bin/python \
  deploy/science/codex_evaluation_template.py \
  --base /workspace-local/path/base-template.json \
  --build-receipt /workspace-local/path/build/receipt.json \
  --output /workspace-local/path/codex-template.json
```

上面的 `/workspace-local/path` 是占位符，实际所有路径必须位于 `/mnt/data/zhanglinfeng/workspace`。生成器从回执取固定 digest 与实际 Codex 版本，显式设置 dawnfm／DeepSeek／Responses、四小时、无步数限制、4c/8g、北京 i 节点以及零自动重试。密钥仍是运行时占位符，不写入配置。生成配置不代表完成科学评测；后续须按现有登记入口绑定原始提交、题包及构建回执。

五次评测由同一独占派单生成五个独立任务，队列默认并行度为五；每个任务内部仍是一次 attempt、并发一。平台回归使用已有简单题，不能将其高通过率误作科学新题接收。


## 自动交接（思路绑定的新作业）

作者先用 `author-iteration-clock start <idea-id>` 建立稳定思路，并在每次 `role-acs-selftest submit` 加 `--idea <idea-id>`。读取前一次真实执行结果、修改并提交新版本后，使用 `--previous-job`、`--iteration-note` 和 `--request-review` 请求自动交接。初始化会安装当前客户端。

自测worker保存平台接收时间、完成时间和每次ACS调用起止。交接服务核对原始提交／冻结执行身份、正负对照、前一完成作业、同思路和真实修改，再根据operator已观测的思路事件及实际ACS区间计算主动时间保守上界。重叠ACS区间只扣一次；作者自报秒数和未经验证的等待不予退款。上界超出时等待补充证据，不假称实际主动工作必然超时。首次观测前的起点仍明确标为未独立证明，不宣称防止作者事前隐瞒工作。

资格生成与科学审核分离：显式请求审核表示作者认为方向仍可行，不是平台证明难度足够。平台先登记不可变执行，成功后才发布版本绑定的作者资格；dispatcher随后的PR轮询派给唯一evaluator。登记失败可恢复，重复轮询复用登记；未完成／中断自测不发布资格，不覆盖已返回的中断状态。返回stage/reason指导修复，evaluator仍独立检查质量与五次难度。

原始operator记录不会因更新回传状态而改写。作者可见的脱敏诊断包含构建日志尾部及oracle/nop的verifier stdout、CTRF尾部，以支持真实结果驱动迭代；不包含云端凭证或其它角色私有材料。
