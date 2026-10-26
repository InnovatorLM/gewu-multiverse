#!/usr/bin/env python3
"""Read-only current-source evidence audit; never turns evidence presence into acceptance."""
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
from evaluation_queue import W,root_file,validated_template,evaluation_catalog
from build_task_images import validate_build_receipt
from role_exec import role_processes


def catalog_status(registry, published):
    expected=evaluation_catalog(registry)
    entries=published.get('evaluations')
    if not isinstance(entries,list):
        raise ValueError('Published catalog lacks evaluation list')
    identifiers=[item['evaluation_id'] for item in entries]
    if len(identifiers)!=len(set(identifiers)):
        raise ValueError('Published catalog has duplicate evaluation IDs')
    return {'published_matches_current_registry':published==expected,
            'visible_evaluation_ids':set(identifiers)}


def phase_requirements():
    return {
        'author_proposal': {
            'readiness': 'requires_current_preflight',
            'qualified_first_task_required': False,
            'required_checks': [
                'Current dedicated-role processes and persisted role-session allowance.',
                'Current ACS resource inventory and previous run cleanup.',
                'Broker/controller, designated provider and credential boundaries.',
                'Explicit proposal-only initial scope; no unreviewed implementation or difficulty trial.'
            ],
            'note': 'Solver dispatch allowance is separate from author role-session allowance.'
        },
        'first_task_admission': {'readiness': 'not_proven_complete',
                                 'qualified_first_task_required': True}
    }


def audit():
    queue=json.loads(root_file(W/'.config/science-evaluation/queue.json').read_text())
    registry=json.loads(root_file(queue['registry']).read_text())
    catalog_path=Path(queue['inbox']).parent/'catalog.json'
    published=json.loads(root_file(catalog_path).read_text())
    catalog=catalog_status(registry,published)
    visible=catalog.pop('visible_evaluation_ids')
    day=datetime.now(timezone.utc).date().isoformat()
    claims=[]
    for path in sorted(Path(queue['state']).glob('*/claim.json')):
        claim=json.loads(root_file(path).read_text())
        result_path=path.parent/'result.json'
        result=json.loads(root_file(result_path).read_text()) if result_path.exists() else {}
        claims.append({'job_id':claim['job_id'],'day':claim['day'],
                       'cleanup_confirmed':result.get('cleanup_confirmed') is True})
    count=sum(c['day']==day for c in claims)
    evidence={'published_catalog':catalog,'day_utc':day,'dispatch_budget':{'configured':queue['max_jobs_per_day'],'claimed_today':count,'remaining':max(0,queue['max_jobs_per_day']-count)},
              'prior_dispatch_cleanup_confirmed':all(c['cleanup_confirmed'] for c in claims),
              'dedicated_uid_live_process_counts':{str(uid):len(role_processes(uid)) for uid in (21001,21002,21003,21012)},'candidate_routes':{}}
    for identifier in ('eis-research-v1','eis-research-v1-quality','eis-research-v1-semantic'):
        entry=registry[identifier]
        template=validated_template(entry,{'snapshot_sha256':entry['snapshot_sha256']})
        receipt=json.loads(root_file(Path(entry['snapshot']).parent/'build-receipt.json').read_text())
        validate_build_receipt(receipt,entry['snapshot'],entry['source_commit'],entry['source_task_path'],template)
        evidence['candidate_routes'][identifier]={'source_commit':entry['source_commit'],'snapshot_sha256':entry['snapshot_sha256'],'source_receipt_verified':True,'enabled':entry.get('enabled',True),'catalog_visible':identifier in visible,'private_retention_requested':template['agents'][0]['kwargs'].get('retain_private_trajectory',False)}
    evidence['image_smokes']={}
    for role in ('runtime','verifier'):
        r=json.loads(root_file(W/f'.state/eis-image-publication-v1/acs-{role}-smoke.json').read_text())
        entry=registry['eis-research-v1']
        receipt=json.loads(root_file(Path(entry['snapshot']).parent/'build-receipt.json').read_text())
        passed=(r.get('snapshot_sha256')==entry['snapshot_sha256'] and r.get('image')==receipt['images'][role]['published_digest'] and
                r.get('expected_image_config_id')==receipt['images'][role]['image_config_id'] and r.get('image_config_linkage_verified') is True and
                r.get('public_data_and_boundary_verified') is True and r.get('exit_code')==0 and r.get('node_region')=='cn-beijing' and r.get('cleanup',{}).get('confirmed') is True)
        evidence['image_smokes'][role]={'record_matches_current_registration':passed,'run_id':r.get('run_id'),'scope':'retained execution evidence; not a new cluster query'}
    # Missing actual acceptance artifacts are explicit. Static checks must never
    # fabricate scientific truth, empirical difficulty or human approvals.
    remaining=[
        'Exact-candidate full Harbor solver/verifier lifecycle and cleanup evidence.',
        'Live private science trajectory retention, exact execution binding and native review input.',
        'Live role-queue semantic comparison for the current candidate against both fixed benchmark corpora.',
        'Independent factual/scientific adjudication of current candidate quality and scientific suitability.',
        'Actual task/trajectory direct and WinRate evaluation views required by the original plan.',
        'Designated-model difficulty trials with infra errors separated and token/tool metrics.',
        'Concrete sanitized acceptance receipt, evaluator approval and first-pilot user approval before curator admission.',
        'Final admission configuration, resource and process audit before first task admission.'
    ]
    return {'checked_at_utc':datetime.now(timezone.utc).isoformat(),'read_only':True,'current_evidence':evidence,
            'requirements_not_proven_complete':remaining,'launch_ready':False,'scientific_acceptance':False,
            'launch_ready_scope':'Legacy field denotes first-task admission, not author proposal startup.',
            'phases':phase_requirements(),
            'scope':'Local source/receipt/retained-run linkage and current process/budget inspection. No new API, ACS, model or approval call.'}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists() or not args.output.resolve().is_relative_to(W):raise ValueError('fresh workspace output required')
    result=audit()
    from evaluation_queue import atomic_json
    atomic_json(args.output,result)
    print(json.dumps({'launch_ready':False,'remaining_requirements':len(result['requirements_not_proven_complete']),'dispatch_budget':result['current_evidence']['dispatch_budget'],'dedicated_uid_live_process_counts':result['current_evidence']['dedicated_uid_live_process_counts']}))
