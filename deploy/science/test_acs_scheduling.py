import unittest
from acs_scheduling import enforce
class SchedulingTests(unittest.TestCase):
    def test_every_or_term_excludes_forbidden_zone(self):
        original={'affinity':{'nodeAffinity':{'requiredDuringSchedulingIgnoredDuringExecution':{'nodeSelectorTerms':[{'matchExpressions':[{'key':'disk','operator':'In','values':['ssd']}]},{}]}}}}
        spec=enforce(original)
        terms=spec['affinity']['nodeAffinity']['requiredDuringSchedulingIgnoredDuringExecution']['nodeSelectorTerms']
        for term in terms:
            self.assertEqual(sum(e['operator']=='NotIn' and e['values']==['cn-beijing-f'] for e in term['matchExpressions']),2)
        self.assertEqual(len(original['affinity']['nodeAffinity']['requiredDuringSchedulingIgnoredDuringExecution']['nodeSelectorTerms'][0]['matchExpressions']),1)
        self.assertEqual(enforce(spec),spec)
