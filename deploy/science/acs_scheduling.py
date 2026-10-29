"""Mandatory deployment scheduling constraints, intersecting existing terms."""
from copy import deepcopy

def enforce(spec):
    result=deepcopy(spec)
    affinity=result.setdefault('affinity',{}).setdefault('nodeAffinity',{})
    required=affinity.setdefault('requiredDuringSchedulingIgnoredDuringExecution',{})
    terms=required.setdefault('nodeSelectorTerms',[{}])
    if not terms:
        raise ValueError('Empty node selector terms would never schedule')
    for term in terms:
        expressions=term.setdefault('matchExpressions',[])
        for key in ('topology.kubernetes.io/zone','failure-domain.beta.kubernetes.io/zone'):
            rule=dict(key=key,operator='NotIn',values=['cn-beijing-f'])
            if rule not in expressions:expressions.append(rule)
    return result
