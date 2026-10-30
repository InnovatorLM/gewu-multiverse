import tempfile,unittest
from pathlib import Path
from dockerfile_bases import pin_bases
from evaluation_queue import W
class BaseTests(unittest.TestCase):
 def test_preserves_multistage_platform_and_unrelated_instructions(self):
  with tempfile.TemporaryDirectory(dir=W/'.tmp') as raw:
   path=Path(raw)/'Dockerfile';nl=chr(10);path.write_text(nl.join(['FROM --platform=linux/amd64 python:3.13-slim AS build','RUN echo python:3.13-slim','FROM build AS final','COPY --from=build /x /y','']))
   digest='docker.io/library/python@sha256:'+'a'*64
   mapping=pin_bases(path,'unused',lambda image:digest)
   self.assertEqual(mapping,[{'source':'python:3.13-slim','resolved':digest}])
   self.assertIn('FROM build AS final',path.read_text());self.assertIn('RUN echo python:3.13-slim',path.read_text());self.assertIn('--platform=linux/amd64 '+digest,path.read_text())
 def test_unresolved_build_argument_refused(self):
  with tempfile.TemporaryDirectory(dir=W/'.tmp') as raw:
   path=Path(raw)/'Dockerfile';path.write_text('FROM $BASE'+chr(10))
   with self.assertRaises(ValueError):pin_bases(path,'unused',lambda _:self.fail('unresolved'))
if __name__=='__main__':unittest.main()
