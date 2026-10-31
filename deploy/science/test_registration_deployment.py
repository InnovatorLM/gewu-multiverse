"""Registration CLIs must never silently select a different world's queue."""
import argparse
import os
from pathlib import Path
import unittest
from unittest.mock import patch

import register_evaluation as evaluation
import register_acs_quality as quality
from deployment_paths import WORKSPACE


class RegistrationDeploymentTests(unittest.TestCase):
    def test_both_commands_select_current_world_and_fail_closed(self):
        args = argparse.Namespace(evaluation_id='example', settings=WORKSPACE/'settings.json',
                                  repo=WORKSPACE/'repo', commit='a'*40, task_path='task')
        for module in (evaluation, quality):
            for root in (str(WORKSPACE/'.tmp/registration-test-world'), '/root/forbidden'):
                visited = []
                def read(path):
                    visited.append(Path(path))
                    if Path(path) == args.settings:
                        return path
                    raise FileNotFoundError('selected queue absent')
                with self.subTest(command=module.__name__, root=root), \
                     patch.dict(os.environ, GEWU_UNIVERSE_ROOT=root), \
                     patch('argparse.ArgumentParser.parse_args', return_value=args), \
                     patch.object(module.os, 'geteuid', return_value=0), \
                     patch.object(module, 'root_file', side_effect=read), \
                     patch.object(quality, 'load_settings', return_value=({}, 'task')), \
                     patch.object(quality, 'source_inventory', return_value={}), \
                     patch.object(quality, 'task_inventory', return_value={}):
                    with self.assertRaises((FileNotFoundError, ValueError)):
                        module.main()
                    queues = [p for p in visited if p.name == 'queue.json']
                    self.assertEqual(queues, [] if root.startswith('/root/') else
                                     [Path(root)/'.config/science-evaluation/queue.json'])


if __name__ == '__main__':
    unittest.main()
