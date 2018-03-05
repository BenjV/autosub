import logging,os,sys,json,webbrowser,HTMLParser,threading
import cherrypy
from time import sleep,time
from uuid import getnode
import library.requests as requests
from library.requests.packages import chardet
from xmlrpclib import Server as xmlRpcServer 
import autosub
from autosub import WebServer,checkSub
import autosub.version as Versions
from autosub.Config import ReadConfig, WriteConfig
from autosub.Db import initDb as InitDatabase
from autosub.Helpers import CheckVersion,InitLogging
from codecs import open as CodecsOpen
from platform import node
from sys import platform

# Settings
log = logging.getLogger('thelogger')

def Initialize():
    autosub.LOGFILE = os.path.join(autosub.PATH,autosub.LOGNAME)
    autosub.DBFILE  = os.path.join(autosub.PATH,autosub.DBNAME)
    if autosub.CONFIGFILE:
        path,file = os.path.split(autosub.CONFIGFILE)
        if path:
            autosub.CONFIGPATH = path
            autosub.DBFILE     = os.path.join(path,autosub.DBNAME)
            autosub.LOGFILE    = os.path.join(path,autosub.LOGNAME)
        if file:
            autosub.CONFIGNAME = file
    else:
        autosub.CONFIGPATH = autosub.PATH
    autosub.CONFIGFILE = os.path.join(autosub.CONFIGPATH,autosub.CONFIGNAME)

        # Check if the folder exits en/or is writable
    if not os.path.exists(autosub.CONFIGPATH):
        try: 
            os.makedirs(autosub.CONFIGPATH)
        except Exception as error:
            os._exit(1)
        # Cleanup old files
    FileName = os.path.normpath(autosub.PATH +'/autosub/AutoSub.py')
    if os.path.isfile(FileName):
        os.remove(FileName)

    ReadConfig()
    if 'Alpha' in Versions.autosubversion:
        release = Versions.autosubversion.split(' ')[0]
        versionnumber = Versions.autosubversion.split(' ')[1]
    else:
        versionnumber = autosub.version.autosubversion
    autosub.VERSION = int(versionnumber.split('.')[0]) * 1000 + int(versionnumber.split('.')[1]) * 100 + int(versionnumber.split('.')[2]) * 1
    autosub.OPENSUBTITLESUSERAGENT += versionnumber
    autosub.CERT = os.path.normpath(autosub.PATH +'/library/requests/cacert.pem')
    autosub.OPENSUBTITLESSERVER = xmlRpcServer(autosub.OPENSUBTITLESURL)
    autosub.TVDBSESSION = requests.Session()
    autosub.TVDBSESSION.headers.update({'Accept': 'application/json','Content-Type': 'application/json'})
    autosub.A7MAPFILE = os.path.join(autosub.PATH,'AddicMapping.json')
    autosub.RLSGRPFILE = os.path.join(autosub.PATH,'ReleaseGroups.txt')
    autosub.NODE_ID = getnode()
    autosub.SEARCHSTOP = False
    return


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


def Browser():
        # This routine starts the default webbrowser if the system has one 
    host = 'localhost' if autosub.WEBSERVERIP == '0.0.0.0' else autosub.WEBSERVERIP
    url = 'http://%s:%s%s' % (host, autosub.WEBSERVERPORT,autosub.WEBROOT)
    try:
        webbrowser.open(url, 2, True )
    except:
        log.error(error.message)

def StartCherrypy():
     # Do the cherrypy stuff to config the webserver
     # Only use authentication in CherryPy when a username and password is set by the user
    if autosub.USERNAME and autosub.PASSWORD:
        users = {autosub.USERNAME: autosub.PASSWORD}
        cherrypy.config.update({'server.socket_host': autosub.WEBSERVERIP,
                            'server.socket_port': int(autosub.WEBSERVERPORT),
                            'tools.digest_auth.on': True,
                            'tools.digest_auth.realm': 'AutoSub website',
                            'tools.digest_auth.users': users
                           })
    else:
        cherrypy.config.update({'server.socket_host': autosub.WEBSERVERIP,'server.socket_port': int(autosub.WEBSERVERPORT)})
    RootPath = str(os.path.normpath(os.path.join(autosub.PATH,'interface')))
    conf={
            '/': {
            'tools.encode.encoding': 'utf-8',
            'tools.decode.encoding': 'utf-8',
            'tools.staticdir.on': True,
            'tools.staticdir.root': RootPath,
            'tools.staticdir.dir': "",
            'tools.staticfile.root' : RootPath
            },
            '/favicon.ico':{
            'tools.staticfile.on': True,
            'tools.staticfile.filename': "images/lynx.ico"
            },
        }

    cherrypy.config.update({ 'server.shutdown_timeout': 1 })
    try:
        cherrypy.tree.mount(autosub.WebServer.WebServerInit(), autosub.WEBROOT, config = conf)
    except Exception as error:
        log.error(error.message)
        raise SystemExit(error.message)
    cherrypy.config.update({'log.screen': False,
                            'log.access_file': '',
                            'log.error_file': ''})
    log.info("Starting CherryPy webserver")
    try:
        cherrypy.server.start()
    except Exception as error:
        log.error(error.message)
        raise SystemExit(error.message)

        os._exit(1)
    cherrypy.server.wait()


def _Scheduler():
        #Here we keep the thread going and schedule the search rounds
    while True:
        sleep(60)
        Interval = time() - autosub.LASTRUN 
        if (Interval  > autosub.SEARCHINTERVAL and Interval > 43200):
            autosub.LASTRUN = time()
            threading.Thread(target=checkSub).start()    

def start():
        #load configuration and the default settings.
    Initialize()
        # Starts the logging
    log = InitLogging()
        # Start Cherrypy
    StartCherrypy()
        # Check the version on github
    CheckVersion()
        # Read the Mapping and Releasegroup Files.
    _ReadFiles()
        # Initialise the database
    InitDatabase()
    if autosub.LAUNCHBROWSER and not autosub.UPDATING:
        Browser()
        sleep(0.1)

    log.debug("PID is: %s" %autosub.PID)
    log.debug("Currrent Directory is: %s" %autosub.PATH)
    try:
        import pwd
        log.debug("Current user is %s" % pwd.getpwuid(os.getuid())[0])
    except:
        pass
    log.info("Current Config Directory is: %s" % autosub.CONFIGPATH)
    log.debug("Systemencoding is: %s" %autosub.SYSENCODING)
    log.debug("Python version is: %s" %sys.version.split('(')[0])
    log.debug("Configversion is: %d" %autosub.CONFIGVERSION)
    log.debug("Dbversion is: %d" %autosub.DBVERSION)
    log.debug("Autosub version is: %s" %Versions.autosubversion)
        # Start the initial checksub round
    threading.Thread(target=autosub.checkSub.checkSub).start()
    _Scheduler()

def stop(signum=None):
    autosub.SEARCHSTOP = True
    if not signum or signum == 15:
        if not signum:
            log.info('Shutdown from user interface, gracefully shutting down.')
        else:
            log.info('Got Signal from OS, gracefully shutting down.')
        log.debug("Stopping Search thread, Cherrypy and removing pid file")
        try:
            log.debug('Stopping Cherrypy')
            #cherrypy.server.stop()
            cherrypy.engine.exit()
            log.debug('Cherrypy stopped')
            os.remove(os.path.join(autosub.PATH,'autosub.pid'))
        except Exception as error:
            log.error(error.message)
            # wait for the search thread to finish
        while autosub.WRITELOCK:
            sleep(0.2)
        log.debug("Flush logfile and shutting down Autosub.")
        logging.shutdown()
        os._exit(0)
    elif signum == 98 or signum == 99:
        if time() - autosub.STARTTIME < 20:
            autosub.UPDATING = False
            return
        if signum == 98:
            log.info('Reboot at user request.')
        else:
            log.info('Reboot after updating.')
        Result = WriteConfig()
        log.debug('Config is saved now restarting')
        logging.shutdown()
            # Wait to finish writing subfile if it was busy
        while autosub.WRITELOCK:
            sleep(0.2)
        args =[]
        args = sys.argv[:]
        args.insert(0, sys.executable)
        autosub.SEARCHSTOP = False
        autosub.SEARCHBUSY = False
        autosub.UPDATING = False
        sleep(1)
        os.execv(sys.executable, args)
    else:
        while autosub.WRITELOCK:
            sleep(0.2)
        os._exit(0)