import copy
from fractions import Fraction as F
import unittest
from prototype import build
from prototype_checker import check, number, impedance


class PrototypeTests(unittest.TestCase):
    def setUp(self):
        self.data = build()

    def test_both_cases_and_serialized_slack(self):
        for name, case in self.data['cases'].items():
            report = self.data['known_witness_reports'][name]
            self.assertTrue(check(case,report))
            models = [(report['two_branch'],2)]
            if name == 'ambiguous': models.append((report['one_branch'],1))
            for model,count in models:
                for row in case['observations']:
                    prediction = impedance(number(row['omega']),model,case['boxes'],count)
                    for value,key in zip(prediction,('real','imag')):
                        self.assertGreater(number(row['error_'+key])-abs(value-number(row[key])), F('0.005'))

    def test_permutations_and_alternative_series_resistance(self):
        for name,case in self.data['cases'].items():
            report = copy.deepcopy(self.data['known_witness_reports'][name])
            report['two_branch']['branches'].reverse()
            self.assertTrue(check(case,report))
        # Alternate feasible parameters are not required to match the generator.
        case=self.data['cases']['excluded']
        report=copy.deepcopy(self.data['known_witness_reports']['excluded'])
        report['two_branch']['rs']='5.001'
        self.assertTrue(check(case,report))

    def test_negative_controls(self):
        for name in self.data['cases']:
            case=self.data['cases'][name]
            original=self.data['known_witness_reports'][name]
            mutations=[]
            bad=copy.deepcopy(original);bad['two_branch']['rs']='50';mutations.append(bad)
            bad=copy.deepcopy(original);bad['two_branch']['branches'][0]['tau']=bad['two_branch']['branches'][1]['tau'];mutations.append(bad)
            bad=copy.deepcopy(original);bad['two_branch']['branches'][0]['r']='-80';mutations.append(bad)
            bad=copy.deepcopy(original);bad['two_branch']['branches'][0]['tau']=0.01;mutations.append(bad)
            bad=copy.deepcopy(original);bad['single_branch_status']='always_feasible';mutations.append(bad)
            bad=copy.deepcopy(original);bad['two_branch']['branches'][0]['tau']='10';mutations.append(bad)
            if name=='excluded':
                bad=copy.deepcopy(original);bad['certificate']=[True,1,2];mutations.append(bad)
                bad=copy.deepcopy(original);bad['certificate']=[0,0,1];mutations.append(bad)
                bad=copy.deepcopy(original);bad['single_branch_status']='feasible';bad['one_branch']=self.data['known_witness_reports']['ambiguous']['one_branch'];mutations.append(bad)
            else:
                bad=copy.deepcopy(original);bad['d_vector'][0]='999';mutations.append(bad)
                bad=copy.deepcopy(original);bad['next_measurement']='not_resolvable';mutations.append(bad)
                bad=copy.deepcopy(original);bad['single_branch_status']='excluded';bad['certificate']=[0,1,2];mutations.append(bad)
            for bad in mutations:
                with self.subTest(name=name,bad=bad),self.assertRaises(ValueError):check(case,bad)


if __name__=='__main__':unittest.main()
