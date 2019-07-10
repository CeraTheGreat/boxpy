from cmd import Cmd
import re
import src.core as core


args_val = re.compile('(?:--|-)\w+(?: |=|$)(?:(?:[\"\'][^\"\']*[\"\'])|(?:\w+))?')
def parse_args(args):
    single      = 0
    pairs       = {}

    for m in args_val.finditer(args):
        t = m.group(0)
        if('\'' in t or '\"' in t):
            if('=' in t):
                lval,rval = t.split('=',1)
                pairs[lval] = rval
            else:
                lval,rval = t.split(' ',1)
                pairs[lval] = rval
        else:
            if('=' in t[:-1]):
                lval,rval = t.split('=',1)
                pairs[lval] = rval
            elif(' ' in t[:-1]):
                lval,rval = t.split(' ',1)
                pairs[lval] = rval
            else:
                pairs[single] = t
                single += 1

    return pairs

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
        argv = parse_args(args)

        try:

            if '-A' in argv:
                self.core.login(id=argv['-A'])
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
            iteminfo [-P file_path]
            iteminfo [-I file_id]

        DESCRIPTION:
            Displays information on a item. This is NOT the content of the item,
            but information that Box provides about the item.

        OPTIONS:
            The -P and -I options specify unique locations in the box repository.
            To see the item structure of your Box repository, use `tree`.

            -P  Use a filepath to specify a item. e.g. '/a/b/fileorfolder'

            -I  Use an ID to specify and item. e.g. '12345...'
        """
        pass

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
        pass

#QUIT
    def do_quit(self, args):
        self.core.logout()
        raise SystemExit

if __name__ == '__main__':

    repl = BoxRepl()
    repl.prompt = '> '
    repl.cmdloop('Starting prompt...')





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
