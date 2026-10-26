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
