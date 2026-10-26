import hashlib, json, os, subprocess, sys
from pathlib import Path
w = Path('/mnt/data/zhanglinfeng/workspace')
repo = w / 'repos/unified-evaluator-pipeline'
root = w / '.state/role-chroot-proof'
assets = repo / 'unified_evaluator/assets'
prompt = (assets / 'prompts/quality.md').read_text().replace('{{RUBRIC}}', (assets / 'rubrics/quality.yaml').read_text())
prompt = prompt.replace('The Codex harness enforces the workspace permissions and disables network access.', 'An external non-root chroot enforces file access. Network access is permitted for this run.')
prompt += '\nReview task_id robust-sensor-calibration at /task. Scratch directory is /tmp. Use shell tools with tty=false. Finish within 12 shell calls. Do not inspect /runtime.\n'
command = ['timeout', '600', 'chroot', '--userspec=21002:21002', str(root), '/usr/bin/env', 'HOME=/home/review', 'CODEX_HOME=/home/review', 'PATH=/usr/local/bin:/usr/bin:/bin', 'TMPDIR=/tmp', 'LANG=C', 'LC_ALL=C', 'REVIEW_SCRATCH_DIR=/tmp', '/usr/local/bin/codex', '--no-daemon', 'exec', '--skip-git-repo-check', '--ephemeral', '--ignore-rules', '--cd', '/task', '--json', '--output-last-message', '/runtime/quality-answer.json', '-']
out = w / '.state/harbor-eval'
with (out / 'chroot-quality-events.jsonl').open('w') as events, (out / 'chroot-quality-stderr.log').open('w') as errors:
    result = subprocess.run(command, input=prompt, text=True, stdout=events, stderr=errors)
print(json.dumps({'exit_code': result.returncode}))
if result.returncode:
    sys.exit(result.returncode)
sys.path.insert(0, str(repo))
from unified_evaluator.pipelines.quality_review.review import validate_and_score, load_rubric
answer = json.loads((root / 'runtime/quality-answer.json').read_text())
rubric, _ = load_rubric()
answer = validate_and_score(answer, 'robust-sensor-calibration', rubric)
calls = []
usage = {}
for line in (out / 'chroot-quality-events.jsonl').read_text().splitlines():
    event = json.loads(line)
    item = event.get('item', {})
    if event.get('type') == 'item.completed' and item.get('type') == 'command_execution':
        calls.append(item.get('exit_code'))
    if event.get('type') == 'turn.completed':
        usage = event.get('usage', {})
answer['review_metadata'] = {'transport': 'nonroot-chroot', 'uid': 21002, 'successful_shell_commands': sum(code == 0 for code in calls), 'shell_calls': len(calls), 'usage': usage, 'production_launcher_wired': False}
(out / 'chroot-quality-validated.json').write_text(json.dumps(answer, indent=2))
print(json.dumps({'gate': answer['gate'], 'quality_score': answer['quality_score'], 'metadata': answer['review_metadata']}))
