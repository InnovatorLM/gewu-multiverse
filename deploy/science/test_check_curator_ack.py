"""Authenticated identity, exact versions and superseding decisions are required."""
import copy
import unittest
from check_curator_ack import inspect
from configure_review_protection import POLICY


class AckTests(unittest.TestCase):
    def setUp(self):
        self.head = 'a' * 40
        self.digest = 'b' * 64
        self.pull = {'state': 'open', 'merged': False, 'head': {'sha': self.head},
                     'base': {'ref': 'main'}, 'user': {'id': 3}}
        self.users = {name: {'login': name, 'id': uid}
                      for name, uid in [('science-evaluator', 1), ('owner', 2)]}
        self.reviews = [{'id': uid, 'user': {'id': uid}, 'state': 'APPROVED',
                         'official': True, 'dismissed': False, 'commit_id': self.head,
                         'body': 'science-review-inventory-sha256:' + self.digest} for uid in (1, 2)]

    def check(self, **changes):
        values = dict(pull=self.pull, reviews=self.reviews, protection=POLICY,
                      users=self.users, inventory_sha256=self.digest, expected_head=self.head)
        values.update(changes)
        return inspect(**values)

    def test_bound_ack_is_not_admission_or_user_approval(self):
        result = self.check()
        self.assertTrue(result['acknowledgments_verified'])
        for key in ('release_eligible', 'scientific_acceptance', 'first_pilot_user_approval_verified', 'merged_any_task'):
            self.assertIs(result[key], False)

    def test_forged_stale_dismissed_unofficial_or_unbound_reviews(self):
        for key, value in [('user', {'id': 9}), ('commit_id', 'c' * 40),
                           ('dismissed', True), ('official', False), ('body', 'unbound')]:
            reviews = copy.deepcopy(self.reviews)
            reviews[0][key] = value
            with self.subTest(key=key):
                self.assertFalse(self.check(reviews=reviews)['acknowledgments_verified'])

    def test_later_decision_revokes_old_approval_and_duplicate_ids_fail(self):
        later = dict(self.reviews[0], id=5, state='REQUEST_CHANGES')
        self.assertFalse(self.check(reviews=self.reviews + [later])['acknowledgments_verified'])
        dismissed = dict(self.reviews[0], id=6, dismissed=True)
        self.assertFalse(self.check(reviews=self.reviews + [dismissed])['acknowledgments_verified'])
        with self.assertRaises(ValueError):
            self.check(reviews=self.reviews + [self.reviews[0]])

    def test_wrong_commit_self_review_closed_pull_or_policy_fail(self):
        for field, value in [('head', {'sha': 'c' * 40}), ('user', {'id': 1}),
                             ('state', 'closed'), ('base', {'ref': 'other'})]:
            with self.subTest(field=field):
                self.assertFalse(self.check(pull=dict(self.pull, **{field: value}))['acknowledgments_verified'])
        self.assertFalse(self.check(protection=dict(POLICY, required_approvals=0))['acknowledgments_verified'])


if __name__ == '__main__':
    unittest.main()
