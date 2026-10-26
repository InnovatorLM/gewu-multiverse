"""Reproduce public-only fitting and exact serialized-witness validation, offline."""
import hashlib
import json
from pathlib import Path
from prototype_checker import impedance, number
from reference_fit import solve


def study(public_cases):
    results={}
    for name,case in public_cases.items():
        report,metrics=solve(case)
        slacks=[]
        for witness,count in [(report['two_branch'],2)]+([(report['one_branch'],1)] if report['single_branch_status']=='feasible' else []):
            for row in case['observations']:
                prediction=impedance(number(row['omega']),witness,case['boxes'],count)
                slacks.extend(number(row['error_'+k])-abs(value-number(row[k])) for k,value in zip(('real','imag'),prediction))
        results[name]={'report':report,'metrics':metrics,'minimum_exact_feasibility_slack_ohm':str(min(slacks))}
    directory=Path(__file__).parent
    return {'kind':'offline public-data numerical reference study','results':results,
            'public_cases_sha256':hashlib.sha256(json.dumps(public_cases,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
            'source_sha256':{name:hashlib.sha256((directory/name).read_bytes()).hexdigest() for name in ('prototype_checker.py','reference_fit.py','run_reference_study.py')},
            'timing_scope':'local host, not a measured 2CPU/4Gi ACS allocation',
            'global_optimizer_guarantee':False,'scientific_acceptance':False,'difficulty_measured':False,'model_calls':0}


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('public_cases',type=Path,help='JSON with only the public case mapping')
    args=parser.parse_args()
    print(json.dumps(study(json.loads(args.public_cases.read_text())),indent=2))
