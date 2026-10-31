import json
from pathlib import Path
import tempfile
import unittest
from evaluation_queue import W
from selftest_budget import verify,merge


class BudgetTests(unittest.TestCase):
    def test_actual_acs_intervals_refunded_once_and_unverified_pauses_not_refunded(self):
        with tempfile.TemporaryDirectory(dir=W/'.tmp') as raw:
            root=Path(raw);state=root/'state';job=state/('a'*32);job.mkdir(parents=True)
            status=dict(role='author-01',idea_id='idea',job_id='a'*32,received_at=20,
                        trials=[dict(cleanup_confirmed=True,acs_started_at=30,acs_finished_at=50),
                                dict(cleanup_confirmed=True,acs_started_at=40,acs_finished_at=60)])
            (job/'status.json').write_text(json.dumps(status))
            obs=root/'clock.json';row=dict(status='active',first_observed_at=10,events=[dict(action='start',at=0),dict(action='platform-wait',at=5),dict(action='resume',at=90)])
            value=dict(role='author-01',observed_at=95,ideas={'idea':row});obs.write_text(json.dumps(value))
            result=verify(state,'author-01','idea',obs,100)
            self.assertEqual(result['acs_excluded_seconds'],30)
            self.assertEqual(result['active_iteration_seconds_upper_bound'],70)
            self.assertTrue(result['within_budget']);self.assertFalse(result['event_origin_attested'])
            result=verify(state,'author-01','idea',obs,20000)
            self.assertFalse(result['within_budget'])
            row['first_observed_at']=21;obs.write_text(json.dumps(value))
            with self.assertRaisesRegex(ValueError,'before its first selftest'):verify(state,'author-01','idea',obs,100)
            row['first_observed_at']=10;obs.write_text(json.dumps(value));status['trials'][0]['cleanup_confirmed']=False;(job/'status.json').write_text(json.dumps(status))
            with self.assertRaisesRegex(ValueError,'cleanup'):verify(state,'author-01','idea',obs,100)

    def test_interval_boundaries_and_nonfinite_values(self):
        self.assertEqual(merge([(-1,20),(15,30),(40,200)],0,100),[[0,30],[40,100]])
        with self.assertRaises(ValueError):merge([(0,float('nan'))],0,100)


if __name__=='__main__':unittest.main()
