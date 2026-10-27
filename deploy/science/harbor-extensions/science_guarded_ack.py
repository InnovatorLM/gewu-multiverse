"""Opt-in ACS verifier process-tree guard. Requires a fresh dedicated verifier.

All exec calls are guarded for a no-network verifier. This is not Pod-wide
isolation; sidecars, services, and reused environments are outside its scope.
"""
import base64
import shlex
from copy import deepcopy
from pathlib import Path, PurePosixPath
from harbor.environments.capabilities import EnvironmentCapabilities
from harbor.models.task.config import NetworkMode
from universe_ack import UniverseACK

class ScienceGuardedACK(UniverseACK):
    def __init__(self, *, environment_dir, **kwargs):
        self._guarded_verifier = Path(environment_dir).name == 'tests'
        policy = kwargs.get('network_policy')
        if self._guarded_verifier and policy and policy.network_mode == NetworkMode.NO_NETWORK:
            overrides = deepcopy(kwargs.get('pod_overrides') or {})
            spec = overrides.setdefault('spec', {})
            containers = spec.setdefault('containers', [{'name': 'main'}])
            if len(containers) != 1 or spec.get('initContainers'):
                raise ValueError('Dedicated single-container verifier required')
            main = containers[0]
            main['securityContext'] = {
                'privileged': False,
                'readOnlyRootFilesystem': True,
                'allowPrivilegeEscalation': False,
                'capabilities': {'drop': ['ALL'], 'add': []},
            }
            if spec.get('volumes') or main.get('volumeMounts'):
                raise ValueError('Unreviewed verifier mounts refused')
            spec['automountServiceAccountToken'] = False
            spec['volumes'] = [{'name': name, 'emptyDir': {}}
                               for name in ('guard-tmp','guard-logs','guard-workspace')]
            main['volumeMounts'] = [
                {'name': name, 'mountPath': path}
                for name,path in [('guard-tmp','/tmp'),('guard-logs','/logs'),
                                  ('guard-workspace','/workspace')]]
            kwargs['pod_overrides'] = overrides
        super().__init__(environment_dir=environment_dir, **kwargs)
        if self.network_policy.network_mode == NetworkMode.NO_NETWORK:
            if not self._guarded_verifier:
                raise ValueError('No-network guard is limited to a dedicated verifier')
            if kwargs.get('use_sandbox_claim', False):
                raise ValueError('Reused sandbox pool refused for process guard')

    def _check_upload(self, source, target):
        if not self._guarded_verifier:
            return
        destination = PurePosixPath(target)
        if not destination.is_absolute() or '..' in destination.parts:
            raise ValueError('Absolute normalized verifier upload path required')
        # This experimental adapter is deliberately scoped to the frozen
        # stacking-disorder task, not arbitrary artifact destinations.
        # Tests must be baked into the immutable verifier image.
        roots = (PurePosixPath('/workspace/stacking_submission'),)
        if not any(destination == root or root in destination.parents for root in roots):
            raise ValueError('Upload outside reviewed verifier artifact roots')
        source = Path(source)
        paths = [source, *source.rglob('*')] if source.is_dir() else [source]
        for path in paths:
            if path.is_symlink() or not (path.is_dir() or path.is_file()):
                raise ValueError('Symlink or special file refused in verifier upload')

    async def upload_file(self, source_path, target_path):
        self._check_upload(source_path, target_path)
        return await super().upload_file(source_path, target_path)

    async def upload_dir(self, source_dir, target_dir):
        self._check_upload(source_dir, target_dir)
        return await super().upload_dir(source_dir, target_dir)

    @property
    def capabilities(self):
        return EnvironmentCapabilities(disable_internet=self._guarded_verifier)

    async def exec(self, command, **kwargs):
        if self.network_policy.network_mode == NetworkMode.NO_NETWORK:
            source = Path(__file__).with_name('no_network_exec.py').read_text()
            source = source.split("if __name__ == '__main__':")[0]
            payload = source + '\ninstall()\nos.execvp("/bin/bash", ["/bin/bash", "--noprofile", "--norc", "-c", ' + repr(command) + '])\n'
            encoded = base64.b64encode(payload.encode()).decode()
            wrapper = 'import base64;exec(compile(base64.b64decode(' + repr(encoded) + '),"<trusted-network-guard>","exec"))'
            command = 'python3 -I -c ' + shlex.quote(wrapper)
        return await super().exec(command=command, **kwargs)
