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
