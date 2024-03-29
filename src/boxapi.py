import hexdump
import pprint
import json
from cmd import Cmd
import re
import src.core as Core
import os

# regex for matching arguments in an args string e.g. 
# '-P ~/Documents/Notes/note.txt -r -m' -> 
# [('-P', '~/Documents/Notes/note.txt')],['-r','-m']
args_re = re.compile(
        '((?:--|-)[\w\\\/\:\-]+(?: |=|$)(?:(?:[\"\'][^\"\']*[\"\'])|(?:[\w\\\/\.]+(?:-[\w\\\/\.\-\(\)]*)?))?)|'
        '(?:(?:[\"\'][\w\.\\\/\:\~\(\)\- ]+[\"\'])|(?:[\w\.\\\/\:\~\(\)\-]+))'
    )

#The core does the dirty work of connecting and keeping track of the state
core = Core.BoxCore()

#uses a regex to parse an argument string
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

    #For all matches
    for m in args_re.finditer(args):
        t = m.group(0)
        #if the match contains ' or "
        if('\'' in t or '\"' in t):
            if not t.startswith("-"):
                single.append(t[1:-1])
            elif('=' in t):
                #split at the first equals sign
                lval,rval = t.split('=',1)
                pairs[lval] = rval[1:-1]
            else:
                #split at the first space
                lval,rval = t.split(' ',1)
                pairs[lval] = rval[1:-1]
        else:
            #split at the first equals sign
            if('=' in t[:-1]):
                lval,rval = t.split('=',1)
                pairs[lval] = rval
            #split at the first space
            elif(' ' in t[:-1]):
                lval,rval = t.split(' ',1)
                pairs[lval] = rval
            #we have a single
            else:
                single.append(t)
    return (single, pairs)

#convert Xnix paths to your machine's path
def fixpath(path):
    return os.path.abspath(os.path.expanduser(path))


                                      #REPL#
#------------------------------------------------------------------------------#
class BoxRepl(Cmd):

    def __init__(self):
        super(BoxRepl, self).__init__()

#LOGIN
    def do_login(self, args):
        """
        NAME :
            login - login to your box account

        SYNOPSIS :
            login [options]
            login [-A auth_code] [options]

        DESCRIPTION :
            If not supplied with an <auth_code>, this will open up a browser
            window with a login form. The user will be redirected to a local
            webpage on a successful login.

            When supplied with an <auth_code> (usually the developer <auth_code>),
            this will open a browser window and instad simply log the user in.

        OPTIONS:
            -t  Use the tokens generated from the last sessoin. Refresh tokens
                last for 60 days so this should be valid for just as long.
                Logout wil invalidate these tokens.
        """
        arg,argkv = parse_args(args)


        if __debug__:
                if '-A' in argkv:
                    core.login(id=argkv['-A'])
                elif '-t' in arg:
                    core.login(token=True)
                else:
                    core.login()
            
        else:
            try:
                if '-A' in argkv:
                    core.login(id=argkv['-A'])
                elif '-t' in arg:
                    core.login(token=True)
                else:
                    core.login()
            except Exception as e:
                print(e)
                print("Could not login, token expired or invalid")

        

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
        
        if core.is_logged_in():
            if __debug__:
                user = core.uid()
                response = core.logout()
                print ("logging out {}...".format(user))
            else:
                try:
                    user = core.uid()
                    response = core.logout()
                    print ("logging out {}...".format(user))
                except Exception as e:
                    print(e)
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
        print(core.tokens())
        

#TEMPLATES
    def do_templates(self, args):
        """
        NAME:
            templates - the current enterprise level templates

        SYNOPSIS:
            templates

        DESCRIPTION:
            Shows the current templates by name and id

        OPTIONS:
            NONE
        """

        templates = core.templates()
        for template in templates:
            print("{} {}".format(templates[template], templates[template].displayName))
        

#TEMPLATEINFO
    def do_template(self, args):
        """ 
        NAME:
            template - info about a template

        SYNOPSIS:
            template [template_index] [options]
            template -n [template_name] [options]

        DESCRIPTION:
            Shows the template info for the specified template

        OPTIONS:
            -n  template_name, gets template by the name shown in the
                'templates' command.
            
            -v  show all information
        """
        
        arg,argkv = parse_args(args)
        template = None

        if __debug__:
            if '-n' in argkv: 
                template = core.template(argkv['-n'])
            elif len(arg) > 0: 
                template = core.template(arg[0])
            else:
                print("unrecognized arguments")
                return

        else:
            try:
                if '-n' in argkv: 
                    template = core.template(argkv['-n'])
                elif len(arg) > 0: 
                    template = core.template(arg[0])
                else:
                    print("unrecognized arguments")
                    return
            except Exception as e:
                print(e)
                return

        print("{} {}".format(template, template.displayName))

        if '-v' in arg:
            print(json.dumps(template.fields, indent=4)) 
        #skip unwanted information about each field
        else:
            string = json.dumps(template.fields, indent=4)
            for line in string.splitlines():
                if  line.lstrip().startswith('"') and \
                not line.lstrip().startswith('"key') and \
                not line.lstrip().startswith('"type') and \
                not line.lstrip().startswith('"displayName') and \
                not line.lstrip().startswith('"options'):
                    continue
                else:
                    print(line)
        

#TEMPLATE INFO AUTOCOMPLTE
    def complete_template(self, text, line, begidx, endidx):
        return [x for x in core.templates() if x.startswith(text)]

#METADATA
    def do_meta(self, args):
        """ 
        NAME:
            meta - the metadata on a specified file

        SYNOPSIS:
            meta [item_name] [options]

        DESCRIPTION:
            Shows the metadata of a file or folder specified by the user.

        OPTIONS:
            -v  show all information
        """
        arg,argkv = parse_args(args)
        data = None

        if __debug__:
            if len(arg) > 0:
                data = core.metadata(arg[0])
            else:
                print("name must be supplied")
                return

        else:
            try:
                if len(arg) > 0:
                    data = core.metadata(arg[0])
                else:
                    print("name must be supplied")
                    return
            except Exception as e:
                    print(e)
                    return

        #format data for printing
        for instance in data:
            print("template: {}".format(instance['$template']))
            #print verbose
            if '-v' in arg:
                print(json.dumps(instance, indent=4))
            #print clean
            else:
                string = json.dumps(instance, indent=4)
                for line in string.splitlines():
                    #ignore lines that start with $, they are extra information
                    if line.lstrip().startswith('"$'):
                        continue
                    else:
                        print("    {}".format(line))
            print('')        


#METADATA AUTOCOMPLTE
    def complete_meta(self, text, line, begidx, endidx):
        return [x for x in core.ls() if x.startswith(text)]


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

        if core.is_logged_in():
            if __debug__:
                user = core.uid()
                print(user)
            else:
                try:
                    user = core.uid()
                    print(user)
                except Exception as e:
                    print(e)
        else:
            print("not currently logged in")
        

#ITEMINFO
    def do_info(self, args):
        """
        NAME:
            info - show the info (not the content) of a item on Box

        SYNOPSIS:
            info file_name [options]

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
            print("filename must be supplied\n")
            return
        else:

            if __debug__:
                result = core.iteminfo(arg[0])
            else:
                try:
                    result = core.iteminfo(arg[0])
                except Exception as e:
                    print(e)
                    return

        printstr = "<Box {type} - {id} ({name})>".format(type=result.type.capitalize(),
                                                         id=result.id,
                                                         name=result.name)
        
        #print info specified by the flags
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
        

#ITEMINFO AUTOCOMPLTE
    def complete_info(self, text, line, begidx, endidx):
        return [x for x in core.ls() if x.startswith(text)]

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
            print('must specify a filename and a download location\n')
            return

        if __debug__:
            output_file = open(fixpath(arg[1]),'wb')
            result = core.download(arg[0], output_file)
            output_file.close()

        else:
            try:
                output_file = open(fixpath(arg[1]),'wb')
                result = core.download(arg[0], output_file)
                output_file.close()
            except Exception as e:
                print(e)


#DOWNLOAD AUTOCOMPLTE
    def complete_download(self, text, line, begidx, endidx):
        return [x for x in core._get_files_cached() if x.startswith(text)]
        
#UPLOAD
    def do_upload(self, args):
        """
        NAME:
            upload - upload content

        SYNOPSIS:
            upload [local_resource_path] [filename]

        DESCRIPTION:
            Uploads a file from your machine to the Box repository.

        OPTIONS:
        """
        arg,argkv = parse_args(args)
        result = None

        if len(arg) < 2:
            print('must specify a source and filename\n')
            return

        if __debug__:
            source_file = open(fixpath(arg[0]),'rb')
            result = core.upload(arg[1], source_file)
            source_file.close()

        else:
            try:
                source_file = open(fixpath(arg[0]),'rb')
                result = core.upload(arg[1], source_file)
                source_file.close()
            except Exception as e:
                print(e)

        
#LS
    def do_ls(self, args):
        """
        NAME:
            ls - list items in current directory

        SYNOPSIS:
            ls [options]

        DESCRIPTION:
            Lists all files available to you in your current directory

        OPTIONS:
            -f  Force the cache to update. Boxpy caches files after every
                traversal. If you think that files may have changed while you
                were in the directory, you can use this flag to ensure that the
                most recently available files are listed.
        """
        arg,argkv = parse_args(args)


        if __debug__:
            if '-f' in arg:
                items = core.ls(force=True)
                if len(items) > 0:
                    print(' | '.join(items))
            else:
                items = core.ls()
                if len(items) > 0:
                    print(' | '.join(items))

        else:
            try:
                if '-f' in arg:
                    items = core.ls(force=True)
                    if len(items) > 0:
                        print(' | '.join(items))
                else:
                    items = core.ls()
                    if len(items) > 0:
                        print(' | '.join(items))
            except Exception as e:
                print(e)

        
#PWD
    def do_pwd(self, args):
        """
        NAME:
            pwd - show your present working directory

        SYNOPSIS:
            pwd

        DESCRIPTION:
            Shows your present working directory

        OPTIONS:
        """

        arg,argkv = parse_args(args)


        if __debug__:
            print(core.pwd())
        else:
            try:
                print(core.pwd())
            except Exception as e:
                print(e)
        

#CD
    def do_cd(self, args):
        """
        NAME:
            cd - change directory

        SYNOPSIS:
            cd [dir]

        DESCRIPTION:
            Changes your present working directory to the one specified

        OPTIONS:
        """

        arg,argkv = parse_args(args)


        if __debug__:
            core.cd(arg[0])
        else:
            try:
                core.cd(arg[0])
            except Exception as e:
                print(e)
        
#CD AUTOCOMPLTE
    def complete_cd(self, text, line, begidx, endidx):
        return [x for x in core._get_folders_cached() if x.startswith(text)]

#MKDIR
    def do_mkdir(self, args):
        """
        NAME:
            mkdir - make a subdirectory

        SYNOPSIS:
            mkdir [dir]

        DESCRIPTION:
            Create a subdirectory in your present working directory

        OPTIONS:
        """

        arg, argkv = parse_args(args)

        if __debug__:
            core.mkdir(arg[0])
        else:
            try:
                core.mkdir(arg[0])
            except Exception as e:
                print(e)

#RM
    def do_rm(self, args):
        """
        NAME:
            rm - remove an item from the Box repository

        SYNOPSIS:
            rm [item] [options]

        DESCRIPTION:
            Removes an item (folder or file) from the Box repository.

        OPTIONS:
            -r  Recursively remove items from a directory. Required if a
                directory is not empty.
        """

        arg,argkv = parse_args(args)
        success = False
        name = ''

        if __debug__:
            if '-r' in arg:
                name = arg[0]
                success = core.rm(name,recursive=True)
            elif '-r' in argkv:
                name = argkv['-r']
                success = core.rm(name,recursive=True)
            elif len(arg) < 1:
                print("no item specified\n")
                return
            else:
                name = arg[0]
                success = core.rm(name)

        else:
            try:
                if '-r' in arg:
                    name = arg[0]
                    success = core.rm(name,recursive=True)
                elif '-r' in argkv:
                    name = argkv['-r']
                    success = core.rm(name,recursive=True)
                elif len(arg) < 1:
                    print("no item specified\n")
                    return
                else:
                    name = arg[0]
                    success = core.rm(name)
            except Exception as e:
                print(e)

        if not success:
            print("could not delete {}".format(name))
        
#RM AUTOCOMPLTE
    def complete_rm(self, text, line, begidx, endidx):
        return [x for x in core.ls() if x.startswith(text)]

#HEXDUMP
    def do_xxd(self, args):
        """
        NAME:
            xxd - print out a hexdump of the file specified

        SYNOPSIS:
            cat [file] 

        DESCRIPTION:
            Prints a hexdump of the specified file

        OPTIONS:
        """
        arg,argkv = parse_args(args)


        if __debug__:
            hexdump.hexdump(core.cat(arg[0]))
        else:
            try:
                hexdump.hexdump(core.cat(arg[0]))
            except Exception as e:
                print(e)

#AUTOCOMPLETE HEXDUMP
    def complete_xxd(self, text, line, begidx, endidx):
        return [x for x in core._get_files_cached() if x.startswith(text)]
    
#CAT
    def do_cat(self, args):
        """
        NAME:
            cat - print out the file specified

        SYNOPSIS:
            cat [file] [options]

        DESCRIPTION:
            Prints the file specified. Uses UTF-8 encoding.

        OPTIONS:
            -d Decode type, how should cat decode the string.
               By default this is 'utf-8'.
                 > utf-8
                 > ascii
        """
        arg,argkv = parse_args(args)


        if __debug__:
            if '-d' in argkv and argkv['-d'] == 'ascii':
                print(core.cat(arg[0]).decode('ascii'))
            elif ('-d' in argkv and argkv['d'] == 'utf-8') or '-d' not in argkv:
                print(core.cat(arg[0]).decode('utf-8'))
        else:
            try:
                if '-d' in argkv and argkv['-d'] == 'ascii':
                    print(core.cat(arg[0]).decode('ascii'))
                elif ('-d' in argkv and argkv['d'] == 'utf-8') or '-d' not in argkv:
                    print(core.cat(arg[0]).decode('utf-8'))
            except Exception as e:
                print(e)

#CAT AUTOCOMPLTE
    def complete_cat(self, text, line, begidx, endidx):
        return [x for x in core._get_files_cached() if x.startswith(text)]

#MANUAL
    def do_man(self, args):
        """
        NAME:
            man - show help documentation for a given command

        SYNOPSIS:
            cat [command] 

        DESCRIPTION:
            An alias for 'help'

        OPTIONS:
        """ 
        self.do_help(args)

#QUIT
    def do_quit(self, args):
        raise SystemExit

#Only runs if this is the main, change boxpy.py to affect these values
if __name__ == '__main__':

    repl = BoxRepl()
    repl.prompt = '\nboxpy> '
    repl.cmdloop('Starting prompt...')

