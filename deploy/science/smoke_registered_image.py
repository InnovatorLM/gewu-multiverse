#!/usr/bin/env python3
"""Operator-only ACS image smoke: no model, no Harbor trial, scoped cleanup."""
import argparse
import base64
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import time
import uuid

from evaluation_queue import W, atomic_json, root_file, validated_template
from build_task_images import validate_build_receipt


def smoke(evaluation_id, output, image_role='runtime'):
    if os.geteuid()!=0 or image_role not in ('runtime','verifier'):
        raise ValueError('Operator and supported image role required')
    output=Path(output)
    if output.exists() or not output.resolve().is_relative_to(W):
        raise ValueError('Require fresh workspace-local report')
    output.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
    registry=json.loads(root_file(W/'.config/science-evaluation/registry.json').read_text())
    entry=registry[evaluation_id]
    template=validated_template(entry,{'snapshot_sha256':entry['snapshot_sha256']})
    receipt=json.loads(root_file(Path(entry['snapshot']).parent/'build-receipt.json').read_text())
    validate_build_receipt(receipt,entry['snapshot'],entry['source_commit'],entry['source_task_path'],template)
    public=Path(entry['snapshot'])/'environment/data/cases.json'
    expected_data=hashlib.sha256(root_file(public).read_bytes()).hexdigest()
    kwargs=template['environment']['kwargs'];image=receipt['images'][image_role]['published_digest']
    expected_config=receipt['images'][image_role]['image_config_id']
    spec=importlib.util.spec_from_file_location('acs_image_guard',W/'.agents/skills/acs-harbor-eval/scripts/run_guard.py')
    guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard)
    cluster=guard.Cluster(kwargs['kubeconfig'],kwargs.get('namespace','default'))
    run='eis-image-'+uuid.uuid4().hex[:16]
    report={'run_id':run,'mode':'registered-image-smoke','evaluation_id':evaluation_id,
        'snapshot_sha256':entry['snapshot_sha256'],'source_commit':entry['source_commit'],
        'image_role':image_role,'image':image,'expected_image_config_id':expected_config,
        'expected_public_data_sha256':expected_data,'model_calls':0,'provider_credentials_loaded':False,
        'harbor_trial_executed':False,'scientific_acceptance':False,'cleanup':{'confirmed':False}}
    known={}
    def save():atomic_json(output,report)
    def interrupted(*_):raise InterruptedError('Smoke interrupted')
    previous={s:signal.signal(s,interrupted) for s in (signal.SIGINT,signal.SIGTERM)}
    save()
    try:
        nodes=cluster.call('/api/v1/nodes')['items']
        if {n['metadata'].get('labels',{}).get('topology.kubernetes.io/region') for n in nodes}!={'cn-beijing'}:
            raise ValueError('Unexpected cluster region')
        secret=cluster.call(cluster.path('pods').rsplit('/pods',1)[0]+'/secrets/'+kwargs['image_pull_secret'])
        auths=json.loads(base64.b64decode(secret['data']['.dockerconfigjson']))['auths']
        if secret['type']!='kubernetes.io/dockerconfigjson' or image.split('/',1)[0] not in auths:
            raise ValueError('Configured pull Secret does not cover registry')
        versions=receipt['harness_versions'] if image_role=='runtime' else {}
        code=("import hashlib,importlib.metadata as m,os; from pathlib import Path; "
              "assert hashlib.sha256(Path('/app/data/cases.json').read_bytes()).hexdigest()=="+repr(expected_data)+"; "
              "assert not any(Path(p).exists() for p in ('/tests','/solution','/oracle','/var/run/secrets/kubernetes.io/serviceaccount/token')); "
              "assert 'OPENAI_API_KEY' not in os.environ and 'LLM_PROVIDER' not in os.environ; "
              "expected="+repr(versions)+"; assert all(m.version(k)==v for k,v in expected.items()); ")
        if image_role=='runtime':code+='from minisweagent.models.litellm_model import LitellmModel; '
        code+="print('public-data-boundary-and-dependencies-ok')"
        resources={'requests':{'cpu':'2','memory':'4Gi','ephemeral-storage':'30Gi'},'limits':{'cpu':'2','memory':'4Gi','ephemeral-storage':'30Gi'}}
        body={'apiVersion':'v1','kind':'Pod','metadata':{'name':run,'labels':{'evaluation-run':run,'alibabacloud.com/acs':'true'}},
          'spec':{'automountServiceAccountToken':False,'restartPolicy':'Never','activeDeadlineSeconds':360,
          'imagePullSecrets':[{'name':kwargs['image_pull_secret']}],
          'containers':[{'name':'main','image':image,'command':['python3','-c',code],'resources':resources}]}}
        pod=cluster.call(cluster.path('pods'),'POST',body=body)
        known[('pods',run)]=pod['metadata']['uid'];report['known_resource']={'name':run,'uid':pod['metadata']['uid']};save()
        deadline=time.monotonic()+420
        while time.monotonic()<deadline:
            pod=cluster.call(cluster.path('pods')+'/'+run);report['phase']=pod.get('status',{}).get('phase');save()
            if report['phase'] in ('Succeeded','Failed'):
                status=pod['status'].get('containerStatuses',[])
                if len(status)!=1:raise ValueError('Unexpected container status')
                status=status[0];exit_code=status.get('state',{}).get('terminated',{}).get('exitCode')
                report.update(exit_code=exit_code,image_id=status.get('imageID'),resources=pod['spec']['containers'][0]['resources'],node=pod['spec'].get('nodeName'))
                actual_config=(status.get('imageID') or '').split('://')[-1]
                if report['phase']!='Succeeded' or exit_code!=0 or actual_config!=expected_config or report['resources']!=resources:
                    raise ValueError('Runtime/image/resource verification failed')
                node=cluster.call('/api/v1/nodes/'+report['node']);report['node_region']=node['metadata']['labels'].get('topology.kubernetes.io/region')
                if report['node_region']!='cn-beijing':raise ValueError('Actual node region differs')
                report.update(public_data_and_boundary_verified=True,pinned_dependencies_verified=image_role=='runtime',image_config_linkage_verified=True)
                break
            time.sleep(3)
        else:raise TimeoutError('Image smoke timed out')
    except Exception as error:
        report['error_type']=type(error).__name__
    finally:
        try:report['cleanup']=guard.release(cluster,run,known)
        except Exception as error:report['cleanup_error_type']=type(error).__name__
        save()
        for signum,handler in previous.items():signal.signal(signum,handler)
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evaluation-id',required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--image-role',choices=('runtime','verifier'),default='runtime')
    args=parser.parse_args()
    result=smoke(args.evaluation_id,args.output,args.image_role)
    print(json.dumps({key:result.get(key) for key in ('run_id','phase','exit_code','public_data_and_boundary_verified','image_config_linkage_verified','error_type','cleanup')}))
    raise SystemExit(0 if result.get('public_data_and_boundary_verified') and result['cleanup']['confirmed'] else 1)
