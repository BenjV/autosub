import Config
import logging.handlers
import time,os
import autosub.version


BOOTSTRAPVERSION='3.3.6'
JQUERYVERSION = '1.9.1'
JQUERYDATATABLES = '1.10.12'
SERIESPATH = u''
BROWSERREFRESH = int(1)
FALLBACKTOENG = False
DOWNLOADENG = False
DOWNLOADDUTCH = True
SUBENG = u"en"
LOGFILE = u"AutoSubService.log"
SUBNL = u""
SKIPHIDDENDIRS = True
NOTIFYNL = False
NOTIFYEN = False
LOGLEVEL = int(20)
CONSOLE = None
LOGHANDLER = None
LOGLEVELCONSOLE = int(40)
LOGSIZE = int(1048576)
LOGNUM = int(3)
SKIPSHOW = {}
SKIPSHOWUPPER = {}
USERNAMEMAPPING = {}
USERADDIC7EDMAPPING = {}
POSTPROCESSCMD = u''
CONFIGFILE = None
PATH = None
MINMATCHSCORE = int(0)
CONFIGVERSION = version.configversion
WANTEDFIRST = True
ENGLISHSUBDELETE = False
PODNAPISI = False
SUBSCENE = False
OPENSUBTITLES = False
ADDIC7ED = False
ADDIC7EDUSER = u''
ADDIC7EDPASSWD = u''
ADDIC7EDLOGGED_IN = False
ADDICHIGHID = '0'

OPENSUBTITLESUSER = u''
OPENSUBTITLESPASSWD = u''
OPENSUBTITLESAPI = u''
OPENSUBTITLESURL = u''
OPENSUBTITLESTOKEN = None

OPENSUBTITLESTIME = float(0)

ADDIC7EDAPI = None
WANTEDQUEUE = []
LASTESTDOWNLOAD = []

APIKEY = None
API = None
IMDBAPI = None

APICALLSLASTRESET_TVDB = None
APICALLSLASTRESET_SUBSEEKER = None
APICALLSRESETINT_TVDB = 86400
APICALLSRESETINT_SUBSEEKER = 86400
APICALLSMAX_TVDB = 2500
APICALLSMAX_SUBSEEKER = 2500
APICALLS_TVDB = 2500
APICALLS_SUBSEEKER = 2500

TIMEOUT = 300
DOWNLOADS_A7 = int(0)
DOWNLOADS_A7MAX = int(40)
DOWNLOADS_A7TIME = float(0)

SEARCHINTERVAL = int(21600)
SEARCHTIME= float(0)
SEARCHBUSY = False
SEARCHSTOP = False
SCANDISK = None
CHECKSUB = None
WRITELOCK = False
SUBCODEC = u'windows-1252'

WEBSERVERIP = '0.0.0.0'
WEBSERVERPORT = '9960'
LAUNCHBROWSER=True
USERNAME = u''
PASSWORD = u''
WEBROOT = u''

DAEMON = None

DBFILE = None
DBVERSION = None
DBCONNECTION = None
DBIDCACHE = None

ADDICMAPURL = None
VERSIONURL = None
USERAGENT = None

SYSENCODING = None
MOBILEUSERAGENTS = None
MOBILEAUTOSUB = True

UPDATED = False
SKIPSTRINGNL = u''
SKIPSTRINGEN = u''
SKIPFOLDERSNL = u''
SKIPFOLDERSEN = u''
NODE_ID = None
PID = None
VERSION = int(0)
HI = False
OPENSUBTITLESSERVER = None
OPENSUBTITLESTOKEN  = None
ENGLISH = 'English'
DUTCH = 'Dutch'
CERTIFICATEPATH=u""

NOTIFYMAIL = False
MAILSRV = u""
MAILFROMADDR = u""
MAILTOADDR = u""
MAILUSERNAME = u""
MAILPASSWORD = u""
MAILSUBJECT = u""
MAILENCRYPTION = u""
MAILAUTH = u''
NOTIFYGROWL = False
GROWLHOST = u""
GROWLPORT = u""
GROWLPASS = u""
NOTIFYTWITTER = False
TWITTERKEY = u""
TWITTERSECRET = u""
NOTIFYNMA = False
NMAAPI = u""
NMAPRIORITY = 0
PROWLAPI = u""
NOTIFYPROWL = False
PROWLPRIORITY = 0
NOTIFYPUSHALOT = False
PUSHALOTAPI = u""
NOTIFYPUSHBULLET = False
PUSHBULLETAPI = u""
NOTIFYPUSHOVER = False
PUSHOVERAPPKEY = u""
PUSHOVERUSERKEY = u""
PUSHOVERPRIORITY = 0
NOTIFYBOXCAR2 = False
BOXCAR2TOKEN = u""
NOTIFYPLEX = False
PLEXSERVERHOST = u"127.0.0.1"
PLEXSERVERPORT = u"32400"
PLEXSERVERUSERNAME = u""
PLEXSERVERPASSWORD = u""
PLEXSERVERTOKEN = u""
NOTIFYTELEGRAM = False
TELEGRAMAPI = u""
TELEGRAMID = u""


MOBILEUSERAGENTS = ["midp", "240x320", "blackberry", "netfront", "nokia", "panasonic", 
                    "portalmmm", "sharp", "sie-", "sonyericsson", "symbian", "windows ce", 
                    "benq", "mda", "mot-", "opera mini", "philips", "pocket pc", "sagem",
                    "samsung", "sda", "sgh-", "vodafone", "xda", "palm", "iphone", "ipod", 
                    "ipad", "android", "windows phone"]
DBFILE = 'database.db'

def Initialize():
    global SERIESPATH,PATH, LOGFILE, LOGLEVEL, LOGLEVELCONSOLE, LOGSIZE, LOGNUM,  \
    CONFIGFILE, CERTIFICATEPATH, ZIPURL, APIKEY, API, IMDBAPI,  \
    APICALLSLASTRESET_TVDB, APICALLSLASTRESET_SUBSEEKER, \
    USERAGENT, VERSION, VERSIONURL, ADDICMAPURL, TVDBURL, \
    OPENSUBTITLESURL, OPENSUBTITLESUSERAGENT

    PATH = unicode(os.getcwd(), SYSENCODING)
    if 'Alpha' in version.autosubversion:
        release = version.autosubversion.split(' ')[0]
        versionnumber = version.autosubversion.split(' ')[1]
    else:
        versionnumber = version.autosubversion

    VERSION = int(versionnumber.split('.')[0]) * 1000 + int(versionnumber.split('.')[1]) * 100 + int(versionnumber.split('.')[2]) * 1
    VERSIONURL =  u'https://raw.githubusercontent.com/BenjV/autosub/master/autosub/version.py'
    ADDICMAPURL = u'https://raw.githubusercontent.com/BenjV/autosub/master/AddicMapping.txt'
    ZIPURL =  u'https://github.com/BenjV/autosub/archive/master.zip'
    USERAGENT = u'AutoSub/' + versionnumber
    OPENSUBTITLESUSERAGENT = u'PYAutosub V' + versionnumber

    APIKEY = "24430affe80bea1edf0e8413c3abf372a64afff2"
    TIMEOUT = 300 #default http timeout

    CERTIFICATEPATH = os.path.normpath(PATH +'/library/requests/cacert.pem')
    API = "http://api.subtitleseeker.com/get/title_subtitles/?api_key=%s" %APIKEY
    IMDBAPI = "http://thetvdb.com/api/"
    OPENSUBTITLESURL = 'http://api.opensubtitles.org/xml-rpc'

    APICALLSLASTRESET_TVDB = time.time()
    APICALLSLASTRESET_SUBSEEKER = time.time() 

    if not CONFIGFILE:
        CONFIGFILE = os.path.join(PATH,'config.properties')
    Config.ReadConfig()
    

def initLogging(logfile):
    global LOGLEVEL, LOGSIZE, LOGNUM, LOGLEVELCONSOLE, CONSOLE, LOGHANDLER, DAEMON
    
    # initialize logging
    # A log directory has to be created below the start directory
    log = logging.getLogger("thelogger")
    log.setLevel(LOGLEVEL)


    LOGHANDLER = logging.handlers.RotatingFileHandler(logfile, 'a', LOGSIZE, LOGNUM)
    log_script_formatter=logging.Formatter('%(asctime)s %(levelname)s  %(message)s')
    LOGHANDLER.setFormatter(log_script_formatter)
    LOGHANDLER.setLevel(LOGLEVEL)
    log.addHandler(LOGHANDLER)
   
    #CONSOLE log handler
    if DAEMON != True:
        CONSOLE = logging.StreamHandler()
        CONSOLE.setLevel(LOGLEVELCONSOLE)
        # set a format which is simpler for console use
        formatter = logging.Formatter('%(asctime)s %(levelname)s  %(message)s')
        CONSOLE.setFormatter(formatter)
        log.addHandler(CONSOLE)
        
    return log