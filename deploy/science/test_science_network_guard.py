"""Local process/adapter checks. No LLM, Kubernetes, or cloud calls."""
import asyncio
import base64
import json
import logging
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

EXT = Path(__file__).parent / 'harbor-extensions'
sys.path.insert(0, str(EXT))
from science_guarded_ack import ScienceGuardedACK
from universe_ack import UniverseACK
from harbor.models.task.config import NetworkMode, NetworkPolicy
from harbor.trial.artifact_handler import ArtifactHandler

class GuardTests(unittest.TestCase):
    def test_real_harbor_artifact_handler_transfers_convention_and_task(self):
        obj=object.__new__(ScienceGuardedACK);obj._guarded_verifier=True
        uploaded=[]
        async def mkdir(*args,**kwargs):pass
        async def upload_dir(source_dir,target_dir):
            obj._check_upload(source_dir,target_dir);uploaded.append(target_dir)
        obj.empty_dirs=mkdir;obj.ensure_dirs=mkdir;obj.upload_dir=upload_dir
        workspace=Path(__file__).resolve().parents[3]
        with tempfile.TemporaryDirectory(dir=workspace/'.tmp') as temp:
            root=Path(temp)
            (root/'logs/artifacts').mkdir(parents=True)
            (root/'workspace/stacking_submission').mkdir(parents=True)
            (root/'workspace/stacking_submission/solve_stacking.py').write_text('pass\n')
            handler=ArtifactHandler(artifacts=['/workspace/stacking_submission/'],logger=logging.getLogger(__name__))
            asyncio.run(handler.upload_artifacts(obj,root,
                source_artifacts_dir='/logs/artifacts',target_artifacts_dir='/logs/artifacts'))
        self.assertEqual(set(uploaded),{'/logs/artifacts','/workspace/stacking_submission/'})

    def test_expansion_profiles_keep_artifact_boundaries(self):
        def initialize(obj, **kwargs):
            obj._network_policy=kwargs['network_policy']
            obj.pod_overrides=kwargs['pod_overrides']
        image='example.invalid/verifier@sha256:'+'b'*64
        workspace=Path(__file__).resolve().parents[3]
        with tempfile.TemporaryDirectory(dir=workspace/'.tmp') as temp:
            source=Path(temp)/'artifact';source.write_text('fixture')
            for profile,roots in ScienceGuardedACK.REVIEWED_ARTIFACTS.items():
                with self.subTest(profile=profile),patch.object(UniverseACK,'__init__',initialize):
                    obj=ScienceGuardedACK(environment_dir=Path('/original/tests'),
                        verifier_image=image,artifact_profile=profile,
                        network_policy=NetworkPolicy(network_mode=NetworkMode.NO_NETWORK))
                    for root in roots:obj._check_upload(source,root)
                    for forbidden in ['/tests/test_state.py','/etc/profile','/app/other.json']:
                        with self.assertRaises(ValueError):obj._check_upload(source,forbidden)
                    paths=[m['mountPath'] for m in obj.pod_overrides['spec']['containers'][0]['volumeMounts']]
                    self.assertEqual('/app' in paths,any(p.startswith('/app/') for p in roots))
        with self.assertRaises(ValueError):
            ScienceGuardedACK(environment_dir=Path('/tests'),artifact_profile='unknown')

    def test_verifier_evidence_includes_stdout_and_metrics(self):
        obj=object.__new__(UniverseACK)
        files={'reward.txt':b'0\n','test-stdout.txt':b'FAILED scientific assertion\n',
               'ctrf.json':b'{"results":{}}','nested/binary':bytes(range(256))}
        async def capture(**kwargs):
            from types import SimpleNamespace
            return SimpleNamespace(return_code=0,stdout=json.dumps({
                k:base64.b64encode(v).decode() for k,v in files.items()}))
        obj.exec=capture
        workspace=Path(__file__).resolve().parents[3]
        with tempfile.TemporaryDirectory(dir=workspace/'.tmp') as temp:
            asyncio.run(obj.download_dir('/logs/verifier',temp))
            for name,data in files.items():
                self.assertEqual((Path(temp)/name).read_bytes(),data)
            files['../escape']=b'bad'
            with self.assertRaises(ValueError):
                asyncio.run(obj.download_dir('/logs/verifier',temp))

    def test_original_verifier_permissions_and_trusted_seed(self):
        captured = {}
        def initialize(obj, **kwargs):
            captured.update(kwargs)
            obj._network_policy = kwargs['network_policy']
        image = 'example.invalid/verifier@sha256:' + 'a' * 64
        with patch.object(UniverseACK, '__init__', initialize):
            ScienceGuardedACK(
                environment_dir=Path('/original/tests'), verifier_image=image,
                network_policy=NetworkPolicy(network_mode=NetworkMode.NO_NETWORK),
            )
        spec = captured['pod_overrides']['spec']
        main = spec['containers'][0]
        self.assertTrue(main['securityContext']['readOnlyRootFilesystem'])
        self.assertNotIn('capabilities', main['securityContext'])
        seed = spec['initContainers'][0]
        self.assertEqual(seed['image'], image)
        self.assertEqual(seed['volumeMounts'], [{'name':'guard-tests','mountPath':'/seed'}])
        self.assertNotIn('guard-workspace', str(seed))
        self.assertIn({'name':'guard-tests','mountPath':'/tests'}, main['volumeMounts'])

    def test_socket_and_uring_denied_across_child_exec(self):
        code = '''import socket,ctypes,errno,json,subprocess,sys
r={}
for name,family in [('ipv4',socket.AF_INET),('ipv6',socket.AF_INET6),('unix',socket.AF_UNIX)]:
 try:socket.socket(family);r[name]=False
 except OSError as e:r[name]=e.errno==errno.EPERM
c=ctypes.CDLL(None,use_errno=True)
for name,n in [('uring',425),('x32',0x40000029)]:
 r[name]=c.syscall(n,0,0,0,0,0,0)==-1 and ctypes.get_errno()==errno.EPERM
p=subprocess.run([sys.executable,'-c','import socket;socket.socket()'],capture_output=True)
r['child']=p.returncode!=0 and b'PermissionError' in p.stderr
r['file_io']=bool(open('/etc/os-release').read())
print(json.dumps(r))'''
        result = subprocess.run([sys.executable,str(EXT/'no_network_exec.py'),sys.executable,'-c',code],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertTrue(all(json.loads(result.stdout).values()))

    def test_artifact_destinations_and_symlinks(self):
        obj=object.__new__(ScienceGuardedACK);obj._guarded_verifier=True
        workspace=Path(__file__).resolve().parents[3]
        with tempfile.TemporaryDirectory(dir=workspace/'.tmp') as temp:
            source=Path(temp);(source/'solver.py').write_text('pass\n')
            obj._check_upload(source,'/workspace/stacking_submission')
            for target in ['/root/.bashrc','/tests','/workspace/stacking_submission/../../etc','relative']:
                with self.subTest(target=target),self.assertRaises(ValueError):obj._check_upload(source,target)
            (source/'link').symlink_to('/etc/passwd')
            with self.assertRaises(ValueError):obj._check_upload(source,'/workspace/stacking_submission')

    def test_public_commands_unchanged_and_verifier_wrapped(self):
        async def capture(self,command,**kwargs):return command
        obj=object.__new__(ScienceGuardedACK);obj._guarded_verifier=True
        async def run():
            with patch.object(UniverseACK,'exec',capture):
                obj._network_policy=NetworkPolicy(network_mode=NetworkMode.PUBLIC)
                self.assertEqual(await obj.exec('echo public'),'echo public')
                obj._network_policy=NetworkPolicy(network_mode=NetworkMode.NO_NETWORK)
                command=await obj.exec('printf verifier-ok')
            result=subprocess.run(['/bin/sh','-c',command],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(result.stdout,'verifier-ok')
        asyncio.run(run())

if __name__=='__main__':unittest.main()
