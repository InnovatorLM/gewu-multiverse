"""Exact controls and bounded perturbations; no optimizer, model or ACS calls."""
from fractions import Fraction as F
from itertools import product
import unittest
from feasibility import response,exclusion,study


class FeasibilityTests(unittest.TestCase):
    def test_ambiguous_and_resolvable_cases(self):
        result=study()
        self.assertTrue(result['ambiguous_case']['single_and_two_branch_witnesses_within_error'])
        self.assertFalse(result['ambiguous_case']['exclusion_check']['single_rc_excluded'])
        self.assertTrue(result['resolvable_case']['single_rc_excluded'])
        self.assertFalse(result['single_rc_control']['single_rc_excluded'])
        self.assertFalse(result['scientific_acceptance'])

    def test_single_rc_never_excluded_within_declared_error(self):
        w=[F(10),F(100),F(1000)];e=F(1,100)
        for resistance,tau,rs,signs in product([F(1),F(80),F(200)],[F(1,1000),F(1,100),F(1,10)],[F(0),F(5)],product([-1,0,1],repeat=3)):
            y=[response(f,rs,[(resistance,tau)])[1]+s*e for f,s in zip(w,signs)]
            with self.subTest(resistance=str(resistance),tau=str(tau),signs=signs):self.assertFalse(exclusion(w,y,e)['single_rc_excluded'])

    def test_canonical_order_is_not_scientific_identification(self):
        branches=[(80,F(1,100)),(120,F(1,10))]
        for w in [1,10,100,1000]:self.assertEqual(response(w,5,branches),response(w,5,branches[::-1]))
        with self.assertRaises(ValueError):exclusion([10,10,100],[0,0,0],F(1,100))
        with self.assertRaises(ValueError):exclusion([1,10,100],[0,0,0],-1)


if __name__=='__main__':unittest.main()
