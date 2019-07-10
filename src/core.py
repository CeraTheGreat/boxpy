from boxsdk import Client, OAuth2
from http.server import HTTPServer, BaseHTTPRequestHandler
import webbrowser
from urllib.parse import urlparse
from urllib.parse import parse_qs
from pythonping import ping
import requests

auth_code = None

class StoppableHttpServer (HTTPServer):
    """http server that reacts to self.stop flag"""
    stop = False

    def serve_forever (self):
        """Handle one request at a time until stopped."""
        while not self.stop:
            self.handle_request()

class HTTPLoopbackHandler(BaseHTTPRequestHandler):

        stop = False
        allow_reuse_address = True

        def serve_forever(self):
            while not self.stop:
                self.handle_request()

        def force_stop(self):
            self.server.server_close()
            self.stop = True
            self.server.stop = True
            self.server.serve_forever()

        def do_GET(self):
            global auth_code

            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'Login Successful!')

            auth_code = parse_qs(urlparse(self.path).query)

            self.force_stop()

        def log_message(self, format, *args):
            pass


                                  #CORE#
#------------------------------------------------------------------------------#
class BoxCore:

    #initializatoins
    def __init__(self):
        self.client = None

        self.client_id = 'ba6xqqqso7wauppnvtixr258oemo1cnk'
        self.client_secret ='jB1t76Q4WlnRL8ETYwI2gc2Doa90Rrkm'
        self.redirect_port = 55655
        self.redirect_uri = 'http://localhost:{}/'.format(self.redirect_port)

        self.oauth = None
        self.auth_url = None
        self.csrf_token = None
        self.token_dict = {'access_token':'','refresh_token':''}

    #internal private functions
    def _store_tokens(self, access_token, refresh_token):
        self.token_dict['access_token'],self.token_dict['refresh_token'] = access_token,refresh_token

    def _get_children(self, folder_id):
        folder_info = self._get_folder(folder_id).json
        return folder_info['item_collection']['entries']

    #item_id: string, type: ['unknown','folder','file']
    def _get_iteminfo(self, item_id, type='unknown'):
        if type is 'unknown':
            item_info = None

            try:
                item_info = _get_folder(item_id)
            except Exception as e:
                try:
                 item_info = _get_file(item_id)
                except Exception as e:
                    raise Exception("Item not found")

        elif type is 'folder':
            return self._get_folder(item_id)

        elif type is 'file':
            return self._get_file(item_id)

    #Get folder by id
    def _get_folder(self, folder_id):
        return self.client.folder(folder_id).get()

    #Get file by id
    def _get_file(self, file_id):
        return self.client.file(file_id).get()

    #Log dev user in with token
    def _dev_login(self, token):
        self.oauth = OAuth2(
            client_id=self.client_id,
            client_secret=self.client_secret,
            access_token=token
        )
        self.client = Client(self.oauth)

    #Log a regular user in
    def _user_login(self):
        global auth_code

        httpd = StoppableHttpServer(('localhost', self.redirect_port),
            HTTPLoopbackHandler)



        self.oauth = OAuth2(
            client_id=self.client_id,
            client_secret=self.client_secret,
            store_tokens=self._store_tokens
        )
        self.auth_url, self.csrf_token = self.oauth.get_authorization_url(self.redirect_uri)

        webbrowser.open_new_tab(self.auth_url)

        httpd.serve_forever()
        if auth_code is None:
            raise Exception("Localhost unable to retrieve auth code")
        if 'state' not in auth_code:
            raise Exception("Invalid URL")

        csrf_token = auth_code['state'][0]

        try:
            assert csrf_token == self.csrf_token
        except AssertionError:
            raise Exception(("Login session changed",(csrf_token,self.csrf_token)))

        self.oauth.authenticate(auth_code['code'])
        self.client = Client(self.oauth)

    #public functions
    def is_logged_in(self):
        return True if self.client is not None else False

    #REPL links
#LOGIN
    def login(self, id=None):
        if id is not None:
            self._dev_login(id)
        else:
            self._user_login()

#LOGOUT
    def logout(self):
        data = {"client_id":self.client_id,"client_secret":self.client_secret,"token":self.token_dict['refresh_token'],"token":self.token_dict['access_token']}
        return requests.post('https://api.box.com/oauth2/revoke', json=data)

#TOKENS
    def tokens(self):
        return(self.token_dict)

#UID
    def uid(self):
        return self.client.user().get()

#ITEMINFO
    def iteminfo(self, args):
        pass

#TREE
    def tree(self, args):
        pass

#CHILDREN
    def children(self, args):
        pass

#FINDITEM
    def finditem(self, selector, method='id'):
        if method is 'id':
            return self.client.file(selector).get()
        else:
            pass

