"""Exact-rational proposal study, not a Harbor task or statistical classifier.

For Z=Rs+R/(1+i*w*tau), q=-Im(Z)/w=A/(1+w*w*x),
where A=R*tau and x=tau*tau. Bounded component errors give intervals
for q. Two frequencies bound x; a third can contradict those bounds.
All arithmetic used to exclude the model is rational, not floating point.
"""
from fractions import Fraction as F
import json


def rational(value):
    if type(value) not in (int, str, F):
        raise ValueError('Use integers, explicit decimal/rational strings or Fractions; binary floats are refused')
    return F(value)


def response(w, rs, branches):
    w,rs=rational(w),rational(rs)
    real=rs;imag=F(0)
    for resistance,tau in branches:
        r,t=rational(resistance),rational(tau);d=1+(w*t)**2
        real+=r/d;imag-=r*w*t/d
    return real,imag


def exclusion(omega,imaginary,absolute_error):
    if len(omega)!=3 or len(imaginary)!=3:raise ValueError('Three frequencies required')
    w=list(map(rational,omega));y=list(map(rational,imaginary));e=rational(absolute_error)
    if e<0 or not 0<w[0]<w[1]<w[2]:raise ValueError('Require ordered positive angular frequencies and nonnegative error')
    q=[((-value-e)/frequency,(-value+e)/frequency) for value,frequency in zip(y,w)]
    # Independent interval bounds are conservative: correlations are discarded,
    # so an overlap cannot prove existence of a feasible single-RC model.
    numerator=(q[0][0]-q[1][1],q[0][1]-q[1][0])
    denominator=(w[1]**2*q[1][0]-w[0]**2*q[0][1],w[1]**2*q[1][1]-w[0]**2*q[0][0])
    if min(q[0])<=0 or numerator[0]<=0 or denominator[0]<=0:
        return {'single_rc_excluded':False,'state':'inconclusive_interval_bounds'}
    x=(numerator[0]/denominator[1],numerator[1]/denominator[0])
    amplitude=(q[0][0]*(1+w[0]**2*x[0]),q[0][1]*(1+w[0]**2*x[1]))
    predicted=(amplitude[0]/(1+w[2]**2*x[1]),amplitude[1]/(1+w[2]**2*x[0]))
    excluded=predicted[1]<q[2][0] or q[2][1]<predicted[0]
    return {'single_rc_excluded':excluded,'state':'exact_interval_contradiction' if excluded else 'inconclusive_overlap',
            'tau_squared_bounds':[str(v) for v in x],
            'predicted_q3_bounds':[str(v) for v in predicted],
            'observed_q3_bounds':[str(v) for v in q[2]],
            'scope':'positive single Debye branch plus real series resistance; bounded imaginary-component errors only'}


def study():
    omega=[F(10),F(100),F(1000)];error=F(1,100)
    close=[(F(80),F(1,100)),(F(120),F(10001,1000000))]
    merged=[(F(200),F(50003,5000000))]
    broad=[(F(80),F(1,1000)),(F(120),F(1,10))]
    # Noise-free synthetic centers with an explicit bounded-error observation
    # envelope. No Gaussian probability or confidence-coverage claim is made.
    close_data=[response(w,5,close) for w in omega]
    errors=[abs(a-b) for w,pair in zip(omega,close_data) for a,b in zip(pair,response(w,5,merged))]
    broad_y=[response(w,5,broad)[1] for w in omega]
    control=[response(w,5,[(200,F(1,100))])[1] for w in omega]
    return {'kind':'proposal feasibility only','angular_frequency_rad_s':[str(w) for w in omega],
            'absolute_component_error_ohm':str(error),
            'ambiguous_case':{'single_and_two_branch_witnesses_within_error':max(errors)<=error,'max_component_difference_ohm':str(max(errors)),'exclusion_check':exclusion(omega,[p[1] for p in close_data],error)},
            'resolvable_case':exclusion(omega,broad_y,error),
            'single_rc_control':exclusion(omega,control,error),
            'scientific_acceptance':False,'difficulty_measured':False,'model_calls':0}


if __name__=='__main__':print(json.dumps(study(),indent=2))
