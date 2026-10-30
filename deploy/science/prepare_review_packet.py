#!/usr/bin/env python3
"""Prepare an exact-version review inventory, not an acceptance receipt or signature.

No raw evidence, credentials, trajectories or model judgment text is copied.
The resulting packet lists missing gates; no operator-authored flag grants release.
"""
import argparse
import hashlib
import json
from pathlib import Path
from evaluation_queue import W, atomic_json, root_file, validated_template
from build_task_images import validate_build_receipt

GATES = ('scientific_suitability', 'source_provenance', 'oracle_leak_review',
         'independent_reference_and_negative_controls', 'harbor_lifecycle',
         'task_quality_direct',
         'task_quality_winrate', 'trajectory_direct', 'trajectory_winrate',
         'empirical_difficulty', 'resource_cleanup', 'evaluator_approval',
         'curator_admission')


def evidence_record(path):
    path=root_file(path)
    return {'workspace_relative_path':str(path.relative_to(W)),
            'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'bytes':path.stat().st_size,'content_included':False}


def prepare(evaluation_id):
    registry=json.loads(root_file(W/'.config/science-evaluation/registry.json').read_text())
    entry=registry[evaluation_id]
    if entry.get('dispatch','solver')!='solver':raise ValueError('Require base solver registration')
    template=validated_template(entry,{'snapshot_sha256':entry['snapshot_sha256']})
    parent=Path(entry['snapshot']).parent
    build=json.loads(root_file(parent/'build-receipt.json').read_text())
    validate_build_receipt(build,entry['snapshot'],entry['source_commit'],entry['source_task_path'],template)
    # Only known controller-side provenance records, not arbitrary caller files.
    evidence={name:evidence_record(parent/name) for name in ('provenance.json','mechanical-check.json','build-receipt.json')}
    return {'schema_version':1,'kind':'private_review_inventory',
            'evaluation_id':evaluation_id,'source_commit':entry['source_commit'],
            'source_task_path':entry['source_task_path'],'snapshot_sha256':entry['snapshot_sha256'],
            'registered_template_sha256':entry['template_sha256'],
            'registered_enabled':entry.get('enabled',True),
            'images':{role:build['images'][role]['published_digest'] for role in ('official','runtime','verifier')},
            'evidence_inventory':evidence,
            'gates':{name:{'status':'not_adjudicated','evidence':[]} for name in GATES},
            'scientific_acceptance':False,'release_eligible':False,'approval_authenticated':False,
            'raw_evidence_included':False,'safe_for_publication':False,
            'limitations':['Inventory integrity is not factual verification or approval.',
                           'Controller evidence paths are private; generate a separately reviewed shareable receipt before publication.',
                           'No gate is completed merely by preparing this packet.']}


def validate(packet):
    if packet.get('schema_version')!=1 or packet.get('kind')!='private_review_inventory':raise ValueError('Unsupported packet')
    if any(packet.get(key) is not False for key in ('scientific_acceptance','release_eligible','approval_authenticated','raw_evidence_included','safe_for_publication')):
        raise ValueError('Inventory cannot assert acceptance, approval or sharing safety')
    fresh=prepare(packet['evaluation_id'])
    for key in ('source_commit','source_task_path','snapshot_sha256','registered_template_sha256','registered_enabled','images','evidence_inventory'):
        if packet.get(key)!=fresh[key]:raise ValueError('Review inventory is stale: '+key)
    if packet.get('gates')!=fresh['gates']:raise ValueError('Inventory does not adjudicate scientific or approval gates')
    return True


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evaluation-id',required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists() or not args.output.resolve().is_relative_to(W):raise ValueError('Fresh private workspace output required')
    packet=prepare(args.evaluation_id);validate(packet);atomic_json(args.output,packet)
    print(json.dumps({'evaluation_id':args.evaluation_id,'inventory_valid':True,'unadjudicated_gates':len(GATES),'release_eligible':False}))
