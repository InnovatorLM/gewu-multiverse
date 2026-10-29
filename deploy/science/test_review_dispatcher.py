import unittest
from review_dispatcher import fingerprint
class WakeTests(unittest.TestCase):
    def test_self_comments_do_not_wake(self):
        pr={'head':{'sha':'abc'}}
        own={'id':1,'updated_at':'now','user':{'login':'gewu-evaluator-01'}}
        self.assertEqual(fingerprint(pr,[]),fingerprint(pr,[own]))
        author={'id':2,'updated_at':'now','user':{'login':'gewu-author-10'}}
        self.assertNotEqual(fingerprint(pr,[]),fingerprint(pr,[author]))
        self.assertNotEqual(fingerprint(pr,[]),fingerprint({'head':{'sha':'def'}},[]))

class FakeApi:
    def __init__(self):
        self.pulls=[{'number':30,'title':'Candidate','body':'tasks/science/example','head':{'sha':'abc'}}]
        self.comments=[];self.issues=[]
    def pages(self,path):
        if path.startswith('/pulls'):return self.pulls
        if '/comments' in path:return self.comments
        return self.issues
    def call(self,method,path,data=None):
        if '/contents/' in path:return [{'name':'tests','sha':'tree-id','type':'dir'}]
        if method=='POST':
            issue=dict(data,number=len(self.issues)+1,state='open');self.issues.append(issue);return issue
        number=int(path.rsplit('/',1)[1]);issue=self.issues[number-1]
        if method=='PATCH':issue.update(data)
        return issue

class DispatchTests(unittest.TestCase):
    def test_exclusive_wait_resume_and_revision(self):
        import tempfile,json,os
        from pathlib import Path
        import review_dispatcher as m
        with tempfile.TemporaryDirectory(dir=m.W/'.tmp') as d:
            original=m.STATE;m.STATE=Path(d)/'control';m.STATE.mkdir()
            try:
                cfg={'roles':{}}
                for role in ['evaluator-01','evaluator-02']:
                    root=Path(d)/role;(root/'home/role').mkdir(parents=True)
                    cfg['roles'][role]={'root':str(root),'uid':os.getuid(),'gid':os.getgid()}
                api=FakeApi();ledger={}
                m.reconcile(api,cfg,ledger);m.reconcile(api,cfg,ledger)
                self.assertEqual(len(api.issues),1)
                row=ledger['30:abc'];self.assertEqual(row['role'],'evaluator-01')
                receipt=Path(cfg['roles'][row['role']]['root'])/'home/role/review-status.json'
                receipt.write_text(json.dumps({'key':'30:abc','generation':0,'state':'waiting_author','stage':'completeness'}))
                m.reconcile(api,cfg,ledger);self.assertEqual(api.issues[0]['state'],'closed')
                api.comments=[{'id':1,'updated_at':'now','user':{'login':'gewu-evaluator-01'}}]
                m.reconcile(api,cfg,ledger);self.assertEqual(len(api.issues),1)
                api.comments.append({'id':2,'updated_at':'later','user':{'login':'gewu-author-10'}})
                m.reconcile(api,cfg,ledger);self.assertEqual(len(api.issues),2);self.assertEqual(row['generation'],1)
                api.pulls[0]['head']['sha']='def';m.reconcile(api,cfg,ledger)
                self.assertNotIn('30:def',ledger) # No simultaneous revision ownership.
            finally:m.STATE=original
