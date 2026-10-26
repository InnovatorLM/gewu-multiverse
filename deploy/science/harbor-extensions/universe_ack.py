from copy import deepcopy
from pathlib import Path
from harbor.environments.ack import ACKEnvironment

class UniverseACK(ACKEnvironment):
    def __init__(self, *, runtime_image, verifier_image, environment_dir, pod_overrides=None, **kwargs):
        overrides = deepcopy(pod_overrides or {})
        role = 'verifier' if Path(environment_dir).name == 'tests' else 'runtime'
        image = verifier_image if role == 'verifier' else runtime_image
        if '@sha256:' not in image:
            raise ValueError('Explicit immutable image digest required')
        overrides.setdefault('spec', {}).setdefault('containers', [{'name': 'main'}])[0]['image'] = image
        overrides.setdefault('metadata', {}).setdefault('labels', {})['universe-role'] = role
        super().__init__(environment_dir=environment_dir, pod_overrides=overrides, **kwargs)
        self._universe_image = image

    def _get_image_url(self):
        return self._universe_image

    async def download_dir_filtered(self, source_dir, target_dir, *, include=None, exclude=None, protect=None):
        # Reward is tiny text; avoid the ACK binary websocket tar transport.
        if str(source_dir) == '/logs/verifier':
            target = Path(target_dir)
            target.mkdir(parents=True, exist_ok=True)
            result = await self.exec(command='cat /logs/verifier/reward.txt')
            value = (result.stdout or '').strip()
            if result.return_code != 0 or value not in {'0', '1', '0.0', '1.0'}:
                raise ValueError('Missing or invalid verifier reward')
            (target / 'reward.txt').write_text(value)
            return
        return await super().download_dir_filtered(source_dir, target_dir, include=include, exclude=exclude, protect=protect)
