import os,tempfile,unittest
from pathlib import Path
from selftest_logs import sanitize,publish
from evaluation_queue import W

class LogTests(unittest.TestCase):
    def test_secrets_removed_without_hiding_failure(self):
        text='password=visible Bearer value\nraw exact-secret\nTraceback: missing dependency'
        result=sanitize(text,['exact-secret'])
        for secret in ['visible','Bearer value','exact-secret']:self.assertNotIn(secret,result)
        self.assertIn('missing dependency',result)

    def test_bounded_author_log_preserves_operator_original(self):
        with tempfile.TemporaryDirectory(dir=W/'.tmp') as raw:
            root=Path(raw);work=root/'work';work.mkdir();(root/'selftest/results').mkdir(parents=True)
            original='x'*20000+'\nsecret-value failure';(work/'build.log').write_text(original)
            path=publish(work,root,'a'*32,os.getgid(),['secret-value'])
            content=(root/path.lstrip('/')).read_text()
            self.assertLess(len(content),17000);self.assertNotIn('secret-value',content)
            self.assertIn('failure',content);self.assertEqual((work/'build.log').read_text(),original)
            self.assertEqual((root/path.lstrip('/')).stat().st_mode&0o777,0o640)

if __name__=='__main__':unittest.main()
