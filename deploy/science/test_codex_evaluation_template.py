import unittest
from codex_evaluation_template import prepare
from acs_helpers.run_guard import check_config


class TemplateTests(unittest.TestCase):
    def test_current_profile_replaces_legacy_limits_and_passes_guard(self):
        base=dict(environment=dict(type='ack',kwargs=dict(namespace='default',kubeconfig='/unused',
             image_manifest='/old',override_cpus=2)),agents=[dict(kwargs={'max_steps':40})],export_traces=True)
        receipt=dict(harness='codex',published=True,harness_versions={'codex':'0.164.0'},
                     images={k:{'published_digest':'registry/project/'+k+'@sha256:'+'a'*64} for k in ['runtime','verifier']})
        c=prepare(base,receipt)
        a=c['agents'][0];kw=c['environment']['kwargs']
        self.assertEqual(a['override_timeout_sec'],14400)
        self.assertNotIn('max_steps',a['kwargs']);self.assertNotIn('image_manifest',kw)
        self.assertEqual(a['env']['OPENAI_API_KEY'],'${OPENAI_API_KEY}')
        self.assertEqual(a['env']['CODEX_MODEL_PROVIDER'],'dawnfm')
        self.assertEqual(c['environment']['override_cpus'],4)
        self.assertEqual(c['environment']['override_memory_mb'],8192)
        self.assertNotIn('export_traces',c)
        c['job_name']='tbs-universe-linfeng-queue-'+'f'*32
        kw['pod_overrides']['metadata']['labels']['evaluation-run']=c['job_name']
        check_config(c)
        self.assertEqual(base['agents'][0]['kwargs']['max_steps'],40)


if __name__=='__main__':unittest.main()
