import unittest
import tomllib
from role_codex_runner import MODEL, config

class RunnerConfigTests(unittest.TestCase):
    def test_explicit_provider_without_host_config(self):
        settings=tomllib.loads(config(12345))
        self.assertEqual(settings['model'],MODEL)
        self.assertEqual(settings['model_provider'],'dawnfm-role-gateway')
        provider=settings['model_providers']['dawnfm-role-gateway']
        self.assertEqual(provider['base_url'],'http://127.0.0.1:12345/v1')
        self.assertEqual(provider['wire_api'],'responses')
        self.assertEqual(settings['shell_environment_policy']['inherit'],'none')
        self.assertNotIn('OPENAI_API_KEY',config(12345))

    def test_invalid_port_refused(self):
        for value in [True,0,80,65536,'12345']:
            with self.assertRaises(ValueError):config(value)

if __name__=='__main__':unittest.main()

class CaptureTests(unittest.TestCase):
    def test_streaming_redaction_and_timeout(self):
        import tempfile, sys, os, json
        from pathlib import Path
        from role_codex_runner import capture
        with tempfile.TemporaryDirectory(dir='/mnt/data/zhanglinfeng/workspace/.tmp') as temp:
            root = Path(temp)
            result = capture([sys.executable, '-c', 'import sys;print("secret-token");print("error secret-token",file=sys.stderr)'],
                             prompt='hello', env=os.environ.copy(), cwd=temp, timeout=5,
                             archive=root/'success', secrets=('secret-token',))
            self.assertEqual(result['returncode'], 0)
            self.assertNotIn('secret-token', (root/'success/events.jsonl').read_text())
            self.assertIn('[REDACTED]', (root/'success/stderr.log').read_text())
            self.assertEqual((root/'success/events.jsonl').stat().st_mode & 0o777, 0o600)
            result = capture([sys.executable, '-u', '-c', 'import time;print("partial");time.sleep(30)'],
                             prompt='', env=os.environ.copy(), cwd=temp, timeout=2,
                             archive=root/'timeout')
            self.assertEqual(result['returncode'], 124)
            self.assertIn('partial', (root/'timeout/events.jsonl').read_text())
            self.assertEqual(json.loads((root/'timeout/metadata.json').read_text())['status'], 'timeout')
