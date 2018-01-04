import Scheduler
import autosub.checkSub
import autosub.WebServer
import logging
import os,sys,json
import cherrypy
from time import sleep
import webbrowser
import signal
import HTMLParser #Don't remove this one, needed for the windows bins
from uuid import getnode
import requests
from requests.packages import chardet
from xmlrpclib import Server as xmlRpcServer 
import autosub
import autosub.version as Versions
from autosub.Config import ReadConfig
from autosub.Db import initDb as InitDatabase
from autosub.Helpers import CheckVersion,InitLogging
from codecs import open as CodecsOpen

# Settings
log = logging.getLogger('thelogger')

def _Initialize():
    if sys.version_info[0] != 2 or sys.version_info[1] < 7:
        print 'Unsupported python version (should be 2.7.xx)'
        sys.exit(1)
    try:
        locale.setlocale(locale.LC_ALL, "")
        autosub.SYSENCODING = locale.getpreferredencoding()
    except:
        pass
    if not autosub.SYSENCODING or autosub.SYSENCODING in ('ANSI_X3.4-1968', 'US-ASCII', 'ASCII'):
        autosub.SYSENCODING = 'UTF-8'
    autosub.PATH = unicode(os.getcwd(), autosub.SYSENCODING)
        # Here we deamonise if not on windows
    if autosub.DAEMON:
        autosub.AutoSub.daemon()
        os.chdir(autosub.PATH)
    autosub.PID = str(os.getpid())
    try:
        with open(os.path.join(autosub.PATH,'autosub.pid') , "w") as pidfile:
            pidfile.write(autosub.PID + '\n')
    except Exception as error:
        print error.message
        sys.exit(1)

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
        print "Config path does not exist so creating it"
        try: 
            os.makedirs(autosub.CONFIGPATH)
        except Exception as error:
            print error.message
            sys.exit(1)

    print "AutoSub: Initializing variables and loading config"
    ReadConfig()
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
    autosub.A7MAPFILE = os.path.join(autosub.PATH,'AddicMapping.json')
    autosub.RLSGRPFILE = os.path.join(autosub.PATH,'ReleaseGroups.txt')
    autosub.NODE_ID = getnode()
    autosub.SEARCHBUSY  = True
    # check the logfile location and make it the default if neccessary
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

def daemon():
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError:
        sys.exit(1)

    os.chdir("/")
    os.setsid()
    os.umask(0)
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError:
        sys.exit(1)
    sys.stdin.close()
    sys.stdout.flush()
    sys.stderr.flush()


def Browser():
        # This routine starts the default webbrowser if the system has one 
    host = 'localhost' if autosub.WEBSERVERIP == '0.0.0.0' else autosub.WEBSERVERIP
    url = 'http://%s:%s%s' % (host, autosub.WEBSERVERPORT,autosub.WEBROOT)
    try:
        webbrowser.open(url, new=0, autoraise=True )
    except:
        log.error('Failed to start webbrowser')
        try:
            print 'retry launch browser'
            webbrowser.open(url, new=1, autoraise=True)
        except Exception as error:
            log.error(error.message)
    sleep(0.1)

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
    conf = {
            '/': {
            'tools.encode.encoding': 'utf-8',
            'tools.decode.encoding': 'utf-8',
            'tools.staticdir.root': str(os.path.join(autosub.PATH, 'interface/media/')),
            },
            '/css':{
            'tools.staticdir.on': True,
            'tools.staticdir.dir': "css",
            'tools.expires.on': True,
            'tools.expires.secs': 3600 * 24 * 7
            },
            '/images':{
            'tools.staticdir.on': True,
            'tools.staticdir.dir': "images",
            'tools.expires.on': True,
            'tools.expires.secs': 3600 * 24 * 7
            },
            '/fonts':{
            'tools.staticdir.on': True,
            'tools.staticdir.dir': "fonts",
            'tools.expires.on': True,
            'tools.expires.secs': 3600 * 24 * 7
            },
            '/scripts':{
            'tools.staticdir.on': True,
            'tools.staticdir.dir': "scripts",
            'tools.expires.on': True,
            'tools.expires.secs': 3600 * 24 * 7
            },
            '/mobile':{
            'tools.staticdir.on': True,
            'tools.staticdir.dir': "mobile",
            'tools.expires.on': True,
            'tools.expires.secs': 3600 * 24 * 7
            },
            '/favicon.ico':{
            'tools.staticfile.on' : True,
            'tools.staticfile.filename' : str(os.path.join(autosub.PATH, 'interface/media/images/lynx.ico'))
            }    
        }
    cherrypy.tree.mount(autosub.WebServer.WebServerInit(),autosub.WEBROOT, config = conf)
    print "Starting CherryPy webserver"
    cherrypy.config.update({'log.screen': False,
                                'log.access_file': '',
                                'log.error_file': ''})
    try:
        cherrypy.server.start()
    except Exception as error:
        log.error("Could not start webserver. Error is: %s" %error)
    cherrypy.server.wait()
    if autosub.DAEMON:
        cherrypy.config.update({'log.screen': False,
                                'log.access_file': '',
                                'log.error_file': ''})

def start():
        #load configuration and the default settings.
    _Initialize()
        # Starts the logging
    log = InitLogging()
        # Write some info to the log
    StartCherrypy()
        # Check the version on github
    CheckVersion()
        # Read the Mapping and Releasgroup Files.
    _ReadFiles()
        # Initialise the database
    InitDatabase()
    log.info("PID is: %s" %autosub.PID)
    log.info("Currrent Directory is: %s" %autosub.PATH)
    log.info("Current Config Directory is: %s" % autosub.CONFIGPATH)
    log.info("Systemencoding is: %s" %autosub.SYSENCODING)
    log.info("Configversion is: %d" %autosub.CONFIGVERSION)
    log.info("Dbversion is: %d" %autosub.DBVERSION)
    log.info("Autosub version is: %s" %Versions.autosubversion)
    log.info("Starting the Search thread thread")
    autosub.CHECKSUB = autosub.Scheduler.Scheduler(autosub.checkSub.checkSub(), True, "CHECKSUB")
    autosub.CHECKSUB.thread.start()
    if autosub.LAUNCHBROWSER and not autosub.UPDATED:
        Browser()

def stop():
    autosub.SEARCHSTOP = True
    cherrypy.engine.exit()
    log.info("Stopping Search thread")
    log.info("Got shutdown command. Gracefully Shutting down")
    autosub.CHECKSUB.thread.join(1)
    try:
        os.remove(os.path.join(autosub.PATH,'autosub.pid'))
    except Exception as error:
        log.error('Could not remove the PID file. Error is: %s' % error)
    os._exit(0)
