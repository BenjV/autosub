#################################################################################################################
# History:                                                                                                      #
# First developed by zyronix to work with the website "Bierdopje"                                               #
# After the ending of Bierdopje collincab took over and change it to use subtitleseeker instead of Bierdopje.   #
# Donny stepped in a added the bootstrap user interface an the support for mobile devices and notifications.    #
# Later collincab added support for the website Addic7ed                                                        #
# First collingcab and later Donny abbanded the project and Benj took over the support.                         #
# He added support for the Opensubtitles API, the TVDB API v2 and numerous other options                        #
#################################################################################################################

help_message = '''
Usage:
    -h (--help)     Prints this message
    -c (--config=)  Forces AutoSub.py to use a configfile other than ./config.properties, the database will be put in the same folder
    -d (--daemon)   Run AutoSub in the background
    -l (--nolaunch) Stop AutoSub from launching a webbrowser
    
Example:
    python AutoSub.py
    python AutoSub.py -d
    python AutoSub.py -d -l
    python AutoSub.py -c/home/user/config.properties
    python AutoSub.py -c/home/user
    python AutoSub.py --config=/home/user/config.properties
    python AutoSub.py --config=/home/user/config.properties --daemon
    
'''
class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg

def signal_handler(signum, frame):
    import autosub.Scheduler
    autosub.Scheduler.stop(signum)

def _daemon():
    import os,sys

    try:
        if os.fork() > 0:
            sys.exit(0)
    except OSError:
        sys.exit(1)
    os.chdir("/")
    os.setsid()
    os.umask(0)
    try:
        if os.fork() > 0:
            sys.exit(0)
    except OSError:
        sys.exit(1)
    sys.stdin.close()
    Fpnull = open(os.devnull, 'w')
    sys.stdout = Fpnull
    sys.stderr = Fpnull

def main(argv=None):
    import sys
    from os import getcwd
    #version_info,platform
    from getopt import getopt
    
    if sys.version_info[0] != 2 or sys.version_info[1] < 7:
        raise SystemExit('Unsupported python version (should be 2.7.xx)')
    try:
        opts,args = getopt(sys.argv[1:], "hc:dlu", ["help","config=","daemon","nolaunch"])
    except Exception as error:
        raise SystemExit(error.message)
    # option processing
    LaunchBrowser = True
    Cwd = getcwd()
    for option, value in opts:
        print value
        if option in ("-h", "--help"):
            raise Usage(help_message)
        if option in ("-d", "--daemon"):
            if sys.platform == "win32":
                raise SystemExit('ERROR: No support for daemon mode in Windows. Use pythonw instead.')
            else:
                _daemon()
        if option in ("-c", "--config"):
            WriteConf = value
        if option in ("-l", "--nolaunch"):
            LaunchBrowser = False

        # Here we do the import no need to do it before if we deamonizing
    import autosub
    import autosub.Scheduler
    from locale import setlocale,getpreferredencoding,LC_ALL
    from os import getcwd, getpid, path,chdir,remove
    from signal import signal, SIGTERM
    from time import time
    from distutils.dir_util import remove_tree
    try:
        setlocale(LC_ALL, '')
        autosub.SYSENCODING = getpreferredencoding()
    except:
        pass
    # for OSes that are poorly configured, like synology & slackware
    if not autosub.SYSENCODING or autosub.SYSENCODING in ('ANSI_X3.4-1968', 'US-ASCII', 'ASCII'):
        autosub.SYSENCODING = 'UTF-8'
        # if we deamonise we lost the working directory so we set it back
    chdir(Cwd)
    autosub.PATH = unicode(Cwd, autosub.SYSENCODING)
    #    # First we write the pidfile to the autosub folder
    try:
        autosub.PID = str(getpid())
        with open(path.join(autosub.PATH,'autosub.pid') , "w") as fp:
            fp.write(autosub.PID + '\n')
    except Exception as error:
        raise SystemExit(error.message)
        # remove old folders and files
    Items = ['interface/media','autosub/AutoSub.py','autosub/AutoSub.pyc']
    for Item in Items:
        Item = path.normpath(path.join(autosub.PATH,Item))
        try:
            remove(Item)
        except OSError:
            if path.exists(Item):
                try:
                    remove_tree(Item)
                except Exception as error:
                    log.error(error.message)
        except:
            pass

    autosub.LASTRUN = autosub.STARTTIME = time() 
    autosub.LAUNCHBROWSER = LaunchBrowser
        # setup de signal handler for Termination with a SIGTERM signal
    signal(SIGTERM, signal_handler)
        # Here we start the scheduler to periodically run the checksub routine
    autosub.Scheduler.start()

if __name__ == "__main__":
    exit(main())