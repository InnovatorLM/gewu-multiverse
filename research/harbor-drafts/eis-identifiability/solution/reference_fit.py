"""Public-data-only variable projection research fitter; no generator parameters.

Pure Python numerical least squares, log-grid starts and coordinate refinement.
Exact independent checking follows serialization; numerical fit never proves exclusion.
"""
import math
import time
from itertools import combinations
from prototype_checker import check, excludes, measurement, number


def linear_solve(matrix, rhs):
    a = [list(row)+[value] for row,value in zip(matrix,rhs)]
    n=len(rhs)
    for col in range(n):
        pivot=max(range(col,n),key=lambda r:abs(a[r][col]))
        if abs(a[pivot][col]) < 1e-15: return None
        a[col],a[pivot]=a[pivot],a[col]
        scale=a[col][col]
        a[col]=[v/scale for v in a[col]]
        for r in range(n):
            if r!=col:
                scale=a[r][col]
                a[r]=[x-scale*y for x,y in zip(a[r],a[col])]
    return [row[-1] for row in a]


def fit(case, count):
    observations=case['observations'];boxes=case['boxes']
    bounds={key:tuple(float(number(x)) for x in val) for key,val in boxes.items()}
    data=[(float(number(row['omega'])), float(number(row['real'])),float(number(row['imag']))) for row in observations]
    evaluations=0
    def project(logs):
        nonlocal evaluations
        evaluations+=1
        tau=[10**v for v in logs]
        if any(not bounds['tau'][0]<=t<=bounds['tau'][1] for t in tau):return (math.inf,None)
        rows=[];y=[]
        for w,re,im in data:
            rows.extend([[1]+[1/(1+(w*t)**2) for t in tau],
                         [0]+[-w*t/(1+(w*t)**2) for t in tau]])
            y.extend([re,im])
        n=count+1
        normal=[[sum(row[i]*row[j] for row in rows) for j in range(n)] for i in range(n)]
        rhs=[sum(row[i]*v for row,v in zip(rows,y)) for i in range(n)]
        coeff=linear_solve(normal,rhs)
        if coeff is None:return (math.inf,None)
        if not bounds['rs'][0]<=coeff[0]<=bounds['rs'][1] or any(not bounds['r'][0]<=r<=bounds['r'][1] for r in coeff[1:]):return (math.inf,None)
        score=sum((sum(a*b for a,b in zip(row,coeff))-v)**2 for row,v in zip(rows,y))
        return score,(coeff,tau)
    lower,upper=map(math.log10,bounds['tau'])
    grid=[lower+(upper-lower)*i/64 for i in range(65)]
    seeds=[]
    for logs in combinations(grid,count):
        score,_=project(logs)
        if math.isfinite(score):seeds.append((score,list(logs)))
    if not seeds:raise ValueError('no feasible linear coefficients on starting grid')
    # Multiple starts reduce (but do not remove) local-optimization risk.
    finalists=[]
    for _,logs in sorted(seeds)[:8]:
        score,_=project(logs);step=(upper-lower)/64
        for _ in range(180):
            choices=[]
            for axis in range(count):
                for sign in (-1,1):
                    trial=logs.copy();trial[axis]+=sign*step
                    trial_score,_=project(trial);choices.append((trial_score,trial))
            candidate,newlogs=min(choices)
            if candidate<score:score,logs=candidate,newlogs
            else:step/=2
            if step<1e-11:break
        finalists.append((score,logs))
    score,logs=min(finalists);_,(coeff,tau)=project(logs)
    branches=sorted(zip(coeff[1:],tau),key=lambda pair:pair[1])
    return {'rs':format(coeff[0],'.12g'),'branches':[{'r':format(r,'.12g'),'tau':format(t,'.12g')} for r,t in branches]}, {'squared_residual':score,'forward_projections':evaluations}


def solve(case):
    started=time.perf_counter()
    two,two_metrics=fit(case,2)
    report={'two_branch':two}
    certificate=next((list(c) for c in combinations(range(len(case['observations'])),3) if excludes(case,list(c))),None)
    metrics={'two_branch_fit':two_metrics}
    if certificate is not None:
        report.update(single_branch_status='excluded',certificate=certificate)
    else:
        one,one_metrics=fit(case,1);metrics['one_branch_fit']=one_metrics
        d,choice=measurement(case,one,two)
        report.update(single_branch_status='feasible',one_branch=one,
            interpretation='finite_band_ambiguity_for_submitted_witnesses',
            d_vector=list(map(str,d)),next_measurement=choice)
    check(case,report)
    metrics['elapsed_seconds']=time.perf_counter()-started
    return report,metrics
