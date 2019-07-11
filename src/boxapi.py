from cmd import Cmd
import re
import src.core as core
import os


args_re = re.compile('((?:--|-)[\w\\\/\:\-]+(?: |=|$)(?:(?:[\"\'][^\"\']*[\"\'])|(?:[\w\\\/\.]+(?:-[\w\\\/\.\-\(\)]*)?))?)|((?:[\w\.\\\/\:\~\(\)\-]+)|(?:"[\w\.\\\/\:\~]+"))')
col = '|  '
e_tab = '=--'
c_tab = '+--'
tree_buffer = [['' for x in range (512)] for y in range(2048)]

def parse_args(args):
    """
    Parse command line arguments e.g. 'login -A <token>'

    :param args: the argument string
    :type args: string
    :return: arguments paired up with thier key or just arguments paired with an
    int to count them
    :rtype: dict
    """
    single      = []
    pairs       = {}

    for m in args_re.finditer(args):
        t = m.group(0)
        if('\'' in t or '\"' in t):
            if('=' in t):
                lval,rval = t.split('=',1)
                pairs[lval] = rval[1:-1]
            else:
                lval,rval = t.split(' ',1)
                pairs[lval] = rval[1:-1]
        else:
            if('=' in t[:-1]):
                lval,rval = t.split('=',1)
                pairs[lval] = rval
            elif(' ' in t[:-1]):
                lval,rval = t.split(' ',1)
                pairs[lval] = rval
            else:
                single.append(t)

    return (single, pairs)

def fixpath(path):
    path = os.path.normpath(os.path.expanduser(path))
    if path.startswith("\\"): return "C:" + path
    return path

                                      #REPL#
#------------------------------------------------------------------------------#
class BoxRepl(Cmd):

    def __init__(self):
        super(BoxRepl, self).__init__()

        self.core = core.BoxCore()


#LOGIN
    def do_login(self, args):
        """
        NAME :
            login - login to your box account

        SYNOPSIS :
            login
            login [-A auth_code]

        DESCRIPTION :
            If not supplied with an <auth_code>, this will open up a browser
            window with a login form. The user will be redirected to a local
            webpage on a successful login.

            When supplied with an <auth_code> (usually the developer <auth_code>),
            this will open a browser window and instad simply log the user in.

        OPTIONS:
            NONE
        """
        arg,argkv = parse_args(args)

        try:

            if '-A' in argkv:
                self.core.login(id=argkv['-A'])
            else:
                self.core.login()

        except Exception as e:
            print("Could not login:",e)

#LOGOUT
    def do_logout(self, args):
        """
        NAME:
            logout - revoke credentials for your current session

        SYNOPSIS:
            logout

        DESCRIPTION:
            Tells the Box OAuth service that you are done using the current
            <access_token> and <refresh_token>. Logging out will invalidate the
            current session. If you want to do more after logging out, you have
            to log back in. This is useful if your refresh token has expired
            somehow and you need to re-authenticate without closing the command
            line.

        OPTIONS:
            NONE
        """

        if self.core.is_logged_in():
            try:
                user = self.core.uid()
                response = self.core.logout()
                print(response)
                print ("logging out {}...".format(user))
            except Exception as e:
                print("Exception : \n", e)
        else:
            print("user already logged out")

#TOKENS
    def do_tokens(self, args):
        """
        NAME:
            tokens - the currently stored tokens

        SYNOPSIS:
            tokens

        DESCRIPTION:
            Shows the current tokens

        OPTIONS:
            NONE
        """
        print(self.core.tokens())

#UID
    def do_uid(self, args):
        """
        NAME:
            uid - who is currently logged in

        SYNOPSIS:
            uid

        DESCRIPTION:
            Shows the user id and name of the currently logged in user.

        OPTIONS:
            NONE
        """
        if self.core.is_logged_in():
            try:
                user = self.core.uid()
                print(user)
            except Exception as e:
                print("Error getting client: \n",e)
        else:
            print("not currently logged in")

#ITEMINFO
    def do_iteminfo(self, args):
        """
        NAME:
            iteminfo - show the info (not the content) of a item on Box

        SYNOPSIS:
            iteminfo file_name [options]

        DESCRIPTION:
            Displays information on a item. This is NOT the content of the item,
            but information that Box provides about the item.

        OPTIONS:

            -V  Verbose, show all

            -d  Show description

            -h  Show sha1 hash

            -o  Show owner

            -p  Show parent

            -s  Show size

            -t  Show status

            -v  Show version
        """
        arg,argkv = parse_args(args)
        result = None

        if len(arg) == 0:
            print("filename must be supplied")
        else:
            try:
                result = self.core.iteminfo(arg[0])
            except Exception as e:
                print("error: {}".format(e))
                return
        

        printstr = "<Box {type} - {id} ({name})>".format(type=result.type.capitalize(),
                                                         id=result.id,
                                                         name=result.name)

        if '-d' in arg or '-V' in arg:
            printstr += "\n    :description: {}".format(result.description)
        if ('-h' in arg or '-V' in arg) and result.type=='file':
            printstr += "\n    :sha1: {}".format(result.sha1)
        if ('-o' in arg or '-V' in arg) and result.type=='file':
            printstr += "\n    :owner: {}".format(result.owned_by)
        if ('-p' in arg or '-V' in arg) and result.parent is not None:
            printstr += "\n    :parent: <Box {type} - {id} ({name})>".format(type=result.parent.type.capitalize(),
                                                                          id=result.parent.id,
                                                                          name=result.parent.name)
        if '-s' in arg or '-V' in arg:
            printstr += "\n    :size: {}".format(result.size)
        if '-t' in arg or '-V' in arg:
            printstr += "\n    :status: {}".format(result.item_status)
        if ('-v' in arg or '-V' in arg) and result.type=='file':
            printstr += "\n    :status: {}".format(result.file_version)

        print(printstr)

#DOWNLOAD
    def do_download(self, args):
        """
        NAME:
            download - download the content of a box file

        SYNOPSIS:
            download [filename] [local_path]

        DESCRIPTION:
            Downloads the content of a Box file to the specified location on
            your machine

        OPTIONS:
        """
        arg,argkv = parse_args(args)
        result = None

        if len(arg) < 2:
            print('must specify a filename and a download location')
            return

        try:
            output_file = open(fixpath(arg[1]),'wb')
            result = self.core.download(arg[0], output_file)
            output_file.close()
        except Exception as e:
            print(e)
            return
            
#UPLOAD
    def do_upload(self, args):
        """
        NAME:
            download - download the content of a box file

        SYNOPSIS:
            download [local_resource_path] [filename]

        DESCRIPTION:
            Uploads a file from your machine to the Box repository.

        OPTIONS:
        """
        arg,argkv = parse_args(args)
        result = None

        if len(arg) < 2:
            print('must specify a source and filename')
            return

        try:
            source_file = open(fixpath(arg[0]),'rb')
            result = self.core.upload(arg[1], source_file)
            source_file.close()
        except Exception as e:
            print(e)
            return
            
#LS
    def do_ls(self, args):
        arg,argkv = parse_args(args)
        if '-f' in arg:
            print(' | '.join(self.core.ls(force=True)))
        else:
            print(' | '.join(self.core.ls()))
#CD 
    def do_cd(self, args):
        arg,argkv = parse_args(args)
        
        self.core.cd(arg[0])
        pass
        
#MKDIR
    def do_mkdir(self, args):
        arg, argkv = parse_args(args)
        
        self.core.mkdir(arg[0])
       
#RM
    def do_rm(self, args):
        arg,argkv = parse_args(args)
        success = False
        name = ''
        if '-r' in arg:
            name = arg[0]
            success = self.core.rm(name,recursive=True)
        elif '-r' in argkv:
            name = argkv['-r']
            success = self.core.rm(name,recursive=True)
        elif len(arg) < 1:
            print("no item specified")
            return
        else:
            name = arg[0]
            success = self.core.rm(name)
            
        if not success:
            print("could not delete {}".format(name))
            
#CAT
    def do_cat(self, args):
        arg,argkv = parse_args(args)
        
        print(self.core.cat(arg[0]))
#QUIT
    def do_quit(self, *args):
        self.core.logout()
        raise SystemExit

if __name__ == '__main__':

    repl = BoxRepl()
    repl.prompt = '> '
    repl.cmdloop('Starting prompt...')

#OLD TEST CODE
#auth = OAuth2(
#    client_id='ba6xqqqso7wauppnvtixr258oemo1cnk',
#    client_secret='jB1t76Q4WlnRL8ETYwI2gc2Doa90Rrkm',
#    access_token='ilbWsFamFkv0MvC1YPhiMW60b3MkY7sM',
#)
#
#client = Client(auth)
#
#user = client.user().get()
#print('The current user ID is {0}'.format(user.id))
#
#json_response = client.make_request(
#    'GET',
#    client.get_url('metadata_templates', 'enterprise'),
#).json()
#
#print(json_response)
