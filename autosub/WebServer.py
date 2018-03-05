# The Webserver module

import cherrypy
import logging,sys,os,sqlite3,threading
from shutil import copy as filecopy
from codecs import open as CodecsOpen
from ast import literal_eval
from re import findall
from time import sleep,time
try:
    from Cheetah.Template import Template
except:
    sys.stderr.write("ERROR!!! Cheetah is not installed yet. Download it from: http://pypi.python.org/pypi/Cheetah/2.4.4")
    sys.exit(1)
log = logging.getLogger('thelogger')
import autosub
from autosub.Config import WriteConfig
from autosub.version import autosubversion
from autosub.Db import initDb
import autosub.notify as notify
from autosub.OpenSubtitles import OS_Login,OS_Logout
from autosub.Tvdb import GetToken
from autosub.Helpers import InitLogging,CheckVersion
from autosub.Addic7ed import Addic7edAPI

def redirect(abspath, *args, **KWs):
    assert abspath[0] == '/'
    raise cherrypy.HTTPRedirect(autosub.WEBROOT + abspath, *args, **KWs)

def stringToDict(items=None):
    """
    Return a correct dict from a string
    """
    items = items.split('\r\n')
    returnitems = []
            # Future work
            # returnitems = {k:str(int(v)).zfill(7) for k,v in (x.split('=') for x in items) }
    for item in items:
        if item:
            showinfo = []
            for x in item.split('='):
                if x[-1:] == ' ':
                    x = x[:-1]
                elif x[:1] == ' ':
                    x = x[1:]
                showinfo.append(x)
            showinfo = tuple(showinfo)
            returnitems.append(showinfo)
    returnitems = dict(returnitems)
    return returnitems

def CheckMobileDevice(req_useragent):
    for MUA in autosub.MOBILEUSERAGENTS:
        if MUA.lower() in req_useragent.lower():
            return True
    return False

class PageTemplate (Template):
    #Placeholder for future, this object can be used to add stuff to the template
    pass

class Config:
    @cherrypy.expose
    def index(self):
        redirect("/config/settings")

    @cherrypy.expose
    def info(self):
        tmpl = PageTemplate(file="interface/templates/config-info.tmpl")
        return str(tmpl)  

    @cherrypy.expose
    def settings(self):
        tmpl = PageTemplate(file="interface/templates/config-settings.tmpl")
        return str(tmpl)  

    @cherrypy.expose
    def notifications(self):
        tmpl = PageTemplate(file="interface/templates/config-notification.tmpl")
        return str(tmpl)

    @cherrypy.expose
    def skipShow(self, title, season=None, episode=None):
        title = title.decode("utf-8")
        episodestoskip = None
        if not season:
            tmpl = PageTemplate(file="interface/templates/config-skipshow.tmpl")
            tmpl.title = title
            return str(tmpl)
        else:
            season = int(season)
            tmpl = PageTemplate(file="interface/templates/home.tmpl")
            if not title:
                raise cherrypy.HTTPError(400, "No show supplied")
            if title.upper() in autosub.SKIPSHOWUPPER:
                for x in autosub.SKIPSHOWUPPER[title.upper()]:
                    x = literal_eval(x)
                    x_season = int(x)
                    x_episode = int(round((x-x_season) * 100))
                    if x == -1 or (x_season == season and (x_episode == 0 or (episode and x_episode == int(episode)))):
                        tmpl.message = "This show/season/episode is already being skipped"
                        tmpl.displaymessage = "Yes"
                        tmpl.modalheader = "Information"
                        return str(tmpl)
                if episode:
                    episodestoskip = str(season + float(episode)/100)
                else:
                    episodestoskip = str(season)
                episodestoskip = episodestoskip + ',' + ','.join(autosub.SKIPSHOWUPPER[title.upper()])
            else:
                if episode:
                    episodestoskip = str(season + float(episode)/100)
                else:
                    episodestoskip = str(season)
            autosub.SKIPSHOW[title] = episodestoskip
            autosub.SKIPSHOWUPPER[title.upper()] = episodestoskip
            message = WriteConfig()

            #print season, episode
            Name = 'ImdbId' if title.isnumeric() else 'show'

            if season == -1:
                tmpl.message = "Serie with %s: <strong>%s</strong> will be skipped.<br> This will happen the next time that Auto-Sub checks for subtitles" % (Name, title.title())
            elif episode:
                tmpl.message = "Serie with %s: <strong>%s</strong> season <strong>%s</strong> episode <strong>%s</strong> will be skipped.<br> This will happen the next time that Auto-Sub checks for subtitles" % (Name, title.title(), season, episode)
            else:
                tmpl.message = "Serie with %s: <strong>%s</strong> season <strong>%s</strong> will be skipped.<br> This will happen the next time that Auto-Sub checks for subtitles" % (Name, title.title(), season)
            tmpl.message = message.encode('ascii', 'ignore')
            tmpl.displaymessage = "Yes"
            tmpl.modalheader = "Information"
            return str(tmpl)

    @cherrypy.expose  
    def saveConfig(self, subeng, skipstringnl, skipstringen, skipfoldersnl,skipfoldersen, subnl, postprocesscmd,
                   subcodec,  username, password, webroot, skipshow,
                   webserverip, webserverport, mustmatch, usernamemapping, useraddic7edmapping,
                   logfile, lognum, loglevel, seriespath=None, bckpath=None, logsize=None, web='web',webrip='webrip',
                   opensubtitlesuser=None, opensubtitlespasswd=None,  addic7eduser=None, addic7edpasswd=None,equalmatch=None,
                   ReadOwner=None, ReadGroup=None, ReadWorld=None, WriteOwner=None, WriteGroup=None, WriteWorld=None,tvdbuser = None,tvdbaccountid = None,
                   addic7ed=None,opensubtitles=None, podnapisi=None, subscene=None,
                   browserrefresh = '0', skiphiddendirs = None,useaddic7ed=None,launchbrowser=None,interval = None,
                   fallbacktoeng = None, downloadeng = None, englishsubdelete = None, notifyen = None, notifynl = None, downloaddutch = None,
                   mmssource = u'0', mmssdistro = u'0', mmsquality = u'0', mmscodec = u'0', mmsrelease = u'0',hearingimpaired = None):

        if autosub.SEARCHBUSY:
            tmpl = PageTemplate(file="interface/templates/config-settings.tmpl")
            tmpl.message = "Search is busy, not possible to save the config now"
            tmpl.displaymessage = "Yes"
            tmpl.modalheader = "Information"
            return str(tmpl)
                   
        # Set all internal variablesp
        
        autosub.SERIESPATH = os.path.normpath(seriespath) if seriespath else u''
        autosub.BCKPATH = os.path.normpath(bckpath) if bckpath else u''
        autosub.DOWNLOADENG = True if downloadeng else False
        autosub.DOWNLOADDUTCH = True if downloaddutch else False
        autosub.FALLBACKTOENG = True if fallbacktoeng else False
        autosub.ENGLISHSUBDELETE = True if englishsubdelete else False
        autosub.SUBNL = subnl if subnl and autosub.DOWNLOADDUTCH else ''
        autosub.SUBENG = subeng if (autosub.DOWNLOADENG or autosub.FALLBACKTOENG) and subeng else ''
        if (autosub.DOWNLOADENG or autosub.FALLBACKTOENG) and autosub.DOWNLOADDUTCH and autosub.SUBNL == autosub.SUBENG:
            autosub.SUBENG = 'en'
            if autosub.SUBENG == autosub.SUBNL:
                autosub.SUBNL = 'nl'
        autosub.NOTIFYEN = True if notifyen else False 
        autosub.NOTIFYNL = True if notifynl else False
        autosub.POSTPROCESSCMD = postprocesscmd
        autosub.SUBCODEC = subcodec
        autosub.SUBRIGHTS['owner']  = 4 if ReadOwner else 0
        if WriteOwner: autosub.SUBRIGHTS['owner'] += 2
        autosub.SUBRIGHTS['group']  = 4 if ReadGroup else 0
        if WriteGroup: autosub.SUBRIGHTS['group'] += 2
        autosub.SUBRIGHTS['world']  = 4 if ReadWorld  == 'True' else 0
        if WriteWorld: autosub.SUBRIGHTS['world'] += 2 
        autosub.LAUNCHBROWSER = True if launchbrowser else False
        autosub.SKIPHIDDENDIRS = True if skiphiddendirs else False
        autosub.PODNAPISI = True if podnapisi else False
        autosub.SUBSCENE = True if subscene else False
        autosub.OPENSUBTITLES = True if opensubtitles else False
        autosub.OPENSUBTITLESUSER = opensubtitlesuser
        autosub.OPENSUBTITLESPASSWD = opensubtitlespasswd.replace("%","%%")
        autosub.ADDIC7ED = True if addic7ed else False
        autosub.ADDIC7EDUSER = addic7eduser
        autosub.ADDIC7EDPASSWD = addic7edpasswd.replace("%","%%")
        autosub.TVDBUSER = tvdbuser
        autosub.TVDBACCOUNTID = tvdbaccountid
        autosub.BROWSERREFRESH = int(browserrefresh)
        autosub.SKIPSTRINGNL = skipstringnl
        autosub.SKIPSTRINGEN = skipstringen
        autosub.SKIPFOLDERSNL = skipfoldersnl
        autosub.SKIPFOLDERSEN = skipfoldersen
        autosub.MINMATCHSCORE = int(mmssource) + int(mmssdistro) + int(mmsrelease) + int(mmsquality) + int(mmscodec)
        autosub.WEB = web
        autosub.WEBRIP = webrip
        autosub.EQUALMATCH = True if equalmatch == 'True' else autosub.EQUALMATCH
        interval = '12' if int(interval) < 12 else interval
        interval = '168' if int(interval) > 168 else interval
        autosub.SEARCHINTERVAL = int(interval)*3600
    # here we change the loglevels if neccessary
        if autosub.LOGLEVEL != int(loglevel):
            autosub.LOGLEVEL = int(loglevel)
            log.setLevel(autosub.LOGLEVEL)
            autosub.LOGHANDLER.setLevel(autosub.LOGLEVEL)
        if autosub.LOGNUM != int(lognum):
            autosub.LOGNUM = int(lognum)
            autosub.LOGHANDLER.backupCount = autosub.LOGNUM
        if autosub.LOGSIZE != int(logsize)*1024:
            autosub.LOGSIZE = int(logsize)*1024
            autosub.LOGHANDLER.maxBytes = autosub.LOGSIZE
        if autosub.LOGFILE != logfile:
            autosub.LOGFILE = logfile
            InitLogging()
        autosub.WEBSERVERIP = webserverip
        autosub.WEBSERVERPORT = webserverport
        autosub.USERNAME = username
        autosub.PASSWORD = password.replace("%","%%")
        autosub.WEBROOT = webroot
        autosub.SKIPSHOW = stringToDict(skipshow)
        autosub.MUSTMATCH = [element.lower() for element in findall(r'\w+',mustmatch)] 
        autosub.USERNAMEMAPPING = stringToDict(usernamemapping)
        autosub.USERADDIC7EDMAPPING = stringToDict(useraddic7edmapping)
        autosub.HI = True if hearingimpaired else False
        Reboot = False
        if autosub.WEBSERVERIP != webserverip or int(autosub.WEBSERVERPORT) != int(webserverport) or autosub.USERNAME != username or autosub.PASSWORD != password or autosub.WEBROOT != webroot:
            Reboot = True
        # Now save to the configfile
        message = WriteConfig()
        sleep(1)
        if Reboot:
            message += '\n There are settings changed which need a reboot. Please do a manual reboot'
        tmpl = PageTemplate(file="interface/templates/config-settings.tmpl")
        tmpl.message = message
        tmpl.displaymessage = "Yes"
        tmpl.modalheader = "Information"
        return str(tmpl)

    @cherrypy.expose
    def saveNotification(self, notifymail, notifygrowl, notifynma, notifytwitter, mailsrv, mailfromaddr, mailtoaddr, 
                         mailusername, mailpassword, mailsubject, mailencryption, mailauth, growlhost, growlport, 
                         growlpass, nmaapi, twitterkey, twittersecret, notifyprowl, prowlapi, prowlpriority, notifytelegram, telegramapi, telegramid,
                         notifypushalot, pushalotapi, notifypushbullet, pushbulletapi, notifypushover, pushoverappkey,pushoveruserkey, pushoverpriority,
                         nmapriority, notifyboxcar2, boxcar2token, notifyplex, plexserverhost, plexserverport, plexserverusername, plexserverpassword,
                         notifykodi, kodiserverhost, kodiserverport, kodiserverusername, kodiserverpassword,kodiupdateonce=None):

        # Set all internal notify variables
        autosub.NOTIFYMAIL = notifymail
        autosub.MAILSRV = mailsrv
        autosub.MAILFROMADDR = mailfromaddr
        autosub.MAILTOADDR = mailtoaddr
        autosub.MAILUSERNAME = mailusername
        autosub.MAILPASSWORD = mailpassword
        autosub.MAILSUBJECT = mailsubject
        autosub.MAILENCRYPTION = mailencryption
        autosub.MAILAUTH = mailauth
        autosub.NOTIFYGROWL = notifygrowl
        autosub.GROWLHOST = growlhost
        autosub.GROWLPORT = growlport
        autosub.GROWLPASS = growlpass
        autosub.NOTIFYNMA = notifynma
        autosub.NMAAPI = nmaapi
        autosub.NMAPRIORITY = int(nmapriority)
        autosub.NOTIFYTWITTER = notifytwitter
        autosub.TWITTERKEY = twitterkey
        autosub.TWITTERSECRET = twittersecret
        autosub.NOTIFYPROWL = notifyprowl
        autosub.PROWLAPI = prowlapi
        autosub.PROWLPRIORITY = int(prowlpriority)
        autosub.NOTIFYTELEGRAM = notifytelegram
        autosub.TELEGRAMAPI = telegramapi
        autosub.TELEGRAMID = telegramid
        autosub.NOTIFYPUSHALOT = notifypushalot
        autosub.PUSHALOTAPI = pushalotapi
        autosub.NOTIFYPUSHBULLET = notifypushbullet
        autosub.PUSHBULLETAPI = pushbulletapi
        autosub.NOTIFYPUSHOVER = notifypushover
        autosub.PUSHOVERAPPKEY = pushoverappkey
        autosub.PUSHOVERUSERKEY = pushoveruserkey
        autosub.PUSHOVERPRIORITY = pushoverpriority
        autosub.NOTIFYBOXCAR2 = notifyboxcar2
        autosub.BOXCAR2TOKEN = boxcar2token
        autosub.NOTIFYPLEX = notifyplex
        autosub.PLEXSERVERHOST = plexserverhost
        autosub.PLEXSERVERPORT = plexserverport
        autosub.PLEXSERVERUSERNAME = plexserverusername
        autosub.PLEXSERVERPASSWORD = plexserverpassword
        autosub.NOTIFYKODI = notifykodi
        autosub.KODISERVERHOST = kodiserverhost
        autosub.KODISERVERPORT = kodiserverport
        autosub.KODISERVERUSERNAME = kodiserverusername
        autosub.KODISERVERPASSWORD = kodiserverpassword
        autosub.KODIUPDATEONCE = True if kodiupdateonce else False

            # Now save to the configfile
        tmpl = PageTemplate(file="interface/templates/config-notification.tmpl")
        tmpl.message =  WriteConfig()
        tmpl.displaymessage = "Yes"
        tmpl.modalheader = "Information"
        return str(tmpl)
     
    @cherrypy.expose
    def testPushalot(self, pushalotapi, dummy):
        result = notify.pushalot.test_notify(pushalotapi)
        if result:
            return "Auto-Sub successfully sent a test message with <strong>Pushalot</strong>."
        else:
            return "Failed to send a test message with <strong>Pushalot</strong>."

    @cherrypy.expose
    def testPushbullet(self, pushbulletapi, dummy):
        result = notify.pushbullet.test_notify(pushbulletapi)
        if result:
            return "Auto-Sub successfully sent a test message with <strong>Pushbullet</strong>."
        else:
            return "Failed to send a test message with <strong>Pushbullet</strong>."
    
    @cherrypy.expose
    def testMail(self, mailsrv, mailfromaddr, mailtoaddr, mailusername, mailpassword, mailsubject, mailencryption, mailauth, dummy):  
        result = notify.mail.test_notify(mailsrv, mailfromaddr, mailtoaddr, mailusername, mailpassword, mailsubject, mailencryption, mailauth)
        if result:
            return "Auto-Sub successfully sent a test message with <strong>Mail</strong>."
        else:
            return "Failed to send a test message with <strong>Mail</strong>."
    
    @cherrypy.expose
    def testTwitter(self, twitterkey, twittersecret, dummy):
        result = notify.twitter.test_notify(twitterkey, twittersecret)
        if result:
            return "Auto-Sub successfully sent a test message with <strong>Twitter</strong>."
        else:
            return "Failed to send a test message with <strong>Twitter</strong>."
    
    @cherrypy.expose
    def testNotifyMyAndroid(self, nmaapi, nmapriority, dummy):
        result = notify.nma.test_notify(nmaapi, nmapriority)
        if result:
            return "Auto-Sub successfully sent a test message with <strong>Notify My Android</strong>."
        else:
            return "Failed to send a test message with <strong>Notify My Android</strong>."
    
    @cherrypy.expose
    def testPushover(self, pushoverappkey, pushoveruserkey, pushoverpriority, dummy):
        result = notify.pushover.test_notify(pushoverappkey, pushoveruserkey,pushoverpriority)
        if result:
            return "Auto-Sub successfully sent a test message with <strong>Pushover</strong>."
        else:
            return "Failed to send a test message with <strong>Pushover</strong>."
    
    @cherrypy.expose
    def testGrowl(self, growlhost, growlport, growlpass, dummy):
        result = notify.growl.test_notify(growlhost, growlport, growlpass)
        if result:
            return "Auto-Sub successfully sent a test message with <strong>Growl</strong>."
        else:
            return "Failed to send a test message with <strong>Growl</strong>."
    
    @cherrypy.expose
    def testProwl(self, prowlapi, prowlpriority, dummy):
        result = notify.prowl.test_notify(prowlapi, prowlpriority)
        if result:
            return "Auto-Sub successfully sent a test message with <strong>Prowl</strong>."
        else:
            return "Failed to send a test message with <strong>Prowl</strong>."

    @cherrypy.expose
    def testTelegram(self, telegramapi, telegramid, dummy):
        result = notify.telegram.test_notify(telegramapi, telegramid)
        if result:
            return "Auto-Sub successfully sent a test message with <strong>Telegram</strong>."
        else:
            return "Failed to send a test message with <strong>Telegram</strong>."

    @cherrypy.expose
    def testBoxcar2(self, boxcar2token, dummy):
        result = notify.boxcar2.test_notify(boxcar2token)
        if result:
            return "Auto-Sub successfully sent a test message with <strong>Boxcar2</strong>."
        else:
            return "Failed to send a test message with <strong>Boxcar2</strong>." 
   
    @cherrypy.expose
    def testPlex(self, plexserverhost, plexserverport, plexserverusername, plexserverpassword, dummy):
        result = notify.plexmediaserver.test_update_library(plexserverhost, plexserverport, plexserverusername, plexserverpassword)
        if result:
            return "Auto-Sub successfully updated the media library on your <strong>Plex Media Server</strong>."
        else:
            return "Failed to update the media library on your <strong>Plex Media Server</strong>."

    @cherrypy.expose
    def testKodi(self, kodiserverhost, kodiserverport, kodiserverusername, kodiserverpassword, dummy):
        result = notify.kodimediaserver.test_update_library(kodiserverhost, kodiserverport, kodiserverusername, kodiserverpassword)
        if result:
            return "Auto-Sub successfully updated the media library on your <strong>Kodi Media Server</strong>."
        else:
            return "Failed to update the media library on your <strong>Kodi Media Server</strong>."
 
    @cherrypy.expose
    def verifyTvdb(self, tvdbuser, tvdbaccountid, dummy):
        if not (tvdbuser and tvdbaccountid):
            return "<strong>No input</strong>."
        if GetToken(tvdbuser,tvdbaccountid):
            return "<strong>Success</strong>."
        else:
            return "<strong>Failure</strong>."

    @cherrypy.expose
    def testAddic7ed(self, addic7eduser, addic7edpasswd, dummy):
        if Addic7edAPI().A7_Login(addic7eduser, addic7edpasswd):
            return "<strong>Success</strong>."
        else:
            return "<strong>Failure</strong>."

    @cherrypy.expose
    def testOpenSubtitles(self, opensubtitlesuser, opensubtitlespasswd, dummy):
        if OS_Login(opensubtitlesuser,opensubtitlespasswd):
            OS_Logout()
            return "<strong>Success</strong>."
        else:
            return "<strong>Failure</strong>."
 
    @cherrypy.expose
    def regTwitter(self, token_key=None, token_secret=None, token_pin=None):
        import oauth2
        import autosub.notify.twitter as notifytwitter 
        try:
            from urlparse import parse_qsl
        except:
            from cgi import parse_qsl
        if not token_key and not token_secret:
            consumer = oauth2.Consumer(key=notifytwitter.CONSUMER_KEY, secret=notifytwitter.CONSUMER_SECRET)
            oauth_client = oauth2.Client(consumer)
            response, content = oauth2.Request(notifytwitter.REQUEST_TOKEN_URL, 'GET')
            if response['status'] != '200':
                tmpl = PageTemplate(file="interface/templates/config-settings.tmpl")
                tmpl.message = "Something went wrong when trying to register Twitter"
                tmpl.displaymessage = "Yes"
                tmpl.modalheader = "Error"
                return str(tmpl)
            else:
                request_token = dict(parse_qsl(content))
                tmpl = PageTemplate(file="interface/templates/config-twitter.tmpl")
                tmpl.url = notifytwitter.AUTHORIZATION_URL + "?oauth_token=" + request_token['oauth_token']
                token_key = request_token['oauth_token']
                token_secret = request_token['oauth_token_secret']
                tmpl.token_key = token_key
                tmpl.token_secret = token_secret
                return str(tmpl)     
        if token_key and token_secret and token_pin: 
            token = oauth2.Token(token_key, token_secret)
            token.set_verifier(token_pin)
            consumer = oauth2.Consumer(key=notifytwitter.CONSUMER_KEY, secret=notifytwitter.CONSUMER_SECRET)
            oauth_client2 = oauth2.Client(consumer, token)
            response, content = oauth_client2.request(notifytwitter.ACCESS_TOKEN_URL, method='POST', body='oauth_verifier=%s' % token_pin)
            access_token = dict(parse_qsl(content))
            if response['status'] != '200':
                tmpl = PageTemplate(file="interface/templates/config-settings.tmpl")
                tmpl.message = "Something went wrong when trying to register Twitter"
                tmpl.displaymessage = "Yes"
                tmpl.modalheader = "Error"
                return str(tmpl)
            else:
                autosub.TWITTERKEY = access_token['oauth_token']
                autosub.TWITTERSECRET = access_token['oauth_token_secret']
                tmpl = PageTemplate(file="interface/templates/config-settings.tmpl")
                tmpl.message = "Twitter registration complete.<br> Remember to save your configuration and test Twitter!"
                tmpl.displaymessage = "Yes"
                tmpl.modalheader = "Information"
                return str(tmpl)
                
class Home:
    @cherrypy.expose
    def index(self):
        useragent = cherrypy.request.headers.get("User-Agent", '')
        if CheckMobileDevice(useragent) and autosub.MOBILEAUTOSUB:
            tmpl = PageTemplate(file="interface/templates/mobile/home.tmpl")
        else:
            tmpl = PageTemplate(file="interface/templates/home.tmpl")
        return str(tmpl)
    
    @cherrypy.expose
    def runNow(self):
        tmpl = PageTemplate(file="interface/templates/home.tmpl")
        tmpl.displaymessage = "Yes"
        tmpl.modalheader = "Information"
        if autosub.SEARCHBUSY:
            tmpl.message = "Auto-Sub is already running..."
            return str(tmpl)
        threading.Thread(target=autosub.checkSub.checkSub,args=(True,)).start()
        tmpl.message = "Auto-Sub is now checking for subtitles!"
        tmpl.displaymessage = "Yes"
        tmpl.modalheader = "Information"
        return str(tmpl)

    @cherrypy.expose
    def runHidden(self):
        threading.Thread(target=autosub.checkSub.checkSub,args=(False,)).start()

    @cherrypy.expose
    def stopSearch(self):
        tmpl = PageTemplate(file="interface/templates/home.tmpl")
        if autosub.SEARCHBUSY:
            autosub.SEARCHSTOP = True
            tmpl.message = 'Search will be stopped after the current sub search has ended.'
        else:
            tmpl.message = 'Search is not active.'
        tmpl.displaymessage = "Yes"
        tmpl.modalheader = "Information"     
        return str(tmpl)

    @cherrypy.expose
    def checkVersion(self):
        tmpl = PageTemplate(file="interface/templates/home.tmpl")
        if CheckVersion() == 'OK':
            tmpl.message = 'Active version &emsp;: ' + autosubversion + '<BR>Github version&emsp;: ' + autosub.GITHUBVERSION
        else:
            tmpl.message = 'Could not get Version Info from Github.'
        tmpl.displaymessage = "Yes"
        tmpl.modalheader = "Information"  
        return str(tmpl)

    @cherrypy.expose
    def UpdateAutoSub(self):
        autosub.UPDATING = True
        autosub.MESSAGE = 'Autosub is Updated!'
        threading.Thread(target=autosub.Helpers.UpdateAutoSub).start()
        del autosub.WANTEDQUEUE[:]
        tmpl = PageTemplate(file="interface/templates/status.tmpl")
        tmpl.modalheader = "Information"
        while autosub.UPDATING:
            sleep(0.1)
        tmpl.message = "Autosub is updating..."
        return str(tmpl)

    @cherrypy.expose
    def RebootAutoSub(self):
        autosub.UPDATING = True
        autosub.MESSAGE = 'Autosub is rebooted!'
        threading.Thread(target=autosub.Scheduler.stop,args=(98,)).start()
        tmpl = PageTemplate(file="interface/templates/status.tmpl")
        tmpl.displaymessage = "Yes"
        tmpl.modalheader = "Information"
        while autosub.UPDATING:
            sleep(0.1)
        tmpl.message = "Autosub is rebooting..."
        return str(tmpl)

    @cherrypy.expose
    def exitMini(self):
        if autosub.MOBILEAUTOSUB:
            autosub.MOBILEAUTOSUB = False
            redirect("/home")
        else:
            autosub.MOBILEAUTOSUB = True
            redirect("/home")
    
    @cherrypy.expose
    def shutdown(self):
        autosub.SEARCHSTOP = True
        autosub.MESSAGE = "Shutting down..."
        tmpl = PageTemplate(file="interface/templates/status.tmpl")
        threading.Thread(target=autosub.Scheduler.stop).start()
        return str(tmpl)

    @cherrypy.expose
    def backup(self):
        tmpl = PageTemplate(file="interface/templates/home.tmpl")
        if not autosub.BCKPATH:
            tmpl.message= 'No backup/restore folder in config defined.'
        elif not os.path.exists(autosub.BCKPATH):
            tmpl.message = 'Backup/restore folder does not exists.'
        elif not os.access(autosub.BCKPATH, os.W_OK):
            tmpl.message = 'No write acess to backup location.<BR> Make shure the autosub user(or on Synology the group sc-media) has write access!'
        else:
            dest = os.path.join(autosub.BCKPATH, os.path.splitext(os.path.split(autosub.CONFIGFILE)[1])[0] + '.bck')
            try:
                filecopy(autosub.CONFIGFILE,dest)
                src = os.path.join(autosub.CONFIGPATH,'database.db')
                filecopy(src,os.path.join(autosub.BCKPATH,'database.bck'))
                tmpl.message = 'Succesfull backup of the config and database files to:<BR> %s' % autosub.BCKPATH
            except Exception as error:
                tmpl.message = error.message
        tmpl.displaymessage = "Yes"
        tmpl.modalheader = "Information"     
        return str(tmpl)

    @cherrypy.expose
    def restore(self):
        tmpl = PageTemplate(file="interface/templates/home.tmpl")
        cfg_src = os.path.join(autosub.BCKPATH, os.path.splitext(os.path.split(autosub.CONFIGFILE)[1])[0] + '.bck')
        bck_src = os.path.join(autosub.BCKPATH,'database.bck')
        if not autosub.BCKPATH:
            tmpl.message= 'No backup/restore folder in config defined.'
        elif not os.path.exists(autosub.BCKPATH):
            tmpl.message = 'Backup/restore folder does not exists.'
        elif not os.path.isfile(cfg_src):
            tmpl.message = '%s not found to restore!' % cfg_src
        elif not os.path.isfile(bck_src):
            tmpl.message = '%s not found to restore!' % src_src
        else:
            try:
                filecopy(cfg_src,autosub.CONFIGFILE)
                filecopy(bck_src,os.path.join(autosub.CONFIGPATH,'database.db'))
                initDb()
                tmpl.message = 'Succesfully restored the config and database from:<BR> %s' % autosub.BCKPATH
            except Exception as error:
                tmpl.message = error.message
        tmpl.displaymessage = "Yes"
        tmpl.modalheader = "Information"     
        return str(tmpl)

    @cherrypy.expose
    def flushCache(self):
        connection=sqlite3.connect(autosub.DBFILE)
        cursor=connection.cursor()
        cursor.execute("DELETE FROM show_id_cache")
        connection.commit()
        connection.close()        
        tmpl = PageTemplate(file="interface/templates/home.tmpl")
        tmpl.message = 'Cache flushed'
        tmpl.displaymessage = "Yes"
        tmpl.modalheader = "Information"
        return str(tmpl)
    
    @cherrypy.expose
    def flushLastdown(self):
        connection=sqlite3.connect(autosub.DBFILE)
        cursor=connection.cursor()
        cursor.execute("DELETE FROM downloaded")
        connection.commit()
        connection.close()
        del autosub.DOWNLOADED[:]
        tmpl = PageTemplate(file="interface/templates/home.tmpl")
        tmpl.message = 'Downloaded subtitles database flushed'
        tmpl.displaymessage = "Yes"
        tmpl.modalheader = "Information"
        return str(tmpl)

class Log:
    @cherrypy.expose
    def index(self, loglevel = ''):
        redirect("/log/viewLog")
    
    @cherrypy.expose
    def viewLog(self, loglevel = ''):
        tmpl = PageTemplate(file="interface/templates/viewlog.tmpl")
        tmpl.loglevel = 'All' if loglevel == '' else loglevel
        if tmpl.loglevel == 'debug':
            LevelName = 'DBG'
        elif tmpl.loglevel == 'info':
            LevelName = 'INF'
        elif tmpl.loglevel == 'error':
            LevelName = 'ERR'
        else:
            LevelName = None
        if os.path.isfile(autosub.LOGFILE):
            try:
                with CodecsOpen(autosub.LOGFILE, 'r', autosub.SYSENCODING) as f:
                    LogLines = f.readlines()
            except Exception as error:
                tmpl.message = error.message
                return str(tmpl)
        FilteredLines = []
        numLines = 0
        for line in reversed(LogLines):
                if not LevelName or line[15:18] == LevelName:
                    numLines += 1
                    if numLines >= 1000:
                        break
                    FilteredLines.append(line)
        tmpl.logentries = "".join(FilteredLines)
        return str(tmpl) 
    
    @cherrypy.expose
    def clearLog(self):
        tmpl = PageTemplate(file="interface/templates/home.tmpl")
        try:
            open(autosub.LOGFILE, 'w').close()
            tmpl.message = "Logfile has been cleared!"
        except Exception as error:
            tmpl.message = error.message
        tmpl.displaymessage = "Yes"
        tmpl.modalheader = "Information"
        return str(tmpl)

class Mobile:
    @cherrypy.expose
    def index(self):
        tmpl = PageTemplate(file="interface/templates/mobile/home.tmpl")
        return str(tmpl)

class WebServerInit():
    @cherrypy.expose
    def index(self):
        redirect("/home")
    
    home = Home()
    config = Config()
    log = Log()
    mobile = Mobile()

    def error_page_401(status, message, traceback, version):
        return "Error %s - You don't have access to this resource." %status
    
    def error_page_404(status, message, traceback, version):
        tmpl = PageTemplate(file="interface/templates/home.tmpl")
        message = "Page could not be found.<br><br><center><textarea rows='15' wrap='off' class='traceback'>%s</textarea></center>" %traceback
        tmpl.message = message
        tmpl.displaymessage = "Yes"
        tmpl.modalheader = "Error %s" %status
        return str(tmpl)
    
    def error_page_500(status, message, traceback, version):
        tmpl = PageTemplate(file="interface/templates/home.tmpl")
        message = "Try again. If this error doesn't go away, please report the issue.<br><br><center><textarea rows='15' wrap='off' class='traceback'>%s</textarea></center>" %traceback
        tmpl.message = message
        tmpl.displaymessage = "Yes"
        tmpl.modalheader = "Error %s" %status
        return str(tmpl)

    _cp_config = {'error_page.401':error_page_401,
                  'error_page.404':error_page_404,
                  'error_page.500':error_page_500}