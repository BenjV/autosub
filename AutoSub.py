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
import locale
import platform
from uuid import getnode
import requests
from xmlrpclib import Server as xmlRpcServer 
import autosub
import autosub.version as Versions
from autosub.Config import ReadConfig
from autosub.Db import initDatabase
from autosub.AutoSub import start
import logging.handlers
from autosub.Helpers import CheckVersion

def _Initialize():

    print "AutoSub: Initializing variables and loading config"
    try:
        locale.setlocale(locale.LC_ALL, "")
        autosub.SYSENCODING = locale.getpreferredencoding()
    except:
        pass
        # for OSes that are poorly configured, like slackware
    if not autosub.SYSENCODING or autosub.SYSENCODING in ('ANSI_X3.4-1968', 'US-ASCII', 'ASCII'):
        autosub.SYSENCODING = 'UTF-8'
    autosub.PATH = unicode(os.getcwd(), autosub.SYSENCODING)
    if 'Alpha' in Versions.autosubversion:
        release = Versions.autosubversion.split(' ')[0]
        versionnumber = Versions.autosubversion.split(' ')[1]
    else:
        versionnumber = autosub.version.autosubversion
    autosub.CERTIFICATEPATH = os.path.normpath(autosub.PATH +'/library/requests/cacert.pem')
    autosub.VERSION = int(versionnumber.split('.')[0]) * 1000 + int(versionnumber.split('.')[1]) * 100 + int(versionnumber.split('.')[2]) * 1
    autosub.OPENSUBTITLESUSERAGENT += versionnumber
    autosub.OPENSUBTITLESSERVER = xmlRpcServer(autosub.OPENSUBTITLESURL)
    autosub.TVDBSESSION = requests.Session()
    autosub.TVDBSESSION.headers.update({'Accept': 'application/json','Content-Type': 'application/json'})
    autosub.DBFILE = os.path.join(autosub.PATH, autosub.DBFILE)
    if not autosub.CONFIGFILE:
        autosub.CONFIGFILE = os.path.join(autosub.PATH,'config.properties')
    autosub.NODE_ID = getnode()
    autosub.Config.ReadConfig()
    # check the logfile location and make it the default if neccessary
    LogPath,LogFile = os.path.split(autosub.LOGFILE)
    if not LogFile:
        LogFile = u"AutoSubService.log"
    if not LogPath:
        LogPath = autosub.PATH

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




help_message = '''
Usage:
    -h (--help)     Prints this message
    -c (--config=)  Forces AutoSub.py to use a configfile other than ./config.properties
    -d (--daemon)   Run AutoSub in the background
    -l (--nolaunch) Stop AutoSub from launching a webbrowser
    
Example:
    python AutoSub.py
    python AutoSub.py -d
    python AutoSub.py -d -l
    python AutoSub.py -c/home/user/config.properties
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
            if os.path.exists(value):
                autosub.CONFIGFILE = value
            else:
                print "ERROR: Configfile does not exists."
                os._exit(0)
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
    if autosub.DAEMON:
        autosub.AutoSub.daemon()
        os.chdir(autosub.PATH)
        autosub.LOGLEVELCONSOLE = 50

    autosub.PID = str(os.getpid())
    try:
        with open('autosub.pid' , "w", 0) as pidfile:
            pidfile.write(autosub.PID + '\n')
    except Exception as error:
        log.error('AutoSub: Could not create the PID file. Error is:', error)
        sys.exit(1)

        #make sure that sqlite database is loaded after you deamonise 
    autosub.Db.initDatabase()

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