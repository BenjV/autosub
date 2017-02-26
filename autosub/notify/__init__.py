# Autosub notify library - 
# Every function should have 2 calls, send_notify and test_notify
# Send notify should get 3 argument: videofile, subtitlefile (both without path) and lang (which should be the language)
# test_notify doesn't require any argument
# every module should return True if success, and False when failed

import logging
import os

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

def notify(lang, subtitlefile, videofile, website):
    log.debug("Notification: Trying to send notification. Language: %s Srt: %s Video: %s Website: %s" %(lang, subtitlefile, videofile, website))
    #Lets strip video file and subtitle file of its path!
    subtitlefile = os.path.basename(subtitlefile)
    videofile = os.path.basename(videofile)
    
    if lang == autosub.ENGLISH and autosub.NOTIFYEN:
        notifySend(lang, subtitlefile, videofile, website)
    if lang == autosub.DUTCH and autosub.NOTIFYNL:
        notifySend(lang, subtitlefile, videofile, website)

def notifySend(lang, subtitlefile, videofile, website):
    if autosub.NOTIFYTWITTER:
        log.debug("Notification: Twitter is enabled")
        twitter.send_notify(lang, subtitlefile, videofile, website)
    
    if autosub.NOTIFYMAIL:
        log.debug("Notification: Mail is enabled")
        mail.send_notify(lang, subtitlefile, videofile, website)
    
    if autosub.NOTIFYNMA:
        log.debug("Notification: Notify My Android is enabled")
        nma.send_notify(lang, subtitlefile, videofile, website)
    
    if autosub.NOTIFYGROWL:
        log.debug("Notification: Growl is enabled")
        growl.send_notify(lang, subtitlefile, videofile, website)

    if autosub.NOTIFYPROWL:
        log.debug("Notification: Prowl is enabled")
        prowl.send_notify(lang, subtitlefile, videofile, website)

    if autosub.NOTIFYTELEGRAM:
        log.debug("Notification: Telegram is enabled")
        telegram.send_notify(lang, subtitlefile, videofile, website)    

    if autosub.NOTIFYPUSHALOT:
        log.debug("Notification: Pushalot is enabled")
        pushalot.send_notify(lang, subtitlefile, videofile, website)

    if autosub.NOTIFYPUSHBULLET:
        log.debug("Notification: Pushbullet is enabled")
        pushbullet.send_notify(lang, subtitlefile, videofile, website)
    
    if autosub.NOTIFYPUSHOVER:
        log.debug("Notification: Pushover is enabled")
        pushover.send_notify(lang, subtitlefile, videofile, website)
    
    if autosub.NOTIFYBOXCAR2:
        log.debug("Notification: Boxcar2 is enabled")
        boxcar2.send_notify(lang, subtitlefile, videofile, website)
    
    if autosub.NOTIFYPLEX:
        log.debug("Notification: Plex Media Server is enabled")
        plexmediaserver.send_update_library()

    if autosub.NOTIFYKODI:
        log.debug("Notification: Kodi Media Server is enabled")
        if not (autosub.SEARCHBUSY and autosub.KODIUPDATEONCE):
            kodimediaserver.send_update_library()