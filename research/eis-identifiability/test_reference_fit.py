"""Public-data numerical fitting followed by exact independent verification."""
import copy
import unittest
from prototype import build
from reference_fit import solve, fit
from prototype_checker import check, number, measurement


class ReferenceFitTests(unittest.TestCase):
    def test_solve_only_public_case_and_accept_alternate_parameters(self):
        fixtures=build()
        for name,case in fixtures['cases'].items():
            public=copy.deepcopy(case)
            report,metrics=solve(public)
            self.assertEqual(public,case)
            self.assertTrue(check(case,report))
            self.assertEqual(report['single_branch_status'],fixtures['known_witness_reports'][name]['single_branch_status'])
            self.assertGreater(metrics['two_branch_fit']['forward_projections'],0)
            if name=='ambiguous':
                self.assertNotEqual(report['two_branch'],fixtures['known_witness_reports'][name]['two_branch'])
                self.assertIs(type(report['next_measurement']),int)

    def test_v2_near_merged_pair_is_a_legal_easy_answer(self):
        case=build()['cases']['ambiguous']
        one,_=fit(case,1)
        branch=one['branches'][0]
        r=number(branch['r'])/2; t=number(branch['tau']); delta=number('0.0000000001')
        two={'rs':one['rs'],'branches':[{'r':str(r),'tau':str(t-delta)}, {'r':str(r),'tau':str(t+delta)}]}
        distances,choice=measurement(case,one,two)
        self.assertEqual(choice,'not_resolvable')
        self.assertLess(max(distances),number('0.000000000001'))
        report={'two_branch':two,'one_branch':one,'single_branch_status':'feasible',
            'interpretation':'finite_band_ambiguity_for_submitted_witnesses',
            'd_vector':list(map(str,distances)),'next_measurement':choice}
        # Legal under conditional v2, but fails the explicitly public v3 objective.
        with self.assertRaises(ValueError):check(case,report)
        case['measurement_goal']='conditional_pair'
        self.assertTrue(check(case,report))
        del case['measurement_goal']
        self.assertTrue(check(case,report))

    def test_public_schema_and_discrete_choice(self):
        data=build();case=data['cases']['ambiguous'];report=data['known_witness_reports']['ambiguous']
        bad=copy.deepcopy(case);bad['measurement_goal']='seperating_witness_pair'
        with self.assertRaises(ValueError):check(bad,report)
        for key,value in [('omega','Hz'),('impedance','kilohm')]:
            bad=copy.deepcopy(case);bad['units'][key]=value
            with self.assertRaises(ValueError):check(bad,report)
        self.assertEqual(number('1e-3'),number('1/1000'))
        for value in ('1_000',' 1','1/-2'):
            with self.assertRaises(ValueError):number(value)
        bad=copy.deepcopy(report);bad['d_vector'][0]=1
        with self.assertRaises(ValueError):check(case,bad)
        for value in (True,1.0):
            bad=copy.deepcopy(report);bad['next_measurement']=value
            with self.assertRaises(ValueError):check(case,bad)
        for mutate in ('negative_cost','zero_error','unordered','negative_tau'):
            bad=copy.deepcopy(case)
            if mutate=='negative_cost':bad['measurement_options'][0]['cost']='-1'
            elif mutate=='zero_error':bad['observations'][0]['error_imag']='0'
            elif mutate=='unordered':bad['observations'][1]['omega']='0.001'
            else:bad['boxes']['tau'][0]='-1'
            with self.assertRaises(ValueError):check(bad,report)


if __name__=='__main__':unittest.main()
