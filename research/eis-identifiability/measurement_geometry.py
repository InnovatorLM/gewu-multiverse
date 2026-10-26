"""Exact closed-rectangle check for conditional witness-pair measurements.

This does not infer discrimination of whole model families or confidence levels.
"""
from fractions import Fraction as F


def controls():
    count=0
    for ar in range(-3,4):
        for ai in range(-3,4):
            for br in range(-3,4):
                for bi in range(-3,4):
                    for er,ei in [(F(1),F(1)),(F(1,2),F(2)),(F(2),F(1,2))]:
                        disjoint=(ar+er<br-er or br+er<ar-er or ai+ei<bi-ei or bi+ei<ai-ei)
                        distance=max(abs(F(ar-br))/(2*er),abs(F(ai-bi))/(2*ei))
                        assert disjoint==(distance>1)
                        count+=1
    return {'closed_rectangle_checks':count,'criterion_verified_on_controls':True,'equality_means_overlap':True,'model_calls':0,'scientific_acceptance':False}


if __name__=='__main__':
    import json
    print(json.dumps(controls()))
