import Scheduler
import autosub.checkSub
import autosub.WebServer
import autosub
import logging
import os
import cherrypy
import sys
from time import sleep
import webbrowser
import signal
import HTMLParser #Don't remove this one, needed for the windows bins

# Settings
log = logging.getLogger('thelogger')



def daemon():
    print "AutoSub: Starting as a daemon"
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

    print "AutoSub: Disabling console output for daemon."

    cherrypy.log.screen = False
    sys.stdin.close()
    sys.stdout.flush()
    sys.stderr.flush()


def launchBrowser():
    host = autosub.WEBSERVERIP
    port = autosub.WEBSERVERPORT
    wr = autosub.WEBROOT
    if host == '0.0.0.0':
        host = 'localhost'

    url = 'http://%s:%d' % (host, int(port))
    url = url + wr
    print 'Launch browser', url 
    try:
        webbrowser.open(url, new=1, autoraise=True )
    except:
        log.error('Failed')
        try:
            print 'retry launch browser'
            webbrowser.open(url, 1, 1)
        except:
            log.error('Failed')

def SigHandler(signum, frame):
    autosub.SEARCHSTOP = True
    cherrypy.engine.exit()
    try:
        os.remove(os.path.join(autosub.PATH,'autosub.pid'))
    except Exception as error:
        log.error('Could not remove the PID file. Error is: %s' % error)
    log.info("Got signal. Gracefully Shutting down")
    os._exit(0)

def start():
            # setup de signal handler for Terminal en Keyboard interupt.  
    signal.signal(signal.SIGTERM, SigHandler)
    signal.signal(signal.SIGINT, SigHandler)

    # Only use authentication in CherryPy when a username and password is set by the user
    if autosub.USERNAME and autosub.PASSWORD:
        users = {autosub.USERNAME: autosub.PASSWORD}
        cherrypy.config.update({'server.socket_host': autosub.WEBSERVERIP,
                            'server.socket_port': autosub.WEBSERVERPORT,
                            'tools.digest_auth.on': True,
                            'tools.digest_auth.realm': 'AutoSub website',
                            'tools.digest_auth.users': users
                           })
    else:
        cherrypy.config.update({'server.socket_host': autosub.WEBSERVERIP,
                            'server.socket_port': autosub.WEBSERVERPORT
                           })
    
    conf = {
            '/': {
            'tools.encode.encoding': 'utf-8',
            'tools.decode.encoding': 'utf-8',
            'tools.staticdir.root': os.path.join(autosub.PATH, 'interface/media/'),
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
            'tools.staticfile.filename' : os.path.join(autosub.PATH, 'interface/media/images/lynx.ico')
            }    
        }
    
    cherrypy.tree.mount(autosub.WebServer.WebServerInit(),autosub.WEBROOT, config = conf)
    log.info("Starting CherryPy webserver")

    # TODO: Let CherryPy log to another log file and not to screen
    # TODO: CherryPy settings, etc...satop()
    try:
        cherrypy.server.start()
    except Exception as error:
        log.error("Could not start webserver. Error is: %s" %error)
        os._exit(1)
    cherrypy.config.update({'log.screen': False,
                            'log.access_file': '',
                            'log.error_file': ''})
    cherrypy.server.wait()

    if autosub.LAUNCHBROWSER and not autosub.UPDATED:
        launchBrowser()
    sleep(1)
    log.info("Starting the Search thread thread")
    autosub.CHECKSUB = autosub.Scheduler.Scheduler(autosub.checkSub.checkSub(), True, "CHECKSUB")
    autosub.CHECKSUB.thread.start()


def stop():
    log.info("Stopping Search thread")
    autosub.SEARCHSTOP = True
    log.info("Got shutdown command. Gracefully Shutting down")
    cherrypy.engine.exit()
    while autosub.SEARCHBUSY:
        sleep(1)
    autosub.CHECKSUB.thread.join(2)
    try:
        os.remove(os.path.join(autosub.PATH,'autosub.pid'))
    except Exception as error:
        log.error('Could not remove the PID file. Error is: %s' % error)
    os._exit(0)
