"""Retained seeded exact controls for single-branch certificate false exclusion.

Uses a third direct component construction, not the generator or checker's
forward evaluator. This is finite testing, not a proof of universal soundness.
"""
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import random
from prototype_checker import excludes


def controls(seed=12917, count=4000):
    rng=random.Random(seed)
    transcript=hashlib.sha256()
    inconclusive=0
    for index in range(count):
        r=F(rng.randint(1,100000),100)
        tau=F(rng.randint(1,100000),10**rng.randint(3,8))
        omega=sorted({F(rng.randint(1,100000),10**rng.randint(0,3)) for _ in range(5)})[:3]
        if len(omega)!=3:raise AssertionError('seed produced frequency collision')
        observations=[]
        for w in omega:
            # Im[ R/(1+iw*tau) ] computed directly using u=w*tau.
            u=w*tau;true_imaginary=-r*u/(1+u*u)
            error=F(rng.randint(1,10000),10**rng.randint(2,8))
            # Includes exact endpoints as well as interior nonuniform errors.
            perturbation=error*F(rng.choice([-100,-99,-50,-1,0,1,50,99,100]),100)
            row={'omega':str(w),'imag':str(true_imaginary+perturbation),'error_imag':str(error)}
            assert abs(true_imaginary-F(row['imag']))<=F(row['error_imag'])
            observations.append(row)
        case={'observations':observations}
        verdict=excludes(case,[0,1,2])
        if verdict:raise AssertionError(f'False exclusion at seed={seed}, case={index}: {case}')
        inconclusive+=1
        transcript.update(json.dumps({'r':str(r),'tau':str(tau),'case':case,'excluded':verdict},sort_keys=True,separators=(',',':')).encode()+b'\n')
    return {'seed':seed,'cases':count,'known_feasible_single_branches':count,'false_exclusions':0,
            'inconclusive_certificates':inconclusive,'generated_control_transcript_sha256':transcript.hexdigest(),
            'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'checker_sha256':hashlib.sha256(Path(__file__).with_name('prototype_checker.py').read_bytes()).hexdigest(),
            'scope':'Exact seeded feasible-single-branch controls with heterogeneous bounded imaginary errors; not a mathematical proof, calibration or scientific acceptance.',
            'model_calls':0,'scientific_acceptance':False}


if __name__=='__main__':print(json.dumps(controls(),indent=2))
