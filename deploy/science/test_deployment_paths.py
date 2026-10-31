import os
import subprocess
from pathlib import Path
import tempfile
import unittest
import json
from unittest.mock import patch
from deployment_paths import universe_root,WORKSPACE,deployment_state_root,require_isolated_service_config

class DeploymentTests(unittest.TestCase):
    def test_launcher_rejects_invalid_root_before_starting_services(self):
        env=dict(os.environ,GEWU_UNIVERSE_ROOT='/root/disallowed-universe')
        result=subprocess.run(['bash',str(Path(__file__).with_name('start-universe'))],env=env,capture_output=True,text=True,timeout=10)
        self.assertNotEqual(result.returncode,0)
        self.assertIn('Universe root must be an absolute directory below workspace',result.stderr)

    def test_launcher_refuses_unprovisioned_universe_before_mutation(self):
        with tempfile.TemporaryDirectory(dir=WORKSPACE/'.tmp') as raw:
            root=Path(raw)/'universes/empty';root.mkdir(parents=True)
            env=dict(os.environ,GEWU_UNIVERSE_ROOT=str(root))
            result=subprocess.run(['bash',str(Path(__file__).with_name('start-universe'))],env=env,capture_output=True,text=True,timeout=10)
            self.assertNotEqual(result.returncode,0)
            self.assertIn('Universe services are not isolated/configured',result.stderr)
            self.assertEqual(list(root.iterdir()),[])

    def test_default_and_explicit_replacement_are_distinct(self):
        with tempfile.TemporaryDirectory(dir=WORKSPACE/'.tmp') as raw:
            root=Path(raw)
            with patch.dict(os.environ,{},clear=True):
                self.assertEqual(universe_root(root),root/'universes/my-terminal-bench-science')
            with patch.dict(os.environ,GEWU_UNIVERSE_ROOT=str(root/'universes/replacement')):
                self.assertEqual(universe_root(root),root/'universes/replacement')

    def test_outside_relative_and_workspace_itself_are_refused(self):
        for value in ('relative','/root/new-universe',str(WORKSPACE)):
            with self.subTest(value=value),patch.dict(os.environ,GEWU_UNIVERSE_ROOT=value),self.assertRaises(ValueError):
                universe_root()

    def test_service_paths_are_owned_by_selected_universe(self):
        with tempfile.TemporaryDirectory(dir=WORKSPACE/'.tmp') as raw:
            root=Path(raw)/'universes/test-world'
            self.assertEqual(deployment_state_root(root),root/'.state/gewu-multiverse')

    def test_replacement_refuses_shared_or_missing_service_configuration(self):
        with tempfile.TemporaryDirectory(dir=WORKSPACE/'.tmp') as raw:
            root=Path(raw)/'universes/test-world'
            root.mkdir(parents=True)
            with self.assertRaisesRegex(RuntimeError,'not isolated/configured'):
                require_isolated_service_config(root)

    def test_replacement_requires_each_owned_service_config(self):
        with tempfile.TemporaryDirectory(dir=WORKSPACE/'.tmp') as raw:
            root=Path(raw)/'universes/test-world'
            state=root/'.state/gewu-multiverse'
            agents=root/'.config/gewu-multiverse/agents/evaluator-01'
            agents.mkdir(parents=True)
            broker=state/'role-broker/config.json';broker.parent.mkdir(parents=True)
            broker.write_text(json.dumps({'socket':str(root/'.state/gewu-multiverse/role-broker.sock'),'roles':{'evaluator-01':{'root':str(agents)}}}))
            queue=root/'.config/science-evaluation/queue.json'
            queue.parent.mkdir(parents=True)
            queue.write_text(json.dumps({key:str(root/'.state/gewu-multiverse/evaluation-queue'/key) for key in ('inbox','results','state','registry')}))
            for relative in ('review-dispatcher/config.json','author-selftest/config.json','command-watchdog/config.json'):
                path=state/relative;path.parent.mkdir(parents=True,exist_ok=True)
                path.write_text(json.dumps({'broker_config':str(broker),'state':str(state/relative.split('/')[0])}))
            (state/'deployment.json').write_text(json.dumps({'status':'service_config_prepared','universe_root':str(root)}))
            self.assertEqual(require_isolated_service_config(root),state)

    def test_shared_queue_state_is_rejected_even_when_other_configs_exist(self):
        with tempfile.TemporaryDirectory(dir=WORKSPACE/'.tmp') as raw:
            root=Path(raw)/'universes/test-world'
            state=root/'.state/gewu-multiverse'
            agents=root/'.config/gewu-multiverse/agents/evaluator-01';agents.mkdir(parents=True)
            broker=state/'role-broker/config.json';broker.parent.mkdir(parents=True)
            broker.write_text(json.dumps({'socket':str(root/'.state/gewu-multiverse/broker.sock'),'roles':{'evaluator-01':{'root':str(agents)}}}))
            queue=root/'.config/science-evaluation/queue.json';queue.parent.mkdir(parents=True)
            queue.write_text(json.dumps({'inbox':str(root / '.inbox'),'results':str(root / '.results'),'state':str(WORKSPACE / '.state/shared'),'registry':str(root / '.registry')}))
            for name in ('review-dispatcher','author-selftest','command-watchdog'):
                path=state/(name+'/config.json');path.parent.mkdir(parents=True,exist_ok=True)
                path.write_text(json.dumps({'broker_config':str(broker),'state':str(state/name)}))
            (state/'deployment.json').write_text(json.dumps({'status':'service_config_prepared','universe_root':str(root)}))
            with self.assertRaisesRegex(RuntimeError,'references shared state'):
                require_isolated_service_config(root)

    def test_service_marker_does_not_claim_full_deployment_readiness(self):
        with tempfile.TemporaryDirectory(dir=WORKSPACE/'.tmp') as raw:
            root=Path(raw);state=root/'.state/gewu-multiverse';broker=state/'role-broker/config.json'
            broker.parent.mkdir(parents=True);broker.write_text(json.dumps({'socket':'@'+str(state/'role-broker.sock'),'roles':{}}))
            queue=root/'.config/science-evaluation/queue.json';queue.parent.mkdir(parents=True)
            queue.write_text(json.dumps({'state':str(state/'evaluation-queue'),'registry':str(root/'.config/science-evaluation/registry.json')}))
            (root/'.config/science-evaluation/registry.json').write_text('{}')
            for name in ('review-dispatcher','author-selftest','command-watchdog'):
                path=state/(name+'/config.json');path.parent.mkdir(parents=True,exist_ok=True)
                path.write_text(json.dumps({'broker_config':str(broker),'state':str(state/name)}))
            (state/'deployment.json').write_text(json.dumps({'status':'prepared','universe_root':str(root)}))
            with self.assertRaisesRegex(RuntimeError,'malformed or references shared state'):
                require_isolated_service_config(root)
