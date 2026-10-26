"""Synthetic research fixtures with known witnesses, NOT a numerical fitting solution."""
import json
from itertools import combinations
from fractions import Fraction as F
from feasibility import response
from prototype_checker import check, excludes, measurement


def witness(branches, rs='5'):
    return {'rs':rs,'branches':[{'r':str(r),'tau':str(t)} for r,t in branches]}


def build():
    cases, reports = {}, {}
    for name, branches in [('ambiguous',[(80,F(1,1000)),(120,F(1,100))]),
                           ('excluded',[(80,F(1,1000)),(120,F(1,10))])]:
        frequencies = [F(1,100),F(3,100),F(1,10),F(3,10),F(1)] if name == 'ambiguous' else [1,3,10,30,100,300,1000,3000,10000]
        case = {'measurement_goal':'separating_witness_pair' if name=='ambiguous' else 'conditional_pair','units':{'omega':'rad/s','impedance':'ohm','tau':'s'},
                'boxes':{'rs':['0','20'],'r':['1','300'],'tau':['0.00001','1']},
                'observations':[], 'measurement_options':[]}
        for w in frequencies:
            re,im = response(w,5,branches)
            # Rounded centers leave substantial slack relative to 0.01 ohm.
            case['observations'].append({'omega':str(w),'real':format(float(re),'.9f'),
                'imag':format(float(im),'.9f'),'error_real':'0.01','error_imag':'0.01'})
        for w,precision,cost in [(1,'0.01','1'),(100,'0.01','5'),(1000,'0.01','5')]:
            case['measurement_options'].append({'omega':str(w),'error_real':precision,
                'error_imag':precision,'cost':cost,'cost_unit':'synthetic acquisition units'})
        report = {'two_branch':witness(branches),'single_branch_status':name if name=='excluded' else 'feasible'}
        if name == 'excluded':
            report['certificate'] = next(list(c) for c in combinations(range(len(frequencies)),3) if excludes(case,list(c)))
        else:
            report['one_branch'] = witness([(200,F(64,10000))])
            report['interpretation'] = 'finite_band_ambiguity_for_submitted_witnesses'
            d,choice = measurement(case,report['one_branch'],report['two_branch'])
            report.update(d_vector=list(map(str,d)),next_measurement=choice)
        check(case,report)
        cases[name],reports[name] = case,report
    return {'kind':'synthetic research prototype','scientific_acceptance':False,
            'difficulty_measured':False,'model_calls':0,'cases':cases,'known_witness_reports':reports}


if __name__ == '__main__':
    print(json.dumps(build(),indent=2))
