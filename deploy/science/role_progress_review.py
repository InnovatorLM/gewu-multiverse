"""Read-only dead-end hints. No automatic reset; elapsed time alone proves nothing."""
import argparse, collections, json
from pathlib import Path
from role_reset import U
from trajectory_requests import replay

def assess(events):
    recent = collections.deque(maxlen=30); last_request_chars=0; last_skills=None;finish=None
    previous_request=None; replay_errors=0
    for event in events:
        kind=event.get('event');turn=event.get('turn')
        if kind=='tool_result':
            output=event.get('output','')
            failed=event.get('exit_code') not in (None,0) or 'Traceback (most recent call last)' in output
            recent.append(dict(failed=failed, masked=failed and event.get('exit_code')==0, duration=event.get('duration_ms',0)))
        if kind=='model_request':
            body=event.get('body','')
            last_request_chars=len(body)
            try:record=json.loads(body)
            except (ValueError,TypeError):previous_request=None
            else:
                is_delta=isinstance(record,dict) and record.get('format')=='gewu.request-delta.v1'
                try:previous_request=replay(previous_request,record)
                except ValueError:
                    previous_request=None; replay_errors+=1
                    if is_delta:last_request_chars=None
                else:
                    if is_delta:last_request_chars=len(json.dumps(previous_request,ensure_ascii=False,separators=(',',':')))
        if kind=='skills_discovered':last_skills=len(event.get('skills',[]))
        if kind=='run_finished':finish={k:event.get(k) for k in ('outcome','reason','ts')}
    reasons=[]
    errors=sum(x['failed'] for x in recent)
    if errors>=8:reasons.append('Many recent tool failures; inspect whether they are expected negative controls or repeated unresolved defects')
    if last_request_chars is not None and last_request_chars>=500000:reasons.append('Large accumulated request history; consider a concise handoff and fresh context')
    if replay_errors:reasons.append('Request replay failed; context size is unverified until a valid full checkpoint is available')
    if any(x['duration']>=3600000 for x in recent):reasons.append('At least one recent local command exceeded one hour; inspect progress and complexity')
    if any(x['masked'] for x in recent):reasons.append('Traceback with zero exit status observed; inspect actual success artifacts')
    if last_skills == 0:reasons.append('No skills discovered in this archived session; verify the effective startup capabilities before rescheduling')
    if finish and finish.get('outcome') in ('failed','timed_out'):
        terminal_reason=finish.get('reason') or ''
        if 'max_turns' in terminal_reason:reasons.append('Session exhausted its configured turn limit; inspect effective role configuration before blaming the model')
        elif finish.get('outcome') == 'timed_out':reasons.append('Session timed out; distinguish active work, platform waits and the per-idea iteration budget')
    return dict(recommendation='manual_review' if reasons else 'no_hint',reasons=reasons,last_request_chars=last_request_chars,request_replay_errors=replay_errors,
        recent_tool_count=len(recent),recent_failed_tools=errors,skills_discovered=last_skills,last_finish=finish,
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
