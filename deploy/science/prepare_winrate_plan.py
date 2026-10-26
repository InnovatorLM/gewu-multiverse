#!/usr/bin/env python3
"""Freeze full benchmark packages and prepare a private, no-model WinRate plan."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from evaluation_queue import W, atomic_json, digest_tree, root_file, validated_template
from register_evaluation import freeze
from semantic_comparison import load_corpus

UE = W / 'repos/unified-evaluator-pipeline'


def verify_package_inputs(manifest):
    registry = json.loads(root_file(W/'.config/science-evaluation/registry.json').read_text())
    entry = registry[manifest['evaluation_id']]
    validated_template(entry, {'snapshot_sha256': manifest['snapshot_sha256']})
    if entry['snapshot'] != manifest['candidate_path']:
        raise ValueError('Registered candidate identity changed')
    corpus=Path(manifest['corpus_path'])
    if hashlib.sha256(root_file(corpus/'manifest.json').read_bytes()).hexdigest()!=manifest['corpus_manifest_sha256']:
        raise ValueError('Comparison corpus manifest changed')
    rows,corpus_manifest=load_corpus(corpus)
    if corpus_manifest.get('selection_scope')!='active':
        raise ValueError('Comparison corpus is not active-task scope')
    for record in manifest['references']:
        index=record['corpus_reference_index']
        if type(index) is not int or not 0<=index<len(rows):
            raise ValueError('Reference index outside bound corpus')
        row=rows[index]
        if any(record[key]!=row[source] for key,source in [('dataset','dataset'),('source_commit','commit'),('instruction_sha256','sha256')]) or record['source_task_path']!=str(Path(row['path']).parent):
            raise ValueError('Reference source differs from bound corpus row')
        path = Path(record['snapshot_path'])
        if not path.resolve().is_relative_to(W) or digest_tree(path) != record['snapshot_sha256']:
            raise ValueError('Frozen full reference package changed')
        if hashlib.sha256((path/'instruction.md').read_bytes()).hexdigest() != record['instruction_sha256']:
            raise ValueError('Reference instruction/source mismatch')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evaluation-id', required=True)
    parser.add_argument('--corpus', type=Path, required=True)
    parser.add_argument('--reference-index', type=int, action='append', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output
    if os.geteuid() != 0 or output.exists() or not output.resolve().is_relative_to(W):
        raise ValueError('Require operator and a fresh private workspace output')
    rows, corpus_manifest = load_corpus(args.corpus)
    if corpus_manifest.get('selection_scope') != 'active':
        raise ValueError('Only active benchmark task sources may enter this plan')
    indices = args.reference_index
    if len(indices) != len(set(indices)) or any(i < 0 or i >= len(rows) for i in indices):
        raise ValueError('Require unique valid corpus indices')
    selected = [rows[i] for i in indices]
    if {r['dataset'] for r in selected} != {'terminal-bench-4.0', 'terminal-bench-science-v0.1'}:
        raise ValueError('Reference selection must include both benchmark sources')
    names = [Path(r['path']).parent.name for r in selected]
    if len(names) != len(set(names)):
        raise ValueError('Reference task-name collision; no silent renaming')
    registry = json.loads(root_file(W/'.config/science-evaluation/registry.json').read_text())
    entry = registry[args.evaluation_id]
    validated_template(entry, {'snapshot_sha256': entry['snapshot_sha256']})
    output.mkdir(mode=0o700)
    packages = output/'references';packages.mkdir(mode=0o700)
    records = []
    for index, row in zip(indices, selected):
        task_path = str(Path(row['path']).parent)
        target = packages/Path(task_path).name
        sha = freeze(W/'datasets'/row['dataset'], row['commit'], task_path, target)
        record = {'corpus_reference_index': index, 'dataset': row['dataset'], 'source_commit': row['commit'], 'source_task_path': task_path, 'instruction_sha256': row['sha256'], 'snapshot_path': str(target), 'snapshot_sha256': sha}
        if hashlib.sha256((target/'instruction.md').read_bytes()).hexdigest() != row['sha256']:
            raise ValueError('Full package differs from pinned instruction corpus')
        records.append(record)
    manifest = {'evaluation_id': args.evaluation_id, 'candidate_path': entry['snapshot'], 'snapshot_sha256': entry['snapshot_sha256'], 'corpus_path':str(args.corpus.resolve()), 'corpus_manifest_sha256': hashlib.sha256(root_file(args.corpus/'manifest.json').read_bytes()).hexdigest(), 'references': records, 'selection': 'explicit diagnostic subset; not a representative quality sample', 'scientific_acceptance': False, 'model_calls': 0, 'acs_launched': False}
    verify_package_inputs(manifest)
    atomic_json(output/'source-manifest.json', manifest)
    env = {'PATH': os.environ.get('PATH','/usr/bin:/bin'), 'HOME': str(W/'.state/harbor-home'), 'TMPDIR': str(W/'.tmp'), 'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONPATH': str(UE), 'UE_DATA_DIR': str(output/'pipeline-data'), 'UE_RUNTIME_DIR': str(output/'runtime')}
    command = [sys.executable, '-m', 'unified_evaluator.pipelines.winrater', '--candidate-root', entry['snapshot'], '--reference-root', str(packages), '--references-per-task', '0', '--workers', '1', '--seed', '0', '--output-dir', str(output/'plan'), '--dry-run']
    result = subprocess.run(command, env=env, capture_output=True, timeout=180)
    (output/'planning.log').write_bytes(result.stdout+b'\n'+result.stderr);(output/'planning.log').chmod(0o600)
    if result.returncode:
        raise ValueError('WinRate planning failed; inspect private planning.log')
    verify_package_inputs(manifest)
    plan = json.loads((output/'plan/plan.json').read_text())
    if len(plan['candidates']) != 1 or len(plan['references']) != len(records) or len(plan['pairs']) != len(records) or not plan['swap'] or plan['excluded_candidates'] or plan['excluded_references']:
        raise ValueError('WinRate plan omitted inputs or disabled swapped comparison')
    atomic_json(output/'validation.json', {'full_package_hashes_verified': True, 'references': len(records), 'planned_pairs': len(plan['pairs']), 'planned_model_calls': 2*len(plan['pairs']), 'actual_model_calls': 0, 'acs_launched': False, 'scientific_acceptance': False})
    print(json.dumps({'references': len(records), 'planned_pairs': len(plan['pairs']), 'planned_model_calls': 2*len(plan['pairs']), 'actual_model_calls': 0, 'scientific_acceptance': False}))


if __name__ == '__main__':
    main()
