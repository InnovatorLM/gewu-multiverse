"""Read-only dead-end hints. No automatic reset; elapsed time alone proves nothing."""
import argparse, collections, json
from pathlib import Path
from role_reset import U

def assess(events):
    calls = {}; recent = collections.deque(maxlen=30); requests=[]; checks=[];finish=None
    for event in events:
        kind=event.get('event');turn=event.get('turn')
        if kind=='tool_call':calls[turn]=event.get('command','')
        if kind=='tool_result':
            output=event.get('output','')
            failed=event.get('exit_code') not in (None,0) or 'Traceback (most recent call last)' in output
            recent.append(dict(failed=failed, masked=failed and event.get('exit_code')==0, duration=event.get('duration_ms',0)))
        if kind=='model_request':requests.append(len(event.get('body','')))
        if kind=='skills_discovered':checks.append(len(event.get('skills',[])))
        if kind=='run_finished':finish={k:event.get(k) for k in ('outcome','reason','ts')}
    reasons=[]
    errors=sum(x['failed'] for x in recent)
    if errors>=8:reasons.append('Many recent tool failures; inspect whether they are expected negative controls or repeated unresolved defects')
    if requests and requests[-1]>=500000:reasons.append('Large accumulated request history; consider a concise handoff and fresh context')
    if any(x['duration']>=3600000 for x in recent):reasons.append('At least one recent local command exceeded one hour; inspect progress and complexity')
    if any(x['masked'] for x in recent):reasons.append('Traceback with zero exit status observed; inspect actual success artifacts')
    if checks and checks[-1] == 0:reasons.append('No skills discovered in this archived session; verify the effective startup capabilities before rescheduling')
    if finish and finish.get('outcome') in ('failed','timed_out'):
        terminal_reason=finish.get('reason') or ''
        if 'max_turns' in terminal_reason:reasons.append('Session exhausted its configured turn limit; inspect effective role configuration before blaming the model')
        elif finish.get('outcome') == 'timed_out':reasons.append('Session timed out; distinguish active work, platform waits and the per-idea iteration budget')
    return dict(recommendation='manual_review' if reasons else 'no_hint',reasons=reasons,last_request_chars=requests[-1] if requests else 0,
        recent_tool_count=len(recent),recent_failed_tools=errors,skills_discovered=checks[-1] if checks else None,last_finish=finish,
        caution='Hints are not a dead-end verdict. Expected failed controls, healthy computation and platform waits must be reviewed separately. No process was signalled.')

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('role');args=parser.parse_args()
    if args.role not in {'curator',*[f'author-{i:02}' for i in range(1,11)],*[f'evaluator-{i:02}' for i in range(1,4)]}:raise ValueError('Unknown role')
    runs=list((U/'.state/gewu-multiverse'/args.role).glob('run-*'))
    if not runs:raise ValueError('No runs')
    run=max(runs,key=lambda p:p.stat().st_mtime)
    with (run/'transcript.jsonl').open() as stream:result=assess(json.loads(line) for line in stream if line.strip())
    print(json.dumps(dict(role=args.role,run=run.name,**result),ensure_ascii=False,indent=2))
if __name__=='__main__':main()
