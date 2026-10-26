"""Grade using authoritative public data in tests, never solver-editable data."""
import argparse
import json
from pathlib import Path
from prototype_checker import check


def validate_report(cases, reports):
    if type(reports) is not dict or set(reports)!=set(cases):
        raise ValueError('exact case coverage required')
    for key,case in cases.items():
        check(case,reports[key])
    return True


def unique_pairs(pairs):
    result={}
    for key,value in pairs:
        if key in result: raise ValueError('duplicate JSON key')
        result[key]=value
    return result


def load_report(path):
    raw=Path(path).read_bytes()
    if len(raw)>262144: raise ValueError('report too large')
    return json.loads(raw,object_pairs_hook=unique_pairs)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--report',type=Path,default=Path('/app/report.json'))
    args=parser.parse_args()
    cases=json.loads((Path(__file__).parent/'public-cases.json').read_text())
    validate_report(cases,load_report(args.report))
    print('All exact scientific-interface checks passed (research draft).')
