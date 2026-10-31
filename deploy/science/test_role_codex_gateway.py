import json
import unittest
from role_codex_gateway import MODEL, MAX_BODY, validate_request

class GatewayTests(unittest.TestCase):
    def test_designated_responses_request(self):
        payload={'model':MODEL,'input':'mock input','stream':True}
        self.assertEqual(validate_request('/v1/responses',json.dumps(payload).encode()),payload)

    def test_other_routes_models_and_background_refused(self):
        for path, payload in [('/v1/chat/completions',{'model':MODEL}),
                              ('/v1/responses',{'model':'other'}),
                              ('/v1/responses',{'model':MODEL,'background':True}),
                              ('/v1/responses',[])]:
            with self.assertRaises(ValueError):
                validate_request(path,json.dumps(payload).encode())

    def test_invalid_and_large_bodies_refused(self):
        for body in [b'{',b'x'*(MAX_BODY+1)]:
            with self.assertRaises(ValueError):validate_request('/v1/responses',body)

if __name__=='__main__':unittest.main()

class GatewayTransportTests(unittest.TestCase):
    def test_trusted_credential_replaces_client_header(self):
        import http.server
        import threading
        import urllib.request
        from role_codex_gateway import handler_type
        calls=[]
        class Response:
            status_code=200
            def iter_content(self,chunk_size):return iter([b'event: response.completed'])
            def close(self):pass
        def forward(url,**kwargs):
            calls.append((url,kwargs));return Response()
        server=http.server.ThreadingHTTPServer(('127.0.0.1',0),handler_type('mock-upstream-secret',forward,access_token='role-placeholder'))
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            request=urllib.request.Request('http://127.0.0.1:'+str(server.server_address[1])+'/v1/responses',
                data=json.dumps({'model':MODEL,'input':'mock','stream':True}).encode(),
                headers={'Authorization':'Bearer role-placeholder'},method='POST')
            with urllib.request.urlopen(request,timeout=5) as response:body=response.read()
            self.assertIn(b'response.completed',body)
            self.assertNotIn(b'mock-upstream-secret',body)
            self.assertEqual(calls[0][1]['headers'],{'Authorization':'Bearer mock-upstream-secret'})
            self.assertEqual(calls[0][0],'https://dawnfm.gravarc.cn/v1/responses')
            self.assertFalse(calls[0][1]['allow_redirects'])
        finally:
            server.shutdown();server.server_close();thread.join(timeout=5)

class GatewayAuthorizationTests(unittest.TestCase):
    def test_missing_token_never_calls_upstream(self):
        import http.server
        import threading
        import urllib.request
        import urllib.error
        from role_codex_gateway import handler_type
        def forward(*args,**kwargs):raise AssertionError('Unauthorized upstream call')
        server=http.server.ThreadingHTTPServer(('127.0.0.1',0),handler_type('mock-key',forward,access_token='required-token'))
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            request=urllib.request.Request('http://127.0.0.1:'+str(server.server_address[1])+'/v1/responses',
                data=json.dumps({'model':MODEL}).encode(),method='POST')
            with self.assertRaises(urllib.error.HTTPError) as caught:
                urllib.request.urlopen(request,timeout=5)
            self.assertEqual(caught.exception.code,401)
        finally:
            server.shutdown();server.server_close();thread.join(timeout=5)
