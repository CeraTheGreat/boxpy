from boxsdk import OAuth2
from http.server import HTTPServer, BaseHTTPRequestHandler
import webbrowser
import requests

auth_code = None

class BoxOAuth:
    def __init__(self):
    
        self.client_id = 'ba6xqqqso7wauppnvtixr258oemo1cnk'
        self.client_secret ='jB1t76Q4WlnRL8ETYwI2gc2Doa90Rrkm'
        self.redirect_port = 55655
        self.redirect_uri = 'http://localhost:{}/'.format(self.redirect_port)

        self.oauth = None
        self.auth_url = None
        self.csrf_token = None
        self.token_dict = {'access_token':'','refresh_token':''}

    def _store_tokens(self, access_token, refresh_token):
        self.token_dict['access_token'],self.token_dict['refresh_token'] = access_token,refresh_token
        
    def logout(self):
        data = {"client_id":self.client_id,"client_secret":self.client_secret,"token":self.token_dict['refresh_token'],"token":self.token_dict['access_token']}
        return requests.post('https://api.box.com/oauth2/revoke', json=data)    
        
    def dev_login(self, token):
        """
        Developer login, must use developer token generated from the
        Box application administration page.
        
            :param token: the developer token
            :type token: string
        """
        self.oauth = OAuth2(
            client_id=self.client_id,
            client_secret=self.client_secret,
            access_token=token
        )
        
    def user_login(self):
        """
        User login, uses OAuth2
        """
        
        #auth_code is a global variable set by the server when it exits
        global auth_code

        #setup a local server to catch the redirected OAuth2 login : https://tools.ietf.org/html/rfc6749#section-3.1.2
        httpd = StoppableHttpServer(('localhost', self.redirect_port),
            HTTPLoopbackHandler)

        self.oauth = OAuth2(
            client_id=self.client_id,
            client_secret=self.client_secret,
            store_tokens=self._store_tokens
        )
        self.auth_url, self.csrf_token = self.oauth.get_authorization_url(self.redirect_uri)

        #give the user a login prompt in thier default browser
        webbrowser.open_new_tab(self.auth_url)

        #wait for the redirect
        httpd.serve_forever()
        
        if auth_code is None:
            raise Exception("local server unable to retrieve auth code")
        if 'state' not in auth_code:
            raise Exception("Invalid URL")

        csrf_token = auth_code['state'][0]
        
        #double check that we have the right session
        try:
            assert csrf_token == self.csrf_token
        except AssertionError:
            raise Exception(("Login session changed",(csrf_token,self.csrf_token)))

        #do authentication
        self.oauth.authenticate(auth_code['code'])

class StoppableHttpServer (HTTPServer):
    """http server that reacts to self.stop flag"""
    stop = False

    def serve_forever (self):
        """Handle one request at a time until stopped."""
        while not self.stop:
            self.handle_request()

class HTTPLoopbackHandler(BaseHTTPRequestHandler):
    """http handler that reacts to self.stop flag"""
    stop = False
    allow_reuse_address = True

    def serve_forever(self):
        """Handle one request at a time until stopped."""
        while not self.stop:
            self.handle_request()

    def force_stop(self):
        """forcibly close the server"""
        self.server.server_close()
        self.stop = True
        self.server.stop = True
        self.server.serve_forever()

    def do_GET(self):
        """GET is the ONLY http verb that we support"""
        global auth_code

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Login Successful!')

        auth_code = parse_qs(urlparse(self.path).query)
        
        #kill this server after we respond to this
        self.force_stop()

    def log_message(self, format, *args):
        #we don't care about log messages
        pass

