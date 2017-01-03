import sys
import getopt
import os
import signal
import time
import locale
import platform,shutil
from uuid import getnode

# Root path
base_path = os.path.dirname(os.path.abspath(__file__))

# Insert local directories into path
sys.path.insert(0, os.path.join(base_path, 'library'))


#signal.signal(signal.SIGTERM, autosub.AutoSub.signal_handler)

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

# TODO: comments in everyfile

class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg

def main(argv=None):
    
    import autosub

    #From Sickbeard / Headphones
    try:
        locale.setlocale(locale.LC_ALL, "")
        autosub.SYSENCODING = locale.getpreferredencoding()
    except (locale.Error, IOError):
        pass

    # for OSes that are poorly configured, like synology & slackware
    if not autosub.SYSENCODING or autosub.SYSENCODING in ('ANSI_X3.4-1968', 'US-ASCII', 'ASCII'):
        autosub.SYSENCODING = 'UTF-8'
    
    Update = False
    if argv is None:
        argv = sys.argv
    try:
        try:
            opts, args= getopt.getopt(argv[1:], "hc:dlu", ["help","config=","daemon","nolaunch","updated="])
        except getopt.error, msg:
            raise Usage(msg)
    
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
    
    except Usage, err:
        print >> sys.stderr, sys.argv[0].split("/")[-1] + ": " + str(err.msg)
        print >> sys.stderr, "\t for help use --help"
        return 2
    
    #load configuration

    print "AutoSub: Initializing variables and loading config"
    autosub.Initialize()

    #here we remove the beautifull soap folders because we don't use them anymore.
    BsPath = os.path.join(autosub.PATH,'library','beautifulsoup')
    Bs4Path = os.path.join(autosub.PATH,'library','bs4')
    try:
        if os.path.isdir(BsPath):
            shutil.rmtree(BsPath)
        if os.path.isdir(Bs4Path):
            shutil.rmtree(Bs4Path)
    except Exception as error:
        print 'Autosub could not remove the absolute beautifullsoap folders'
    # check the logfile location and make it the default if neccessary
    LogPath,LogFile = os.path.split(autosub.LOGFILE)
    if not LogFile:
        LogFile = u"AutoSubService.log"
    try:
        if not os.path.exists(LogPath):
            try:
                os.makedirs(LogPath)
            except Exception as error:
                print "Could not create log folder, fallback to default"
                LogPath = autosub.PATH
    except Exception as error:
        LogPath = autosub.PATH
    autosub.LOGFILE = os.path.join(LogPath,LogFile)

    autosub.NODE_ID = getnode()

    import autosub.AutoSub
  
    # setup de signal handler for Terminat en Keyboard interupt.  
    signal.signal(signal.SIGTERM, autosub.AutoSub.signal_handler)
    signal.signal(signal.SIGINT, autosub.AutoSub.signal_handler)
  
    print "AutoSub: Starting output to log. Bye!"
    log = autosub.initLogging(autosub.LOGFILE)    

    if autosub.DAEMON:
        autosub.AutoSub.daemon()
        os.chdir(autosub.PATH)

    autosub.PID = str(os.getpid())
    try:
        with open('autosub.pid' , "w", 0) as pidfile:
            pidfile.write(autosub.PID + '\n')
    except Exception as error:
        log.error('AutoSub: Could not create the PID file. Error is:', error)
        sys.exit(1)

    import autosub.Db  
    #make sure that sqlite database is loaded after you deamonise 
    autosub.Db.initDatabase()

    log.info("AutoSub: PID is: %s" %str(os.getpid()))
    log.debug("AutoSub: Systemencoding is: %s" %autosub.SYSENCODING)
    log.debug("AutoSub: Configversion is: %d" %autosub.CONFIGVERSION)
    log.debug("AutoSub: Dbversion is: %d" %autosub.DBVERSION)
    log.debug("AutoSUb: Autosub version is: %s" %autosub.version.autosubversion)

    autosub.AutoSub.start()
    
    log.info("AutoSub: Going into a loop to keep the main thread going")
    
    while True:
        time.sleep(1)
if __name__ == "__main__":
    sys.exit(main())