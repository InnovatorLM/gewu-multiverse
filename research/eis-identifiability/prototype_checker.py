"""Independent exact checker for the research interface; imports no generator/fitter."""
from fractions import Fraction as Q


def number(v):
    if type(v) not in (str, int):
        raise ValueError('exact integer/decimal/rational required')
    return Q(v)


def impedance(w, witness, boxes, count):
    rs = number(witness['rs'])
    branches = witness['branches']
    if len(branches) != count or not number(boxes['rs'][0]) <= rs <= number(boxes['rs'][1]):
        raise ValueError('branch count or series resistance')
    parameters = [(number(b['r']), number(b['tau'])) for b in branches]
    if len({t for _, t in parameters}) != count:
        raise ValueError('reducible equal-tau branches')
    real, imag = rs, Q(0)
    for r, t in parameters:
        if not (0 < number(boxes['r'][0]) <= r <= number(boxes['r'][1]) and
                0 < number(boxes['tau'][0]) <= t <= number(boxes['tau'][1])):
            raise ValueError('parameter box')
        factor = 1 + w*w*t*t
        real += r/factor
        imag -= r*w*t/factor
    return real, imag


def feasible(case, witness, count):
    for row in case['observations']:
        actual = impedance(number(row['omega']), witness, case['boxes'], count)
        if any(abs(p-number(row[k])) > number(row[e]) for p,k,e in
               zip(actual, ('real','imag'), ('error_real','error_imag'))):
            raise ValueError('witness outside observation envelope')


def excludes(case, indices):
    if (type(indices) is not list or len(indices) != 3 or
            any(type(i) is not int for i in indices) or
            not 0 <= indices[0] < indices[1] < indices[2] < len(case['observations'])):
        raise ValueError('invalid certificate indices')
    rows = [case['observations'][i] for i in indices]
    w = [number(r['omega']) for r in rows]
    q = [((-number(r['imag'])-number(r['error_imag']))/f,
          (-number(r['imag'])+number(r['error_imag']))/f) for r,f in zip(rows,w)]
    n = (q[0][0]-q[1][1], q[0][1]-q[1][0])
    d = (w[1]**2*q[1][0]-w[0]**2*q[0][1], w[1]**2*q[1][1]-w[0]**2*q[0][0])
    if min(q[0][0],n[0],d[0]) <= 0:
        return False
    lo, hi = n[0]/d[1], n[1]/d[0]
    a, b = q[0][0]*(1+w[0]**2*lo), q[0][1]*(1+w[0]**2*hi)
    return b/(1+w[2]**2*lo) < q[2][0] or a/(1+w[2]**2*hi) > q[2][1]


def measurement(case, one, two):
    distances = []
    for option in case['measurement_options']:
        w = number(option['omega'])
        a = impedance(w, one, case['boxes'], 1)
        b = impedance(w, two, case['boxes'], 2)
        errors = [number(option[k]) for k in ('error_real','error_imag')]
        if min(errors) <= 0 or number(option['cost']) < 0:
            raise ValueError('invalid measurement precision/cost')
        distances.append(max(abs(x-y)/(2*e) for x,y,e in zip(a,b,errors)))
    options = [(number(o['cost']),i) for i,o in enumerate(case['measurement_options']) if distances[i] > 1]
    return distances, min(options)[1] if options else 'not_resolvable'


def validate_case(case):
    if case.get('measurement_goal','conditional_pair') not in ('conditional_pair','separating_witness_pair'):
        raise ValueError('unknown public measurement goal')
    if case['units'] != {'omega':'rad/s','impedance':'ohm','tau':'s'}:
        raise ValueError('unsupported units')
    for key in ('rs','r','tau'):
        limits = list(map(number,case['boxes'][key]))
        if len(limits)!=2 or not 0 <= limits[0] < limits[1] or (key!='rs' and limits[0]==0):
            raise ValueError('invalid public parameter bounds')
    previous = Q(0)
    if len(case['observations']) < 3:
        raise ValueError('at least three observations required')
    for row in case['observations']:
        frequency = number(row['omega'])
        if frequency <= previous or min(number(row[k]) for k in ('error_real','error_imag')) <= 0:
            raise ValueError('ordered positive frequencies and error bounds required')
        previous = frequency
        number(row['real']); number(row['imag'])
    if not case['measurement_options']:
        raise ValueError('measurement menu required')
    for option in case['measurement_options']:
        if min(number(option[k]) for k in ('omega','error_real','error_imag')) <= 0 or number(option['cost']) < 0:
            raise ValueError('invalid measurement option')


def check(case, report):
    validate_case(case)
    feasible(case, report['two_branch'], 2)
    status = report['single_branch_status']
    if status == 'excluded':
        if not excludes(case, report['certificate']):
            raise ValueError('inconclusive exclusion certificate')
    elif status == 'feasible':
        feasible(case, report['one_branch'], 1)
        if report['interpretation'] != 'finite_band_ambiguity_for_submitted_witnesses':
            raise ValueError('unsupported inference')
        distances, choice = measurement(case, report['one_branch'], report['two_branch'])
        if case.get('measurement_goal','conditional_pair') == 'separating_witness_pair' and max(distances) <= 1:
            raise ValueError('public objective requires a strictly separating witness pair')
        if list(map(number, report['d_vector'])) != distances or report['next_measurement'] != choice or type(report['next_measurement']) not in (int,str):
            raise ValueError('incorrect conditional measurement decision')
    else:
        raise ValueError('unsupported status')
    return True
