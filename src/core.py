from boxsdk import Client, OAuth2
from http.server import HTTPServer, BaseHTTPRequestHandler
import webbrowser
from urllib.parse import urlparse
from urllib.parse import parse_qs
from pythonping import ping
import requests

auth_code = None

                                #POPUP SERVER#
#------------------------------------------------------------------------------#
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


                              #CORE#
#------------------------------------------------------------------------------#
class BoxCore:

    #initializatoins
    def __init__(self):
        self.current_path = [('/',0)]

        self.current_files = {}
        self.current_folders = {}
        
        self.client = None

        self.client_id = 'ba6xqqqso7wauppnvtixr258oemo1cnk'
        self.client_secret ='jB1t76Q4WlnRL8ETYwI2gc2Doa90Rrkm'
        self.redirect_port = 55655
        self.redirect_uri = 'http://localhost:{}/'.format(self.redirect_port)

        self.oauth = None
        self.auth_url = None
        self.csrf_token = None
        self.token_dict = {'access_token':'','refresh_token':''}

                            #Private Functions#
#------------------------------------------------------------------------------#

    def _store_tokens(self, access_token, refresh_token):
        self.token_dict['access_token'],self.token_dict['refresh_token'] = access_token,refresh_token

    def _get_children(self, folder_id):
        """ :param folder_id: the id of the folder in the box repository
            :type folder_id: string
            :return: the sparse children of the flie
            :rtype: json object
        """
        folder_info = self._get_folder(folder_id)
        children = folder_info.item_collection['entries']
        
        
        self.current_files = {}
        self.current_folders = {}
        for child in children:
                if child.type == 'folder':
                    self.current_folders[child.name] = child.id
                else:
                    self.current_files[child.name] = child.id
        
        return folder_info.item_collection['entries']
        
    def _get_children_cached(self):
        """ :param folder_id: the id of the folder in the box repository
            :type folder_id: string
            :return: the sparse children of the file
            :rtype: array
        """
        return [x for x in self.current_folders]+[x for x in self.current_files]

    #item_id: string, type: ['unknown','folder','file']
    def _get_iteminfo(self, name, type='unknown'):
        """ :param item_id: the id of the item in the box repository
            :param type: the type of the item - 'file', 'folder', 'unknown'
            :type item_id: string
            :type type: string
            :return: the full info on the specified item
            :rtype: json object
        """
        if name in self.current_files:
            return self._get_file(self.current_files[name])
        elif name in self.current_folders:
            return self._get_folder(self.current_folders[name])
        else:
            raise Exception("file not found")

    #Get folder by id
    def _get_folder(self, folder_id):
        return self.client.folder(str(folder_id)).get()

    #Get file by id
    def _get_file(self, file_id):
        return self.client.file(str(file_id)).get()

    def _download_file(self, file_id, dest_stream):
        return self.client.file(str(file_id)).download_to(dest_stream)
        
    def _upload_file(self, dest_folder_id, source_path):
        new_file = self.client.folder(dest_folder_id).upload(source_path)
        return new_file

    #Log dev user in with token
    def _dev_login(self, token):
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
        self.client = Client(self.oauth)
        self._get_children(self.current_path[-1][1]) 

    #Log a regular user in
    def _user_login(self):
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
        self.client = Client(self.oauth)
        self._get_children(self.current_path[-1][1]) 

            
#------------------------------------------------------------------------------#
                         #Public helper functions#
#------------------------------------------------------------------------------#
    def is_logged_in(self):
        return True if self.client is not None else False
        
#------------------------------------------------------------------------------#
                              #REPL commands#
#------------------------------------------------------------------------------#
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
    def iteminfo(self, name):
        return self._get_iteminfo(name)
        
#LS
    def ls(self, force=False):
        if force:
            return [x.name for x in self._get_children(self.current_path[-1][1])]
        else:
            return self._get_children_cached()
        
#CD
    def cd(self, foldername):
        if foldername in self.current_folders:
        
            self.current_path.append((foldername,self.current_folders[foldername]))
            self._get_children(self.current_path[-1][1])           
                    
        elif foldername == '..' and self.current_path[-1][1] != 0:
        
            del self.current_path[-1]          
            self._get_children(self.current_path[-1][1])

        else:
            raise Exception("folder not found")
            
#DOWNLOAD
    def download(self, filename, dest_stream):
        if filename in self.current_files:
            return self._download_file(self.current_files[filename], dest_stream)
        else:
            raise Exception("file not found")

#------------------------------------------------------------------------------#
