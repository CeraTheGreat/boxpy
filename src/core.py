from boxsdk import Client
from urllib.parse import urlparse
from urllib.parse import parse_qs
from pythonping import ping
import src.oauth as oauth



                              #CORE#
#------------------------------------------------------------------------------#
class BoxCore:

    #initializatoins
    def __init__(self):
        self.current_path = [('/',0)]

        self.current_files = {}
        self.current_folders = {}
        self.current_templates = {}

        self.client = None

        self.authenticator = oauth.BoxOAuth()
                            #Private Functions#
#------------------------------------------------------------------------------#
    def _init_filestruct(self):
        self._get_children(self.current_path[-1][1])
        self._get_enterprise_templates()

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

    def _download_file_to_stream(self, file_id, dest_stream):
        return self.client.file(str(file_id)).download_to(dest_stream)

    def _download_file(self, file_id):
        return self.client.file(str(file_id)).content()

    def _upload_file(self, dest_folder_id, file_name, file_stream):
        new_file = self.client.folder(str(dest_folder_id)).upload_stream( \
                                                           file_stream,
                                                           file_name)
        self.current_files[new_file.name] = new_file.id
        return new_file

    def _delete_folder(self, folder_id, recursive=False):
        return self.client.folder(str(folder_id)).delete(recursive=recursive)

    def _delete_file(self, file_id):
        return self.client.file(str(file_id)).delete()

    def _new_folder(self, parent_id, name):
        new_folder = self.client.folder(parent_id).create_subfolder(name)
        self.current_folders[new_folder.name] = new_folder.id
        return new_folder

    def _token_login(self):
        """
        Token login, uses tokens saved between sessions
        """

        self.authenticator.token_login()
        self.client = Client(self.authenticator.oauth)
        self._init_filestruct()

    def _dev_login(self, token):
        """
        Developer login, must use developer token generated from the
        Box application administration page.

            :param token: the developer token
            :type token: string
        """
        self.authenticator.dev_login(token)
        self.client = Client(self.authenticator.oauth)
        self._init_filestruct()

    #Log a regular user in
    def _user_login(self):
        """
        User login, uses OAuth2
        """
        self.authenticator.user_login()
        self.client = Client(self.authenticator.oauth)
        self._init_filestruct()

    #Get enterprise level templates
    def _get_enterprise_templates(self):
        templates = self.client.get_metadata_templates()
        for template in templates:
            self.current_templates[template.id] = template
        return templates

        # TODO : 
        #   Need to impliment metadata
        #   Metadata needs several things:
        #       >View it on the command line
        #       >Map values for upload
        #       >Store existing templates
        #       >Create a template
        #       >

    
    def _get_enterprise_templates_cached(self):
        return self.current_templates
#------------------------------------------------------------------------------#
                         #Public helper functions#
#------------------------------------------------------------------------------#
    def is_logged_in(self):
        return True if self.client is not None else False

#------------------------------------------------------------------------------#
                              #REPL commands#
#------------------------------------------------------------------------------#
#LOGIN
    def login(self, id=None, token=False):
        if id is not None:
            self._dev_login(id)
        elif token:
            self._token_login()
        else:
            self._user_login()

#LOGOUT
    def logout(self):
        self.authenticator.logout()

#TOKENS
    def tokens(self):
        return(self.authenticator.token_dict)

#TEMPLATES
    def templates(self):
        return(self._get_enterprise_templates_cached())

#TEMPLATE
    def template(self, selector, method):
        if method == 'id':
            return self.current_templates[selector]
        elif method == 'index':
            return [self.current_templates[x] for x in self.current_templates][selector]
        else:
            raise Exception("method {} not recognized".format(method))

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
#PWD
    def pwd(self):
        return '/'+'/'.join([x[0] for x in self.current_path[1:]])
#CD
    def cd(self, foldername):
        if foldername in self.current_folders:

            self.current_path.append((foldername,self.current_folders[foldername]))
            self._get_children(self.current_path[-1][1])

        elif foldername == '..' and self.current_path[-1][1] != 0:

            del self.current_path[-1]
            self._get_children(self.current_path[-1][1])

        elif foldername in self.current_files:
            raise Exception("not a folder")

        elif foldername == '..' and self.current_path[-1][1] == 0:
            raise Exception("already at root")

        else:
            raise Exception("folder not found")

#DOWNLOAD
    def download(self, filename, dest_stream):
        if filename in self.current_files:
            return self._download_file_to_stream(self.current_files[filename],
                                                 dest_stream)
        else:
            raise Exception("file not found")

#UPLOAD
    def upload(self, filename, source_stream):
        return self._upload_file(self.current_path[-1][1], 
                                 filename, 
                                 source_stream)

#RM
    def rm(self, name, recursive=False):
        if name in self.current_folders:
            succ = self._delete_folder(self.current_folders[name], 
                                       recursive=recursive)
            if succ:
                del self.current_folders[name]
            return succ
        elif name in self.current_files:
            succ = self._delete_file(self.current_files[name])
            if succ:
                del self.current_files[name]
            return succ
        else:
            raise Exception("file not found")

#MKDIR
    def mkdir(self, name):
        return self._new_folder(self.current_path[-1][1], name)

#CAT
    def cat(self, name):
        if name in self.current_files:
            return self._download_file(self.current_files[name]).decode("utf-8")
#------------------------------------------------------------------------------#
