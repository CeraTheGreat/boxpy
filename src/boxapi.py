from cmd import Cmd
import re
import src.core as core


args_re = re.compile('(?:--|-)[\w-]+(?: |=|$)(?:(?:[\"\'][^\"\']*[\"\'])|(?:[\w\\\/\.]+(?:-[\w\\\/\.]*)?))?')
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
            iteminfo [-P file_path] [options]
            iteminfo [-I file_id] [options]

        DESCRIPTION:
            Displays information on a item. This is NOT the content of the item,
            but information that Box provides about the item.

        OPTIONS:
            The -P and -I options specify unique locations in the box repository.
            To see the item structure of your Box repository, use `tree`.

            -P  Use a filepath to specify a item. e.g. '/a/b/fileorfolder'

            -I  Use an ID to specify and item. e.g. '12345...'
            
            -d  Show description
            
            -h  Show sha1 hash
            
            -o  Show owner
            
            -p  Show parent
            
            -s  Show size
            
            -t  Show status
            
            -v  Verbose show all
        """
        arg,argkp = parse_args(args)
        result = None
                
        if '-I' in argkp:
            result = self.core.iteminfo(argkp['-I'], 'id')
            
            
        elif '-P' in argkp:
            result = self.core.iteminfo(argkp['-P'], 'path')
        else:
            print('unrecognized flag')
            return
        
        printstr = "<Box {type} - {id} ({name})>".format(type=result.type.capitalize(),
                                                         id=result.id,
                                                         name=result.name)
        
        if '-d' in arg or '-v' in arg:
            printstr += "\n    :description: {}".format(result.description)
        if '-h' in arg or '-v' in arg and result.type=='file':
            printstr += "\n    :sha1: {}".format(result.sha1)
        if '-o' in arg or '-v' in arg and result.type=='file':
            printstr += "\n    :owner: {}".format(result.owner)  
        if '-p' in arg or '-v' in arg:
            printstr += "\n    :parent: <Box {type} - {id} ({name})>".format(type=result.parent.type.capitalize(),
                                                                          id=result.parent.id,
                                                                          name=result.parent.name)                                                                                 
        if '-s' in arg or '-v' in arg:
            printstr += "\n    :size: {}".format(result.size)
        if '-t' in arg or '-v' in arg:
            printstr += "\n    :status: {}".format(result.item_status)
        
        print(printstr)   
        
#TREE
    def do_tree(self, args):
        """
        NAME:
            tree - show the tree structure on a Box repository

        SYNOPSIS:
            tree
            tree [-I root_id] [-D depth] [Options]

        DESCRIPTION
            Displays a tree structure representative of the file-strcture in
            the current box repository. '+' indicates children within a folder.
            '=' indicates no childrein within a folder. You can begin the tree
            at any file and end it at any depth. By default <root_id> = '0' and
            <depth> = 0.

            By default the tree command will only display the names of items
            found in it's search. This can be changed with flags like -i
            (which include the file id in the results) or -s (which shows the
            size of the file as reported by Box).

            Ex:

            > tree -I '0' -D 3

            'All Files'
            +--'folder1'
            |
            +--'folder2'
            |  |
            |  +--'subfolder1'
            |  |  |
            |  |  =--'nochildren'
            |  |
            |  +--'subfolder2'
            |
            +--'folder3'


            > tree -D 3 -i -s

            'All Files'
            | :id:0001
            | :size:2500
            |
            +--'folder1'
            |    :id:0002
            |    :size:1000
            |
            +--'folder2'
            |  | :id:0003
            |  | :size:500
            |  |
            |  +--'subfolder1'
            |  |  | :id:0004
            |  |  | :size:250
            |  |  |
            |  |  =--'nochildren'
            |  |       :id:0005
            |  |       :size:0
            |  |
            |  +--'subfolder2'
            |       :id:0006
            |       :size:250
            |
            +--'folder3'
                 :id:0007
                 :size:1000

        OPTIONS:
            The -I and -D options are entirely optional, but allow the user more
            control over what they see. Keeping the terminal from becoming too
            messy.

            -I  Specify a <root_id> which will be the start of the traversal.
                This defaults to '0', the root folder for your Box repository.

            -D  Specify a maximum depth to search to. A depth of 0 indicates no
                depth limit.

            -V  Verbose. Enable all data flags: -i, -s, -v.

            -i  Show the id of items in the tree.

            -s  Show the size of items in the tree.

            -v  Show the version number (if available) of items in tree.

            -l  display information inline rather than on separate lines.

            -d  Show document items alongside file items.
        """
        pass

#CHILDREN
    def do_children(self, args):
        """
        NAME:
            children - show the chlidren of a Box Folder

        SYNOPSIS:
            children [-P file_path] [options]
            children [-I file_id] [options]

        DESCRIPTION:
            Displays the children of a Box Folder

        OPTIONS:
            The -P and -I options specify unique locations in the box repository.
            To see the item structure of your Box repository, use `tree`.

            -P  Use a filepath to specify a item. e.g. '/a/b/fileorfolder'

            -I  Use an ID to specify and item. e.g. '12345...'
            
            -d  Show description
            
            -h  Show sha1 hash
            
            -o  Show owner
            
            -p  Show parent
            
            -s  Show size
            
            -t  Show status
            
            -v  Verbose show all
        """
    
        arg,argkp = parse_args(args)
        result = None
                
        if '-I' in argkp:
            result = self.core.iteminfo(argkp['-I'], 'id') 
        elif '-P' in argkp:
            result = self.core.iteminfo(argkp['-P'], 'path')
        else:
            print('unrecognized flag')
            return
        
        
        printstr = "<Box {type} - {id} ({name})>".format(type=result.type.capitalize(),
                                                         id=result.id,
                                                         name=result.name)
        
        if result.type != 'folder':
            print('item {} was not folder', printstr)
            return
        
        children = result.item_collection['entries']
           
        if '-d' in arg or '-v' in arg:
            printstr += "\n    :description: {}".format(result.description)
        if '-h' in arg or '-v' in arg and result.type=='file':
            printstr += "\n    :sha1: {}".format(result.sha1)
        if '-o' in arg or '-v' in arg and result.type=='file':
            printstr += "\n    :owner: {}".format(result.owned_by)  
        if '-p' in arg or '-v' in arg and result.parent is not None:
            printstr += "\n    :parent: <Box {type} - {id} ({name})>".format(type=result.parent.type.capitalize(),
                                                                          id=result.parent.id,
                                                                          name=result.parent.name)                                                                                 
        if '-s' in arg or '-v' in arg:
            printstr += "\n    :size: {}".format(result.size)
        if '-t' in arg or '-v' in arg:
            printstr += "\n    :status: {}".format(result.item_status)
        
        print(printstr)

        for mini_child in children:

            child = self.core.iteminfo(mini_child.id, method='id', type=mini_child.type)
            
            child_printstr = "    <Box {type} - {id} ({name})>".format(type=child.type.capitalize(),
                                                             id=child.id,
                                                             name=child.name)

            if '-d' in arg or '-v' in arg:
                child_printstr += "\n        :description: {}".format(child.description)
            if '-h' in arg or '-v' in arg and child.type=='file':
                child_printstr += "\n        :sha1: {}".format(child.sha1)
            if '-o' in arg or '-v' in arg and child.type=='file':
                child_printstr += "\n        :owner: {}".format(child.owned_by)  
            if '-p' in arg or '-v' in arg:
                child_printstr += "\n        :parent: <Box {type} - {id} ({name})>".format(type=child.parent.type.capitalize(),
                                                                              id=child.parent.id,
                                                                              name=child.parent.name)                                                                                 
            if '-s' in arg or '-v' in arg:
                child_printstr += "\n        :size: {}".format(child.size)
            if '-t' in arg or '-v' in arg:
                child_printstr += "\n        :status: {}".format(child.item_status)
            
            print(child_printstr)
        
        
        
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
