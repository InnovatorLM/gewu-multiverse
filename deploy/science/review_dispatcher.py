"""Single-writer PR review dispatch. Local Forgejo only; no solver/cloud actions."""
import argparse,fcntl,hashlib,json,os,re,time,urllib.request
from pathlib import Path
W=Path('/mnt/data/zhanglinfeng/workspace')
STATE=W/'.state/science-review-dispatcher'
REPO='/repos/team/terminal-bench-science'
MARK='<!-- exclusive-review-v1 -->'
STATES={'reviewing','waiting_author','waiting_platform','completed'}

def atomic(path,data):
    stage=path.with_suffix('.pending');stage.write_text(json.dumps(data,ensure_ascii=False,indent=2));stage.chmod(0o600);stage.replace(path)

def fingerprint(pr,comments):
    # Evaluator self-comments never wake their own waiting task.
    relevant=[(c['id'],c.get('updated_at')) for c in comments if not c.get('user',{}).get('login','').startswith('gewu-evaluator')]
    return hashlib.sha256(json.dumps([pr['head']['sha'],relevant],sort_keys=True).encode()).hexdigest()

class Api:
    def __init__(self,token):self.token=token
    def call(self,method,path,data=None):
        req=urllib.request.Request('http://127.0.0.1:3000/api/v1'+REPO+path,data=json.dumps(data).encode() if data is not None else None,method=method,headers={'Authorization':'token '+self.token,'Content-Type':'application/json'})
        with urllib.request.urlopen(req,timeout=30) as response:return json.load(response)
    def pages(self,path):
        out=[]
        for page in range(1,1001):
            batch=self.call('GET',path+('&' if '?' in path else '?')+'limit=50&page='+str(page))
            if not batch:return out
            out+=batch
        raise ValueError('Pagination did not terminate')

def reconcile(api,config,ledger):
    pulls=api.pages('/pulls?state=open')
    for pr in pulls:
        if pr.get('draft') or 'draft' in pr['title'].lower():continue
        match=re.search(r'tasks/[a-zA-Z0-9_./-]+',pr.get('body') or '')
        if not match:continue
        task=match.group(0).rstrip('./');key=str(pr['number'])+':'+pr['head']['sha']
        comments=api.pages('/issues/'+str(pr['number'])+'/comments');event=fingerprint(pr,comments)
        if any(v['pr']==pr['number'] and k!=key and v['state']=='reviewing' for k,v in ledger.items()):
            continue  # Finish or park prior revision before assigning the new one.
        row=ledger.get(key)
        if row is None:
            busy={v['role'] for v in ledger.values() if v['state']=='reviewing'}
            roles=[n for n in config['roles'] if n.startswith('evaluator-') and n not in busy]
            if not roles:continue
            role=sorted(roles)[0]
            # Task subtree identity, not a claim of image or tarball digest.
            entries=api.call('GET','/contents/'+task+'?ref='+pr['head']['sha'])
            if not isinstance(entries,list):continue
            inventory=sorted((e['name'],e['sha'],e['type']) for e in entries)
            snap=hashlib.sha256(json.dumps(inventory,separators=(',',':')).encode()).hexdigest()
            row={'pr':pr['number'],'commit':pr['head']['sha'],'task':task,'snapshot_sha256':snap,'snapshot_kind':'sha256-of-git-entry-inventory','role':role,'state':'reviewing','stage':'completeness','event':event,'generation':0,'issue':None,'updated_at':time.time()}
            ledger[key]=row;atomic(STATE/'ledger.json',ledger)
        root=Path(config['roles'][row['role']]['root']);receipt=root/'home/role/review-status.json'
        if receipt.exists():
            try:
                info=receipt.lstat();status=json.loads(receipt.read_text())
                if info.st_uid==config['roles'][row['role']]['uid'] and not receipt.is_symlink() and status.get('key')==key and status.get('generation')==row['generation'] and status.get('state') in STATES:
                    row.update(state=status['state'],stage=str(status.get('stage',''))[:100],reason=str(status.get('reason',''))[:2000],updated_at=time.time())
            except (OSError,ValueError):pass
        if row['state'] in ('waiting_author','waiting_platform','completed') and row.get('issue'):
            issue=api.call('GET','/issues/'+str(row['issue']))
            if issue['state']=='open':api.call('PATCH','/issues/'+str(row['issue']),{'state':'closed'})
        if row['state'] in ('waiting_author','waiting_platform') and event!=row['event']:
            if not any(v['state']=='reviewing' and v['role']==row['role'] for k,v in ledger.items() if k!=key):
                row.update(state='reviewing',event=event,generation=row['generation']+1,issue=None)
        if row['state']!='reviewing':continue
        marker=MARK+' '+key+' generation='+str(row['generation'])
        if not row.get('issue'):
            existing=[i for i in api.pages('/issues?state=all&type=issues') if marker in (i.get('body') or '')]
            if len(existing)>1:raise ValueError('Duplicate review issue')
            if existing:issue=existing[0]
            else:
                body=marker+chr(10)+json.dumps(row,ensure_ascii=False,indent=2)+chr(10)+'''Only this evaluator owns this exact version. Resume saved stages; do not re-review unchanged evidence. Start with completeness, report defects on the PR, then use role-review-status to enter waiting_author/waiting_platform/completed and exit. Never infer another task from recent branches. Five solver rollouts are subtasks of this review, not five evaluator assignments. Do not claim acceptance without evidence. No automatic failover while solver cleanup is unknown.'''
                issue=api.call('POST','/issues',{'title':'[独占评测] PR #'+str(row['pr'])+' '+row['commit'][:8],'body':body,'assignees':['gewu-'+row['role']]})
            row['issue']=issue['number']
        assignment=root/'home/role/review-assignment.json';atomic(assignment,dict(row,key=key));os.chown(assignment,config['roles'][row['role']]['uid'],config['roles'][row['role']]['gid'])
    atomic(STATE/'ledger.json',ledger)

def main():
    from controller_credentials import load_controller_credentials
    p=argparse.ArgumentParser();p.add_argument('--once',action='store_true');a=p.parse_args()
    STATE.mkdir(mode=0o700,exist_ok=True)
    with (STATE/'dispatcher.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        api=Api(load_controller_credentials()['forgejo_admin_token']);config=json.loads((W/'.state/science-role-broker/config.json').read_text())
        while True:
            ledger=json.loads((STATE/'ledger.json').read_text()) if (STATE/'ledger.json').exists() else {}
            try:reconcile(api,config,ledger)
            except Exception as e:print(type(e).__name__+': '+str(e),flush=True)
            if a.once:break
            time.sleep(60)
if __name__=='__main__':main()
