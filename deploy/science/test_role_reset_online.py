import fcntl,json,os,subprocess,tempfile,threading,time,unittest
from pathlib import Path
from unittest.mock import patch
import role_reset as r

class OnlineResetTests(unittest.TestCase):
    def test_ack_requires_exact_nonce_role_controller_and_quiescent_fact(self):
        with tempfile.TemporaryDirectory(dir=r.W/'.tmp') as tmp:
            root=Path(tmp);(root/'operator-role-holds').mkdir();(root/'author-01').mkdir()
            (root/'operator-role-holds/author-01').write_text('n'*32)
            (root/'controller.pid').write_text('123')
            path=root/'author-01/operator-hold-ack.json'
            valid=dict(version=1,nonce='n'*32,role='author-01',controller_pid=123,quiescent=True)
            info=dict(pid=123,uid=os.getuid(),state='S',argv=[b'gewu-multiverse'],start_ticks=1)
            with patch.object(r,'DEPLOYMENT_STATE',root),patch.object(r,'identity',return_value=info):
                path.write_text(json.dumps(valid))
                self.assertEqual(r.verify_pause('author-01','n'*32,{'controller_uid':os.getuid()}),info)
                for change in [dict(nonce='old'),dict(role='author-02'),dict(controller_pid=124),dict(quiescent=False),dict(version=0)]:
                    path.write_text(json.dumps(dict(valid,**change)))
                    with self.assertRaises(RuntimeError):r.verify_pause('author-01','n'*32,{'controller_uid':os.getuid()})

    def test_timeout_keeps_hold_and_does_not_apply_reset(self):
        with tempfile.TemporaryDirectory(dir=r.W/'.tmp') as tmp:
            root=Path(tmp);(root/'role-broker').mkdir();(root/'role-broker/config.json').write_text(json.dumps({'controller_uid':os.getuid()}))
            with patch.object(r,'DEPLOYMENT_STATE',root),patch.object(r,'reset',return_value={}) as reset:
                with self.assertRaisesRegex(RuntimeError,'hold retained'):
                    r.online_reset('author-01','reason','pivot',True,wait_seconds=0)
                self.assertEqual(reset.call_count,1)
                marker=root/'operator-role-holds/author-01'
                self.assertEqual(len(marker.read_text()),32)
                with self.assertRaises(FileExistsError):r.online_reset('author-01','reason','pivot',True,wait_seconds=0)
                self.assertEqual(len(marker.read_text()),32)

    def test_online_protocol_with_real_identity_and_shared_launcher_lock(self):
        with tempfile.TemporaryDirectory(dir=r.W/'.tmp') as tmp:
            root=Path(tmp);(root/'role-broker').mkdir();(root/'role-reset').mkdir();(root/'author-01').mkdir()
            child=subprocess.Popen(['/bin/bash','-c','exec -a gewu-multiverse sleep 20'])
            try:
                (root/'controller.pid').write_text(str(child.pid))
                isolated=root/'isolated';isolated.mkdir();(isolated/'instruction.md').write_text('retain original policy')
                uid=400000+os.getpid()
                self.assertNotIn(uid,{p.stat().st_uid for p in Path('/proc').iterdir() if p.name.isdigit() and p.exists()})
                (root/'role-broker/config.json').write_text(json.dumps({'controller_uid':os.getuid(),'roles':{'author-01':{'uid':uid,'gid':uid,'root':str(isolated)}}}))
                other=root/'other-role-history';other.write_text('preserve')
                def controller():
                    marker=root/'operator-role-holds/author-01';deadline=time.monotonic()+5
                    while time.monotonic()<deadline:
                        if marker.exists() and len(marker.read_text())==32:
                            (root/'author-01/operator-hold-ack.json').write_text(json.dumps(dict(version=1,nonce=marker.read_text(),role='author-01',controller_pid=child.pid,quiescent=True)));return
                        time.sleep(.01)
                thread=threading.Thread(target=controller);thread.start()
                with (root/'role-reset/lifecycle.lock').open('a') as launcher:
                    fcntl.flock(launcher,fcntl.LOCK_SH|fcntl.LOCK_NB)
                    with patch.object(r,'DEPLOYMENT_STATE',root),patch.object(r,'U',root),patch.object(r,'reset',wraps=r.reset) as reset:
                        receipt=r.online_reset('author-01','reason','pivot',True,wait_seconds=5)
                    self.assertEqual(reset.call_count,2)
                    self.assertIn('_online_nonce',reset.call_args.kwargs)
                thread.join(timeout=5)
                self.assertTrue(receipt['hold_released'])
                self.assertFalse((root/'operator-role-holds/author-01').exists())
                self.assertIsNone(child.poll())
                self.assertEqual(other.read_text(),'preserve')
                self.assertEqual((root/'role-reset'/(receipt['reset_id']+'.json')).stat().st_mode&0o777,0o600)
                self.assertIn('retain original policy',(isolated/'instruction.md').read_text())
                self.assertIn('Operator reset: '+receipt['reset_id'],(isolated/'instruction.md').read_text())
            finally:child.terminate();child.wait(timeout=5)
