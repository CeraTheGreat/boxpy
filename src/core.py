from boxsdk import Client
from urllib.parse import urlparse
from urllib.parse import parse_qs
from pythonping import ping
import src.oauth as oauth
import src.fs as filesystem


                              #CORE#
#------------------------------------------------------------------------------#
class BoxCore:

    #initializatoins
    def __init__(self):
        self.fs = filesystem.FileSystem('/',0)
#        self.current_path = [('/',0)]
#        self.current_files = {}
#        self.current_folders = {}
        self.current_templates = {}
        self.enterprise_templates = {}
        self.client = None
        self.authenticator = oauth.BoxOAuth()
                            
    def _init_filestruct(self):
        self._get_children()
        self._get_enterprise_templates()

                            #Private Functions#
#------------------------------------------------------------------------------#

    def _get_children(self):
        """ :param folder_id: the id of the folder in the box repository
            :type folder_id: string
            :return: the sparse children of the flie
            :rtype: json object
        """
        folder_info = self._get_folder(self.fs.pwd().id)
        children = folder_info.item_collection['entries']
        self.fs.pwd().files = {}
        self.fs.pwd().folders= {}
        
        #self.current_files = {}
        #self.current_folders = {}

        for child in children:
                if child.type == 'folder':
                    self.fs.add_folder(child.name, child.id)
                else:
                    self.fs.add_file(child.name, child.id)
        return folder_info.item_collection['entries']

    def _get_folders_cached(self):
        """ :return: the sparse folders of the current directory 
            :rtype: array
        """
        return self.fs.folders()

    def _get_files_cached(self):
        """ :return: the sparse files of the currend directory
            :rtype: array
        """
        return self.fs.files()

    def _get_children_cached(self):
        """ :param folder_id: the id of the folder in the box repository
            :type folder_id: string
            :return: the sparse children of the file
            :rtype: array
        """
        return self.fs.children()

    #item_id: string, type: ['unknown','folder','file']
    def _get_iteminfo(self, name):
        """ :param name: the name of the item in the box repository
            :param type: the type of the item - 'file', 'folder', 'unknown'
            :return: the full info on the specified item
            :rtype: json object
        """
        #If name is a file
        if self.fs.is_file(name):
            return self._get_file(self.fs.get_item(name).id)
        #If name is a folder
        elif self.fs.is_folder(name):
            return self._get_folder(self.fs.get_item(name).id)
        else:
            raise Exception("file not found")

    def _get_metadata(self, name):
        """ :param item_id: the id of the item in the box repository
            :param type: the type of the item - 'file', 'folder', 'unknown'
            :return: the full info on the specified item
            :rtype: json object
        """
        #If name is a file
        if self.fs.is_file(name):
            return self._get_file_meta(self.fs.get_item(name).id)
        #If name is a folder
        elif self.fs.is_folder(name):
            return self._get_folder_meta(self.fs.get_item(name).id)
        else:
            raise Exception("file not found")

    #Get folder by id
    def _get_folder(self, folder_id):
        return self.client.folder(str(folder_id)).get()

    #Get file by id
    def _get_file(self, file_id):
        return self.client.file(str(file_id)).get()
    
    #Get flie metadata
    def _get_file_meta(self, file_id):
        return self.client.file(str(file_id)).get_all_metadata()

    #Get folder metadata
    def _get_folder_meta(self, folder_id):
        return self.client.folder(str(folder_id)).get_all_metadata()
    
    #Get file stream (to save to system)
    def _download_file_to_stream(self, file_id, dest_stream):
        return self.client.file(str(file_id)).download_to(dest_stream)

    #Get file (saved to memory for program use)
    def _download_file(self, file_id):
        return self.client.file(str(file_id)).content()

    #Send byte stream to specified folder
    def _upload_file(self, dest_folder_id, file_name, file_stream):
        new_file = self.client.folder(str(dest_folder_id)).upload_stream( \
                                                           file_stream,
                                                           file_name)
        self.fs.add_file(new_file.name, new_file.id)
        return new_file

    #Remove a folder
    def _delete_folder(self, folder_id, recursive=False):
        return self.client.folder(str(folder_id)).delete(recursive=recursive)

    #Remove a file
    def _delete_file(self, file_id):
        return self.client.file(str(file_id)).delete()

    #Create a folder
    def _new_folder(self, parent_id, name):
        #upload
        new_folder = self.client.folder(parent_id).create_subfolder(name)
        #add to local cache
        self.fs.add_folder(new_folder.name, new_folder.id)
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
            self.enterprise_templates[template.displayName] = template
        return templates

        # TODO : 
        #   Need to impliment metadata
        #   Metadata needs several things:
        #       >Map values for upload
        #       >Create a template

    def _get_enterprise_templates_cached(self):
        return self.enterprise_templates
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
    def template(self, name):
        return self.enterprise_templates[name]

#METADATA
    def metadata(self, name):
        return self._get_metadata(name)

#UID
    def uid(self):
        return self.client.user().get()

#ITEMINFO
    def iteminfo(self, name):
        return self._get_iteminfo(name)

#LS
    def ls(self, force=False):
        if force:
            return [x.name for x in self._get_children()]
        else:
            return self._get_children_cached()
#PWD
    def pwd(self):
        return self.fs.path()
#CD
    def cd(self, path):
        self.fs.traverse(path)
        self._get_children()
        ##folder exists
        #if foldername in self.current_folders:
        #    self.current_path.append((foldername,self.current_folders[foldername]))
        #    self._get_children(self.current_path[-1][1])
        ##return to parent if not at root
        #elif foldername == '..' and self.current_path[-1][1] != 0:
        #    del self.current_path[-1]
        #    self._get_children(self.current_path[-1][1])
        ##folder is actually a flie
        #elif foldername in self.current_files:
        #    raise Exception("not a folder")
        ##at root, can't go any further
        #elif foldername == '..' and self.current_path[-1][1] == 0:
        #    return
        ##folder does not exist
        #else:
        #    raise Exception("folder not found")

#DOWNLOAD
    def download(self, filename, dest_stream):
        if self.fs.is_file(filename):
            return self._download_file_to_stream(self.fs.get_item(filename).id,
                                                 dest_stream)
        else:
            raise Exception("file not found")

#UPLOAD
    def upload(self, filename, source_stream):
        return self._upload_file(self.fs.pwd().id, 
                                 filename, 
                                 source_stream)

#RM
    def rm(self, name, recursive=False):
        #if name is folder
        if self.fs.is_folder(name):
            succ = self._delete_folder(self.fs.get_item(name).id, 
                                       recursive=recursive)
            if succ:
                self.fs.pwd().del_folder(name)
            return succ
        #if name is file
        elif self.fs.is_file(name):
            succ = self._delete_file(self.fs.get_item(name).id)
            if succ:
                self.fs.pwd().del_file(name)
            return succ
        #name does not exist
        else:
            print(name)
            raise Exception("file not found")

#MKDIR
    def mkdir(self, name):
        return self._new_folder(self.fs.pwd().id, name)

#CAT
    def cat(self, name):
        if self.fs.is_file(name):
            return self._download_file(self.fs.get_item(name).id)
#------------------------------------------------------------------------------#
