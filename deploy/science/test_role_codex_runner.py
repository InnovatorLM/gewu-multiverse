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
