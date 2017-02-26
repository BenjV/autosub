# Autosub checkSub.py
#
# The Autosub checkSub module
#

import logging
import os
import time
import sqlite3

# Autosub specific modules
from autosub.getSubLinks import getSubLinks
import autosub.scanDisk
from autosub.Db import idCache
from autosub.Helpers import UpdateA7IdMapping
from autosub.downloadSubs import DownloadSub
from autosub.OpenSubtitles import OpenSubtitlesLogin, OpenSubtitlesLogout
from autosub.notify import kodimediaserver
# Settings
log = logging.getLogger('thelogger')


class checkSub():
    """
    Check the SubtitleSeeker API for subtitles of episodes that are in the WANTEDQUEUE.
    If the subtitles are found, call DownloadSub
    """
    def run(self):
        autosub.SEARCHBUSY = True
        autosub.DOWNLOADED = False
        StartTime = time.time()
        autosub.DBCONNECTION = sqlite3.connect(autosub.DBFILE)
        autosub.DBIDCACHE = idCache()
        del autosub.WANTEDQUEUE[:]

        UpdateA7IdMapping()
        autosub.scanDisk.scanDisk().run()
        Info = None
        if autosub.Addic7ed:
            Info = 'Addic7ed, '
        if autosub.OPENSUBTITLES:
            Info += 'Opensubtitles, '
        if autosub.SUBSCENE:
            Info += 'Sunscene, '
        if autosub.PODNAPISI:
            Info += 'Podnapisi, '
        if Info:
            Info = Info[:-2]
        else:
            log.info("checkSub: No website selected in config" )
        if autosub.WANTEDQUEUE and Info:
            log.info("checkSub: Starting round of subs searching on %s" % Info )                  
            # Initiate a session to OpenSubtitles and log in if OpenSubtitles is choosen
            if autosub.OPENSUBTITLES and autosub.OPENSUBTITLESUSER and autosub.OPENSUBTITLESPASSWD:
                OpenSubtitlesLogin()
            if autosub.ADDIC7ED and autosub.ADDIC7EDUSER and autosub.ADDIC7EDPASSWD:
                autosub.ADDIC7EDAPI = autosub.Addic7ed.Addic7edAPI()
                autosub.ADDIC7EDAPI.login()

            Index = 0
            End = len(autosub.WANTEDQUEUE)
            # loop through the wanted list and try to find subs for the video's
            # because we remove a video from the list we cannot use the internal counter from a for loop
            # so we track the position in the list with the variable 'Index'
            if not autosub.SEARCHSTOP:
                while Index < End:
                    if autosub.SEARCHSTOP:
                        log.info('checkSub: Search stopped by User')
                        break
                    Wanted = {}
                    Wanted = autosub.WANTEDQUEUE[Index]
                    if not Wanted:
                        Index += 1
                        continue

                    log.info("checkSub: Searching downloadlink(s) for %s, for %s" % (Wanted['file'], Wanted['langs']))
                    # get all links above the minimal match score as input for downloadSub
                    SubsNL,SubsEN = getSubLinks(Wanted)

                    if not SubsNL and not SubsEN:
                        log.debug("checkSub: No subs found for %s" % Wanted['file'])
                        Index += 1
                        continue
                    if SubsNL:
                        log.debug('checkSub: Dutch Subtitle(s) found trying to download the highest scored.')
                        if DownloadSub(Wanted,SubsNL):
                            Wanted['langs'].remove(autosub.DUTCH)
                            if not autosub.DOWNLOADENG and autosub.ENGLISH in Wanted['langs']:
                                Wanted['langs'].remove(autosub.ENGLISH)
                                SubsEN =[]
                            if autosub.ENGLISHSUBDELETE and os.path.exists(os.path.join(Wanted['folder'],Wanted['file'] + Wanted['ENext'])):
                                try:
                                    os.unlink(os.path.join(Wanted['folder'],Wanted['file'] + Wanted['ENext']))
                                    log.info("checkSub: Removed English subtitle for : %s" % Wanted['file'])
                                except Exception as error:
                                    log.error("checkSub: Error while trying to remove English subtitle message is:%s." % error)
                    if SubsEN:
                        log.debug('checkSub: English Subtitle(s) found trying to download the highest scored.')
                        if DownloadSub(Wanted,SubsEN):
                            Wanted['langs'].remove(autosub.ENGLISH)
                            time.sleep(0)

                    if len(Wanted['langs']) == 0:
                        del autosub.WANTEDQUEUE[Index]
                        time.sleep(0)
                        End -= 1
                    else:
                        Index += 1
        else:
            log.info("checkSub: Nothing to search for." ) 
        autosub.DBCONNECTION.close()
        del autosub.DBCONNECTION
        del autosub.DBIDCACHE
        if autosub.ADDIC7EDAPI:
            autosub.ADDIC7EDAPI.logout()

        if autosub.OPENSUBTITLESTOKEN:
            OpenSubtitlesLogout()
                                        
        log.info("checkSub: Finished round of subs Search. Go to sleep until the next round.")
        autosub.SEARCHTIME = time.time() - StartTime
        autosub.SEARCHBUSY = False
        autosub.SEARCHSTOP = False
        if autosub.DOWNLOADED and autosub.NOTIFYKODI and autosub.KODIUPDATEONCE:
            kodimediaserver.send_update_library()

        return True
