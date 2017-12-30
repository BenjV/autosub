
# Version information
BOOTSTRAPVERSION=u'3.3.7'
JQUERYVERSION = u'3.2.1'
JQUERYDATATABLES = u'1.10.16'

# Config information
PATH = None
SERIESPATH = u''
CONFIGFILE = None
CONFIGNAME = u'config.properties'
CONFIGPATH = None
LOGFILE = None
LOGNAME = u"AutoSubService.log"
BCKPATH=u''
BROWSERREFRESH = int(1)
FALLBACKTOENG = False
DOWNLOADENG = False
DOWNLOADDUTCH = True
SUBENG = u"en"
SUBNL = u""
SUBCODEC = u'cp1252'
SKIPHIDDENDIRS = True
NOTIFYNL = False
NOTIFYEN = False
SKIPSHOW = {}
SKIPSHOWUPPER = {}
MUSTMATCH = []
USERNAMEMAPPING = {}
USERADDIC7EDMAPPING = {}
POSTPROCESSCMD = u''
MINMATCHSCORE = int(0)
EQUALMATCH = True
CONFIGVERSION = int(4)
WANTEDFIRST = True
ENGLISHSUBDELETE = False
PODNAPISI = False
SUBSCENE = False
OPENSUBTITLES = False
ADDIC7ED = False

ADDIC7EDUSER = u''
ADDIC7EDPASSWD = u''
ADDIC7EDLOGGED_IN = False
ADDIC7EDAPI = None
ADDIC7EDMAPPING = {}
OPENSUBTITLESUSERAGENT = u'PYAutosub V'
OPENSUBTITLESUSER = u''
OPENSUBTITLESPASSWD = u''
OPENSUBTITLESURL = u'http://api.opensubtitles.org/xml-rpc'
OPENSUBTITLESTOKEN = None
OPENSUBTITLESTIME = float(0)
OPENSUBTITLESBADSUBS = []

LOGLEVEL = int(20)
CONSOLE = None
LOGHANDLER = None
LOGLEVELCONSOLE = int(40)
LOGSIZE = int(1048576)
LOGNUM = int(3)

TVDBUSER = u''
TVDBACCOUNTID = u''
TVDBTIME = float(0)
TVDBAPIKEY = "EF9C532B73E84022"
TVDBSESSION = None
TVDBAPI = u'https://api.thetvdb.com'

ADDICMAPURL = u'https://raw.githubusercontent.com/BenjV/autosub/master/AddicMapping.json'
VERSIONURL = u'https://raw.githubusercontent.com/BenjV/autosub/master/autosub/version.py'
ZIPURL = u'https://github.com/BenjV/autosub/archive/master.zip'
SUBSEEKERAPI = u"http://api.subtitleseeker.com/get/title_subtitles/?api_key=24430affe80bea1edf0e8413c3abf372a64afff2"
RLSGRPURL = u'https://raw.githubusercontent.com/BenjV/autosub/master/ReleaseGroups.txt'
RLSGRPS = []


TIMEOUT = 300
DOWNLOADS_A7 = int(0)
DOWNLOADS_A7MAX = int(40)
DOWNLOADS_A7TIME = float(0)
DOWNLOADED = []

SEARCHINTERVAL = int(21600)
SEARCHTIME= float(0)
SEARCHBUSY = False
SEARCHSTOP = False
SCANDISK = None
CHECKSUB = None
WRITELOCK = False

WANTEDQUEUE = []
LASTESTDOWNLOAD = []

WEBSERVERIP = '0.0.0.0'
WEBSERVERPORT = '9960'
LAUNCHBROWSER=True
USERNAME = u''
PASSWORD = u''
WEBROOT = u''

DAEMON = None
INIT = True
DBFILE = 'database.db'
DBVERSION = None
IDCACHE = None
DOWNLOADS = None

MOBILEUSERAGENTS = None
MOBILEAUTOSUB = True

UPDATED = False
SKIPSTRINGNL = u''
SKIPSTRINGEN = u''
SKIPFOLDERSNL = u''
SKIPFOLDERSEN = u''
CERTIFICATEPATH=u''
VERSION = int(0)
GITHUBVERSION ="?.?.?"
A7MAPDATE = None
RLSGRPDATE = None
HI = False
OPENSUBTITLESSERVER = None
OPENSUBTITLESTOKEN  = None
ENGLISH = u'en'
DUTCH = u'nl'
SYSENCODING = None
NODE_ID = None
PID = None

# notifiers
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
NOTIFYKODI = False
KODISERVERHOST = u"127.0.0.1"
KODISERVERPORT = u"9090"
KODISERVERUSERNAME=u"kodi"
KODISERVERPASSWORD = u""
KODIUPDATEONCE = False
NOTIFYTELEGRAM = False
TELEGRAMAPI = u""
TELEGRAMID = u""
SUBRIGHTS = {'owner':6,'group':6,'world':4}

MOBILEUSERAGENTS = ["midp", "240x320", "blackberry", "netfront", "nokia", "panasonic", 
                    "portalmmm", "sharp", "sie-", "sonyericsson", "symbian", "windows ce", 
                    "benq", "mda", "mot-", "opera mini", "philips", "pocket pc", "sagem",
                    "samsung", "sda", "sgh-", "vodafone", "xda", "palm", "iphone", "ipod", 
                    "ipad", "android", "windows phone"]
