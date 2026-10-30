import importlib.util
from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).parent/'acs_helpers'))
spec=importlib.util.spec_from_file_location('run_guard_controls',Path(__file__).parent/'acs_helpers/run_guard.py')
guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard)
class ControlModeTests(unittest.TestCase):
 def test_new_run_watchdog_is_observation_only(self):
  source=(Path(__file__).parent/'acs_helpers/run_guard.py').read_text()
  startup=[line for line in source.splitlines() if "watchdog_snapshot(kw[" in line]
  self.assertEqual(len(startup),1)
  self.assertIn('kill=False',startup[0])
 def test_nonmodel_controls_do_not_need_provider_configuration(self):
  for name in ['oracle','nop']:
   self.assertEqual(guard.execution_mode({'agents':[{'name':name}]}),name)
 def test_actual_model_still_requires_provider(self):
  for name in ['codex','mini-swe-agent']:
   self.assertEqual(guard.execution_mode({'agents':[{'name':name}]}),'llm')
if __name__=='__main__':unittest.main()
