#!/usr/bin/env python3
"""Find and optionally terminate stale ACS resources owned by this universe."""
import argparse, json, time
from pathlib import Path
from kubernetes import client, config
from kubernetes.client.exceptions import ApiException

PREFIX='tbs-universe-linfeng-'
KINDS=('pods','jobs','sandboxsets','sandboxclaims','sandboxes')
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--kubeconfig',required=True); ap.add_argument('--namespace',default='default'); ap.add_argument('--max-age-hours',type=float,default=5); ap.add_argument('--kill',action='store_true'); ap.add_argument('--out',required=True); a=ap.parse_args()
    config.load_kube_config(config_file=a.kubeconfig); api=client.ApiClient(); now=time.time(); found=[]
    paths={'pods':'/api/v1','jobs':'/apis/batch/v1','sandboxsets':'/apis/agents.kruise.io/v1alpha1','sandboxclaims':'/apis/agents.kruise.io/v1alpha1','sandboxes':'/apis/agents.kruise.io/v1alpha1'}
    for kind in KINDS:
      try:
        method,url,h,b,post=api.param_serialize('GET',paths[kind]+'/namespaces/'+a.namespace+'/'+kind,query_params=[('labelSelector','evaluation-run')],body=None,auth_settings=['BearerToken'])
        resp=api.call_api(method,url,header_params=h,body=b,post_params=post,_request_timeout=(10,25)); resp.read(); data=json.loads(resp.data.decode())
      except ApiException as e:
        if e.status==404: continue
        raise
      for item in data.get('items',[]):
        labels=(item.get('metadata') or {}).get('labels') or {}; run=labels.get('evaluation-run',''); ts=(item.get('metadata') or {}).get('creationTimestamp')
        if not run.startswith(PREFIX) or not ts: continue
        age=now-time.mktime(time.strptime(ts[:19],'%Y-%m-%dT%H:%M:%S'))
        if age> a.max_age_hours*3600: found.append({'kind':kind,'name':item['metadata']['name'],'age_seconds':int(age),'run_id':run})
    killed=[]
    if a.kill:
      for x in found:
        path=paths[x['kind']]+f"/namespaces/{a.namespace}/{x['kind']}/{x['name']}"
        method,url,h,b,post=api.param_serialize('DELETE',path,query_params=[],body=None,auth_settings=['BearerToken']); api.call_api(method,url,header_params=h,body=b,post_params=post,_request_timeout=(10,25)); killed.append(x)
    out={'prefix':PREFIX,'max_age_hours':a.max_age_hours,'stale':found,'killed':killed,'alert':bool(found)}; Path(a.out).write_text(json.dumps(out,indent=2)); print(json.dumps(out))
if __name__=='__main__': main()
