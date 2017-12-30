# Autosub notify library - 
# Every function should have 2 calls, send_notify and test_notify
# Send notify should get 3 argument: videofile, subtitlefile (both without path) and lang (which should be the language)
# test_notify doesn't require any argument
# every module should return True if success, and False when failed

import logging
import autosub

from autosub.notify import twitter
from autosub.notify import mail
from autosub.notify import nma
from autosub.notify import growl
from autosub.notify import prowl
from autosub.notify import pushalot
from autosub.notify import pushbullet
from autosub.notify import pushover
from autosub.notify import boxcar2
from autosub.notify import plexmediaserver
from autosub.notify import kodimediaserver
from autosub.notify import telegram

log = logging.getLogger('thelogger')  

#def notify(lang, releasename, website):
#    log.debug("Trying to send notification. Language: %s Video: %s Website: %s" %(lang, releasename, website))
#    #Lets strip video file and subtitle file of its path!
    
#    if lang == autosub.ENGLISH and autosub.NOTIFYEN:
#        notifySend(lang, subtitlefile, videofile, website)
#    if lang == autosub.DUTCH and autosub.NOTIFYNL:
#        notifySend(lang, subtitlefile, videofile, website)

def notify(lang, releasename, website):
    if autosub.NOTIFYTWITTER:
        log.debug("Twitter is enabled")
        twitter.send_notify(lang, releasename, website)
    
    if autosub.NOTIFYMAIL:
        log.debug("Mail is enabled")
        mail.send_notify(lang, releasename, website)
    
    if autosub.NOTIFYNMA:
        log.debug("Notify My Android is enabled")
        nma.send_notify(lang, releasename, website)
    
    if autosub.NOTIFYGROWL:
        log.debug("Growl is enabled")
        growl.send_notify(lang, releasename, website)

    if autosub.NOTIFYPROWL:
        log.debug("Prowl is enabled")
        prowl.send_notify(lang, releasename, website)

    if autosub.NOTIFYTELEGRAM:
        log.debug("Telegram is enabled")
        telegram.send_notify(lang, releasename, website)    

    if autosub.NOTIFYPUSHALOT:
        log.debug("Pushalot is enabled")
        pushalot.send_notify(lang, releasename, website)

    if autosub.NOTIFYPUSHBULLET:
        log.debug("Pushbullet is enabled")
        pushbullet.send_notify(lang, releasename, website)
    
    if autosub.NOTIFYPUSHOVER:
        log.debug("Pushover is enabled")
        pushover.send_notify(lang, releasename, website)
    
    if autosub.NOTIFYBOXCAR2:
        log.debug("Boxcar2 is enabled")
        boxcar2.send_notify(lang, releasename, website)
    
    if autosub.NOTIFYPLEX:
        log.debug("Plex Media Server is enabled")
        plexmediaserver.send_update_library()

    if autosub.NOTIFYKODI:
        log.debug("Kodi Media Server is enabled")
        if not (autosub.SEARCHBUSY and autosub.KODIUPDATEONCE):
            kodimediaserver.send_update_library()