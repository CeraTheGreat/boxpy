from boxsdk import OAuth2
from http.server import HTTPServer, BaseHTTPRequestHandler
import webbrowser
import requests
import json
from urllib.parse import urlparse
from urllib.parse import parse_qs

auth_code = None


class BoxOAuth:
    def __init__(self):

        #json
        cred_file = open('cred/cred.json',"r")
        cred_json = json.load(cred_file)

        #client & websocket
        self.client_id = cred_json['client_id']
        self.client_secret = cred_json['client_secret']
        self.redirect_port = 55655
        self.redirect_uri = 'http://localhost:{}/'.format(self.redirect_port)

        #oauth
        self.oauth = None
        self.auth_url = None
        self.csrf_token = None
        self.token_dict = {'access_token':'','refresh_token':''}

    #when new tokens are generated, this should be run
    def _store_tokens(self, access_token, refresh_token):
        #write tokens to cred
        token_json = open('cred/tokens.json','w+')
        self.token_dict['access_token'] = access_token
        self.token_dict['refresh_token'] = refresh_token
        json.dump(self.token_dict, token_json)
        token_json.close()

    def logout(self):
        return self.oauth.revoke() 

    #Token login, uses tokens saved between sessions
    def token_login(self):
        with open('cred/tokens.json') as tokenfile:

            token_json = json.load(tokenfile)

            self.oauth = OAuth2(
              client_id=self.client_id,
              client_secret=self.client_secret,
              access_token=token_json['access_token'],
              refresh_token=['refresh_token'],
              store_tokens=self._store_tokens
            )

            self.token_dict['access_token'] = token_json['access_token']
            self.token_dict['refresh_token'] = token_json['refresh_token']

    #Developer login, must use developer token generated from the
    def dev_login(self, token):
        #Box application administration page.

        #    :param token: the developer token
        #    :type token: string

        self.oauth = OAuth2(
            client_id=self.client_id,
            client_secret=self.client_secret,
            access_token=token
        )

    # User login, uses OAuth2
    def user_login(self):
        #auth_code is a global variable set by the server when it exits
        global auth_code

        #setup a local server to catch the redirected OAuth2 login 
        #https://tools.ietf.org/html/rfc6749#section-3.1.2
        httpd = StoppableHttpServer((
                                      'localhost',
                                      self.redirect_port
                                    ),
                                    HTTPLoopbackHandler
                                   )

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
    #http server that reacts to self.stop flag
    stop = False

    def serve_forever (self):
        #Handle one request at a time until stopped.
        while not self.stop:
            self.handle_request()


class HTTPLoopbackHandler(BaseHTTPRequestHandler):
    #http handler that reacts to self.stop flag
    stop = False
    allow_reuse_address = True

    def serve_forever(self):
        #Handle one request at a time until stopped.
        while not self.stop:
            self.handle_request()

    def force_stop(self):
        #forcibly close the server
        self.server.server_close()
        self.stop = True
        self.server.stop = True
        self.server.serve_forever()

    def do_GET(self):
        #GET is the ONLY http verb that we support
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
