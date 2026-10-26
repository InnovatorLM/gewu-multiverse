"""Build a fresh standard Harbor RESEARCH/DRAFT package; never registers/runs it."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from prototype import build

WORKSPACE=Path('/mnt/data/zhanglinfeng/workspace')
SOURCE=Path(__file__).resolve().parent
BASE='public.ecr.aws/docker/library/python@sha256:b7a9e5f6a93d6d4a31f129bbd4bdee69efccb6ded0fb230d78aafaf37af98377'
INSTRUCTION=r'''# Finite-band impedance inference — research draft

This is a synthetic research exercise, not real instrument data or an accepted
benchmark. Solve every case in `/app/data/cases.json` and write a JSON object
mapping its case IDs to reports in `/app/report.json`. Use the public data only.
Python's standard library is available; public networking is allowed.

The family is Z(w)=Rs+sum_k Rk/(1+i*w*tauk). Angular frequency w is in rad/s,
impedance in ohm and tau in seconds. Real and imaginary predictions for each
branch are R/(1+(w*tau)^2) and -R*w*tau/(1+(w*tau)^2). Rs adds only to real.
Parameter boxes are inclusive, branch resistances/tau positive, Rs nonnegative.
All boxes, observation centers, componentwise absolute error bounds, and future
measurement options/costs are in each case. These costs are synthetic acquisition
units, with no asserted physical instrument calibration. Observation intervals
are closed, deterministic bounds; do not infer Gaussian confidence or posterior
probability. A feasible witness fits BOTH components of EVERY observation and
all parameter boxes. Recovering the generator's parameters is not required.

Numeric report fields must be JSON integers (not booleans) or exact decimal /
rational STRINGS. For example `"0.001"`, `"1e-3"` or `"1/1000"`. Scientific
notation is exact; whitespace/underscore separators are not allowed. JSON floating numbers,
NaN and infinity are refused. Rational strings must have a positive denominator.
Represent indices as JSON integers. D vectors must be exact rational values
(strings like `"3/2"`), not approximate/truncated floating displays. Each report:

* `two_branch`: `{"rs":"...","branches":[{"r":"...","tau":"..."}, ...]}`
  with exactly two branches and STRICTLY DISTINCT tau. Branch permutations
  are accepted. Equal-tau branches reduce exactly to one and do not count.
* `single_branch_status`: `"feasible"` or `"excluded"`.
* For `"feasible"`, supply `one_branch` in the same format with exactly one
  branch, and `interpretation: "finite_band_ambiguity_for_submitted_witnesses"`.
  Both witnesses must fit all data. This establishes alternatives within the
  declared family, not unique mechanisms or complete feasible parameter regions.
* For `"excluded"`, supply `certificate: [i,j,k]`, strictly increasing zero-based
  observation indices. The exact interval proof below must exclude every positive
  single branch. Exclusion is NOT proof of exactly two physical mechanisms.

For a feasible report compute a D for EVERY future measurement option, in list
order, using your two submitted witnesses a (one branch) and b (two branches):
D=max(abs(ReZa-ReZb)/(2*error_real), abs(ImZa-ImZb)/(2*error_imag)). Return
`d_vector` and `next_measurement`. Their bounded-error prediction rectangles
are strictly disjoint iff D>1; D=1 means touching and is not separation. Choose
the lowest-cost strictly separating option, breaking cost ties by lowest index.
If every D<=1, `next_measurement` is `"not_resolvable"` ONLY in conditional mode.
An index is an integer, not a string/float/bool.

The public `measurement_goal` is either `"conditional_pair"` (also the default
if absent) or `"separating_witness_pair"`. Conditional mode allows ANY feasible
pair, including a near-merged pair with `not_resolvable`. Separating mode
EXPLICITLY asks you to construct a feasible pair with at least one D>1; a
nonseparating pair is not a solution to this objective. At least one such pair
exists in each supplied separating case. This is a conditional contrast
construction, not globally optimal experimental design or discrimination of
entire feasible model families. An excluded report does not need a one-branch
witness or measurement design, irrespective of the goal field.

## Accepted exclusion certificate

For selected frequencies w1<w2<w3, define q bounds from imaginary observation y
and its absolute error e: qL=(-y-e)/w and qU=(-y+e)/w. A single positive branch
would have q=A/(1+w*w*x), where A=R*tau>0 and x=tau^2>0. Let
N=[q1L-q2U,q1U-q2L] and
B=[w2^2*q2L-w1^2*q1U,w2^2*q2U-w1^2*q1L].
This certificate requires q1L>0, NL>0 and BL>0. Then
xL=NL/BU, xU=NU/BL;
AL=q1L*(1+w1^2*xL), AU=q1U*(1+w1^2*xU).
The predicted third q lies in
[AL/(1+w3^2*xU), AU/(1+w3^2*xL)].
It must be STRICTLY disjoint from observed [q3L,q3U]. Otherwise the certificate
is inconclusive and rejected. Choose a different triple or supply a feasible
one-branch witness; overlap does not establish existence. At least one valid
triple exists for any supplied case without a feasible single-branch model.
This conservative proof uses imaginary components only; witness fitting still
checks both components. All proof arithmetic and grading are exact rational.

The task accepts alternate feasible parameters and algorithms. Do not claim
unmeasured scientific difficulty, physical uniqueness or probabilistic coverage.
All cases must pass for reward1. Resource target:2CPU/4GiB; timeout300seconds.
'''
GRADE=r'''"""Grade using authoritative public data in tests, never solver-editable data."""
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
'''
SOLVE='''import json\nimport sys\nfrom pathlib import Path\nfrom reference_fit import solve\ncases=json.loads(Path(sys.argv[1]).read_text())\nreports={key:solve(case)[0] for key,case in cases.items()}\nPath(sys.argv[2]).write_text(json.dumps(reports,indent=2)+'\\n')\n'''
TEST_SH='''#!/bin/bash
set -euo pipefail
mkdir -p /logs/verifier
printf '0\\n' > /logs/verifier/reward.txt
python3 /tests/grade.py
printf '1\\n' > /logs/verifier/reward.txt
'''
SOLVE_SH='''#!/bin/bash
set -euo pipefail
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
python3 "$script_dir/solve.py" /app/data/cases.json /app/report.json
'''


def package(output):
    output=Path(output)
    if output.exists() or not output.resolve().is_relative_to(WORKSPACE):
        raise ValueError('fresh workspace-local output required')
    cases={f'spectrum-{index+1}':case for index,case in enumerate(build()['cases'].values())}
    raw=json.dumps(cases,indent=2)+'\n'
    try:
        for name in ('environment/data','tests','solution','authoring'):(output/name).mkdir(parents=True)
        (output/'instruction.md').write_text(INSTRUCTION)
        (output/'task.toml').write_text('''version = "1.0"
[metadata]
author_name = "Terminal-Bench-Science universe research"
difficulty = "unknown"
category = "physical-sciences"
tags = ["research-draft", "synthetic", "impedance", "inverse-problem"]
[agent]
timeout_sec = 300.0
[verifier]
timeout_sec = 60.0
[environment]
build_timeout_sec = 300.0
cpus = 2
memory_mb = 4096
storage_mb = 30720
''')
        (output/'environment/Dockerfile').write_text(f'FROM {BASE}\nWORKDIR /app\nCOPY data/ /app/data/\n')
        (output/'environment/data/cases.json').write_text(raw)
        (output/'tests/public-cases.json').write_text(raw)
        (output/'tests/grade.py').write_text(GRADE)
        (output/'tests/test.sh').write_text(TEST_SH)
        (output/'solution/solve.sh').write_text(SOLVE_SH)
        (output/'solution/solve.py').write_text(SOLVE)
        for destination in ('tests','solution'):shutil.copyfile(SOURCE/'prototype_checker.py',output/destination/'prototype_checker.py')
        shutil.copyfile(SOURCE/'reference_fit.py',output/'solution/reference_fit.py')
        repo=SOURCE.parent.parent
        commit=subprocess.run(['git','rev-parse','HEAD'],cwd=repo,check=True,capture_output=True,text=True).stdout.strip()
        provenance={'status':'research/draft','registration_enabled':False,'scientific_acceptance':False,'difficulty_measured':False,
          'model_calls':0,'acs_launched':False,'data_origin':'original deterministic synthetic Debye spectra; no external data/code copied',
          'observation_generation':'exact rational forward model then formatted to9decimal places via float conversion; exact witness slack independently tested',
          'data_scope':'bounded deterministic component errors; synthetic acquisition costs; no physical instrument accuracy or statistical confidence claim',
          'public_data_sha256':hashlib.sha256(raw.encode()).hexdigest(),'research_repository_commit':commit,
          'research_source_sha256':{name:hashlib.sha256((SOURCE/name).read_bytes()).hexdigest() for name in ('package_draft.py','prototype.py','feasibility.py','prototype_checker.py','reference_fit.py')},
          'code_license':'repository MIT OR Apache-2.0; see repository LICENSE-MIT and LICENSE-APACHE',
          'literature_scope':'see repository EIS literature/source receipts; structural-identifiability literature does not validate real physical mechanisms for these synthetic data',
          'reference_algorithm':'public-data-only variable projection and local log-grid refinement, then exact verification; no global-optimum claim',
          'environment_payload_allowlist':['Dockerfile','data/cases.json'],
          'runtime_verified':False,'oracle_container_verified':False,'mechanical_checks_pending':True}
        provenance['package_files_sha256']={str(p.relative_to(output)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(output.rglob('*')) if p.is_file()}
        (output/'authoring/provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
        (output/'authoring/STATUS.md').write_text('Research/draft only. Disabled for registration. No scientific acceptance, model difficulty, actual Harbor runtime or ACS evidence. See provenance.json.\n')
    except BaseException:
        if output.exists():shutil.rmtree(output)
        raise
    return output


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    print(package(args.output))
