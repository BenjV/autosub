#################################################################################################################
# History:                                                                                                      #
# First developed by zyronix to work with the website "Bierdopje"                                               #
# After the ending of Bierdopje collincab took over and change it to use subtitleseeker instead of Bierdopje.   #
# Donny stepped in a added the bootstrap user interface an the support for mobil devices and notifications.     #
# Later collincab added support for the website Addic7ed                                                        #
# First collingcab and later Donny abbanded the project and Benj took over the support.                         #
# He added support for the Opensubtitles API, the TVDB API v2 and numerous other options                        #
#################################################################################################################
import sys,os
# Root path
base_path = os.path.dirname(os.path.abspath(__file__))

# Insert local directories into path
sys.path.insert(0, os.path.join(base_path, 'library'))


from getopt import getopt
from time import sleep
import locale,json
from codecs import open as CodecsOpen
import platform
from uuid import getnode
import requests
from requests.packages import chardet
from xmlrpclib import Server as xmlRpcServer 
import autosub
import autosub.version as Versions
from autosub.Config import ReadConfig
from autosub.Db import initDb as InitDatabase
from autosub.AutoSub import start
import logging.handlers
from autosub.Helpers import CheckVersion
from sys import version_info


def _Initialize():
    if version_info[0] != 2 or version_info[1] < 7:
        print 'Unsupported python version (should be 2.7.xx)'
        sys.exit(1)
    try:
        locale.setlocale(locale.LC_ALL, "")
        autosub.SYSENCODING = locale.getpreferredencoding()
    except:
        pass
        # for OSes that are poorly configured, like slackware
    if not autosub.SYSENCODING:
        autosub.SYSENCODING = 'UTF-8'
    autosub.PATH = unicode(os.getcwd(), autosub.SYSENCODING)
    autosub.PID = str(os.getpid())
    try:
        with open(os.path.join(autosub.PATH,'autosub.pid') , "w", 0) as pidfile:
            pidfile.write(autosub.PID + '\n')
    except Exception as error:
        print error
        sys.exit(1)

        # if config folder not set by commandline make it the default location
    if not autosub.CONFIGPATH:
        autosub.CONFIGPATH = autosub.PATH
    if not os.path.exists(autosub.CONFIGPATH):
        try:
            os.makedirs(autosub.CONFIGPATH)
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                print 'Cannot create configfolder.' + exception.message
                sys.exit(1)
    autosub.CONFIGFILE = os.path.join(autosub.CONFIGPATH, autosub.CONFIGNAME)
    if not os.path.isfile(autosub.CONFIGFILE):
        try:
            open(autosub.CONFIGFILE,'w').close()
        except Exception as error:
            print error
            sys.exit(1)


    if not autosub.CONFIGPATH:
        autosub.CONFIGPATH = autosub.PATH
        autosub.CONFIGFILE = os.path.join(autosub.CONFIGPATH, autosub.CONFIGNAME)
    else:
        if not os.path.exists(autosub.CONFIGPATH):
            print "Config path does not exist so creating it"
            try: 
                os.makedirs(autosub.CONFIGPATH)
            except Exception as error:
                print error
                print 'Using default location for config files'
                autosub.CONFIGPATH = autosub.PATH
            ConfigFile = os.path.join(autosub.CONFIGPATH,autosub.CONFIGNAME)
            if not os.path.isfile(ConfigFile):
                try:
                    open(ConfigFile,'w').close()
                except Exception as error:
                    print error
                    sys.exit(1)
    #if not os.access(autosub.CONFIGPATH, os.W_OK):

    print "AutoSub: Initializing variables and loading config"
    autosub.Config.ReadConfig()
    if 'Alpha' in Versions.autosubversion:
        release = Versions.autosubversion.split(' ')[0]
        versionnumber = Versions.autosubversion.split(' ')[1]
    else:
        versionnumber = autosub.version.autosubversion
    autosub.VERSION = int(versionnumber.split('.')[0]) * 1000 + int(versionnumber.split('.')[1]) * 100 + int(versionnumber.split('.')[2]) * 1
    autosub.OPENSUBTITLESUSERAGENT += versionnumber
    autosub.CERTIFICATEPATH = os.path.normpath(autosub.PATH +'/library/requests/cacert.pem')
    autosub.OPENSUBTITLESSERVER = xmlRpcServer(autosub.OPENSUBTITLESURL)
    autosub.TVDBSESSION = requests.Session()
    autosub.TVDBSESSION.headers.update({'Accept': 'application/json','Content-Type': 'application/json'})
    autosub.DBFILE = os.path.join(autosub.CONFIGPATH, autosub.DBFILE)
    autosub.A7MAPFILE = os.path.join(autosub.CONFIGPATH,'AddicMapping.json')
    autosub.RLSGRPFILE = os.path.join(autosub.CONFIGPATH,'ReleaseGroups.txt')
    autosub.NODE_ID = getnode()
    # check the logfile location and make it the default if neccessary

    if not autosub.LOGFILE:
        LogFile = u"AutoSubService.log"
        LogPath = autosub.CONFIGPATH
    else:
        LogPath,LogFile = os.path.split(autosub.LOGFILE)
    if not os.path.exists(LogPath):
        try:
            os.makedirs(LogPath)
        except Exception as error:
            print "Could not create log folder, fallback to default"
            LogPath = autosub.PATH
    if not os.access(LogPath, os.W_OK):
        print "No write access to: ", LogPath
        sys.exit()
    autosub.LOGFILE = os.path.join(LogPath,LogFile)

    return


def _initLogging():  
    # initialize logging
    # A log directory has to be created in the start directory
    print "AutoSub: Starting output to log. Bye!"
    Format = '%(asctime)s %(levelname)-3s %(funcName)-12s:%(message)s'
    try:
        fmt = logging.Formatter(Format,datefmt='%d-%m %H:%M:%S')
        logging.addLevelName(10,'DBG')
        logging.addLevelName(20,'INF')
        logging.addLevelName(30,'WRN')
        logging.addLevelName(40,'ERR')
        logging.addLevelName(50,'CRI')
        log = logging.getLogger("thelogger")   
        log.setLevel(autosub.LOGLEVEL)
        autosub.LOGHANDLER = logging.handlers.RotatingFileHandler(autosub.LOGFILE, 'a', autosub.LOGSIZE, autosub.LOGNUM)
        autosub.LOGHANDLER.setFormatter(fmt)
        autosub.LOGHANDLER.setLevel(autosub.LOGLEVEL)
        log.addHandler(autosub.LOGHANDLER)
    except Exception as error:
        log.error('Problem Initialising the logger. %s' % error)
        sys.exit()
        #CONSOLE log handler
    try:
        autosub.CONSOLE = logging.StreamHandler()
        autosub.CONSOLE.setLevel(autosub.LOGLEVELCONSOLE)
        autosub.CONSOLE.setFormatter(fmt)
        log.addHandler(autosub.CONSOLE)
    except Exception as error:
        log.error('Problem Initialising the console logger. %s' % error)
        pass
    if autosub.DAEMON:
        autosub.CONSOLE.setLevel(50)
    else:
        autosub.CONSOLE.setLevel(autosub.LOGLEVELCONSOLE)
    return log

def _ReadFiles():
        # Read the A7 mapping file
    log = logging.getLogger('thelogger')
    try:
        with open(autosub.A7MAPFILE) as fp:
            autosub.ADDIC7EDMAPPING = json.load(fp)
    except Exception as error:
        log.error('A7 mapping file. %s' %error)
        # Read the releasegroups from the file
    try:
        with CodecsOpen(autosub.RLSGRPFILE, 'r', 'utf-8') as fp:
            autosub.RLSGRPS = fp.read().splitlines()
    except Exception as error:
        log.error('Releasegroups file. %s' % error)
    return

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

def main(argv=None):
    Update = False
    if argv is None:
        argv = sys.argv
    try:
        opts, args= getopt(argv[1:], "hc:dlu", ["help","config=","daemon","nolaunch","updated="])
    except Exception as error:
        print error
        os._exit(1)
    # option processing
    for option, value in opts:
        if option in ("-h", "--help"):
            raise Usage(help_message)
        if option in ("-c", "--config"):
            autosub.CONFIGPATH,autosub.CONFIGFILE = os.path.split(value)
        if option in ("-l", "--nolaunch"):
            autosub.LAUNCHBROWSER = False
        if option in ("-d", "--daemon"):
            if sys.platform == "win32":
                print "ERROR: No support for daemon mode in Windows"
                # TODO: Service support for Windows
            else:
                autosub.DAEMON = True
        if option in ("-u"):
            autosub.UPDATED = True  
    
        #load configuration and the default settings.
    _Initialize()
    log = _initLogging()    
    CheckVersion()
    _ReadFiles()
    if autosub.DAEMON:
        autosub.AutoSub.daemon()
        os.chdir(autosub.PATH)
        autosub.LOGLEVELCONSOLE = 50
        #make sure that sqlite database is loaded after you deamonise 
    InitDatabase()

    log.info("PID is: %s" %autosub.PID)
    log.debug("Systemencoding is: %s" %autosub.SYSENCODING)
    log.debug("Configversion is: %d" %autosub.CONFIGVERSION)
    log.debug("Dbversion is: %d" %autosub.DBVERSION)
    log.debug("Autosub version is: %s" %Versions.autosubversion)

    autosub.AutoSub.start()
    
    log.info("Going into a loop to keep the main thread going")
    while True:
        sleep(1)
if __name__ == "__main__":
    sys.exit(main())