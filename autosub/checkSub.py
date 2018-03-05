# Autosub checkSub.py
#
# The Autosub checkSub module
#

import logging
import os
from codecs import open as CodecsOpen
from time import sleep, time
from datetime import datetime
import json
import sqlite3
import library.requests as requests
# Autosub specific modules
import autosub
from autosub.Addic7ed import Addic7edAPI
from autosub.notify.kodimediaserver import send_update_library
from autosub.getSubLinks import getSubLinks
from autosub.scanDisk import ScanDisk
from autosub.downloadSubs import DownloadSub
from autosub.OpenSubtitles import OS_Login, OS_Logout
from autosub.Helpers import CheckVersion
from autosub.Db import idCache
from autosub.Db import downloads

# Settings
log = logging.getLogger('thelogger')

def _UpdGithub():
    if not autosub.INIT:
        if CheckVersion() != 'OK':
            return
    else:
        autosub.INIT = False
    Session = requests.Session()
    if not os.path.isfile(autosub.A7MAPFILE):
        log.error('No addicmapping file found. Should be: %s'%autosub.A7MAPFILE)
    else:
        if autosub.A7MAPDATE > os.path.getmtime(autosub.A7MAPFILE):
                # Get the latest id mapping for Addic7ed from github
            try:
                Result = Session.get(autosub.ADDICMAPURL,verify=autosub.CERT,timeout=13)
                if Result.ok:
                    autosub.ADDIC7EDMAPPING.clear()
                    autosub.ADDIC7EDMAPPING = json.loads(Result.text)
                    with open(autosub.A7MAPFILE,'w') as fp:
                        json.dump(autosub.ADDIC7EDMAPPING, fp, indent=0)
                    log.info('Addic7ed namemapping is updated from github.')
            except Exception as error:
                log.error('%s' % error)
                # Problems getting the data from github so we use the local file

        # Read new releasegroup file from github and write it to a file when a new one is on github.
    if autosub.RLSGRPDATE > os.path.getmtime(autosub.RLSGRPFILE):
        try:
            Result = Session.get(autosub.RLSGRPURL,verify=autosub.CERT,timeout=13)
            if Result.ok:
                with CodecsOpen(autosub.RLSGRPFILE,'w','utf-8') as fp:
                    fp.write(Result.text)
                autosub.RLSGRPS = Result.text.split('\n')
                log.info('List of releasegroups is updated from github.')
            else:
                log.error('Could not get releasegroup from github. %s' % Result.reason)
        except Exception as error:
            log.error('Could not get releasegroup from github. Error is: %s' % error)
    Session.close()
    return

#class checkSub():
#    """
#    Check the SubtitleSeeker API for subtitles of episodes that are in the WANTEDQUEUE.
#    If the subtitles are found, call DownloadSub
#    """
def checkSub(Forced=False):
        # setup some objects
    autosub.SEARCHBUSY  = True 
    autosub.SEARCHSTOP = False   
    DbConnect           = sqlite3.connect(autosub.DBFILE)
    autosub.DOWNLOADS   = downloads(DbConnect)
    autosub.IDCACHE     = idCache(DbConnect)
    StartTime           = time()
    del autosub.WANTEDQUEUE[:]
    _UpdGithub()
    Info = ''
    if autosub.ADDIC7ED:      Info  = 'Addic7ed,'
    if autosub.OPENSUBTITLES: Info += 'Opensubtitles,'
    if autosub.SUBSCENE:      Info += 'Subscene,'
    if autosub.PODNAPISI:     Info += 'Podnapisi,'
    if Info:
        Info = Info[:-1]
    else:
        log.info("No website selected in config" )
    Downloaded = False
    if ScanDisk(Forced) != 0 and Info and not autosub.SEARCHSTOP:
        SiteCount = 0
        log.info("Starting round of subs searching on %s" % Info )                  
            # Initiate a session to OpenSubtitles and login if it is choosen
        if autosub.OPENSUBTITLES and autosub.OPENSUBTITLESUSER and autosub.OPENSUBTITLESPASSWD:
            if OS_Login():
               SiteCount += 1
            # Initiate a session to Addic7ed and login if it is choosen
        if autosub.ADDIC7ED and autosub.ADDIC7EDUSER and autosub.ADDIC7EDPASSWD:
            autosub.ADDIC7EDAPI = Addic7edAPI()
            if autosub.ADDIC7EDAPI.A7_Login():
                SiteCount += 1
                # If the daily max is reached don't use addic7ed today
            if autosub.ADDIC7EDLOGGED_IN and autosub.DOWNLOADS_A7 >= autosub.DOWNLOADS_A7MAX:
                log.info("Max downloads from Addic7ed reached for today.")
                autosub.ADDIC7EDAPI.A7_Logout()
                SiteCount -= 1
            # Initiate a session to SubtitleSeeker if it is choosen
        autosub.SS_SESSION = requests.session()
        SSavalable = True
        if autosub.PODNAPISI:
            if not autosub.SS_SESSION.head('http://www.subtitleseeker.com',timeout=7).ok:
                SSavalable = False
                SiteCount += 1
        if autosub.SUBSCENE and SSavalable:
            if not autosub.SS_SESSION.head('http://www.subtitleseeker.com',timeout=7).ok:
                SSavalable = False
                SiteCount += 1
        if SiteCount == 0:
            log.info('None of the websites are available')
        Index = 0
        End = len(autosub.WANTEDQUEUE)
        # loop through the wanted list and try to find subs for the video's
        # because we remove a video from the list we cannot use the internal counter from a for loop
        # so we track the position in the list with the variable 'Index'
        if not autosub.SEARCHSTOP and SiteCount > 0:
            while Index < End:
                if autosub.SEARCHSTOP:
                    log.info('Search stopped by User')
                    break
                Wanted = {}               
                Wanted = autosub.WANTEDQUEUE[Index]
                    # Check if something to search for
                if not (Wanted and Wanted['Search']):
                    Index += 1
                    continue
                log.info("Searching %s subs for %s" % (Wanted['langs'],Wanted['file']))
                    # Find all links with minimal match score.
                SubsNL,SubsEN = getSubLinks(Wanted)
                if not SubsNL and not SubsEN:
                    log.info("No subs for %s with minmatch score" % Wanted['file'])
                    Index += 1
                    continue
                if SubsNL and not autosub.SEARCHSTOP:
                    Downloaded = DownloadSub(Wanted,SubsNL)
                    if Downloaded:
                        Wanted['langs'].remove(autosub.DUTCH)
                        if not autosub.DOWNLOADENG and autosub.ENGLISH in Wanted['langs']:
                            Wanted['langs'].remove(autosub.ENGLISH)
                            SubsEN =[]
                        if autosub.ENGLISHSUBDELETE and os.path.exists(os.path.join(Wanted['folder'],Wanted['file'] + Wanted['ENext'])):
                            try:
                                os.unlink(os.path.join(Wanted['folder'],Wanted['file'] + Wanted['ENext']))
                                log.info("Removed English subtitle for : %s" % Wanted['file'])
                            except Exception as error:
                                log.error("Error while trying to remove English subtitle message is:%s." % error)
                if SubsEN:
                    log.info('English Subtitle(s) found trying to download the highest scored.')
                    Downloaded = DownloadSub(Wanted,SubsEN)
                    if Downloaded:
                        Wanted['langs'].remove(autosub.ENGLISH)
                sleep(0.1)
                if len(Wanted['langs']) == 0:
                    del autosub.WANTEDQUEUE[Index]
                    sleep(0.1)
                    End -= 1
                else:
                    Index += 1
    if autosub.ADDIC7EDLOGGED_IN:
        autosub.ADDIC7EDAPI.A7_Logout()
    if autosub.OPENSUBTITLESTOKEN:
        OS_Logout()
    if autosub.SS_SESSION:
        autosub.SS_SESSION.close()
    log.info("Finished round of subs Search. Go to sleep until the next round.")
    autosub.SEARCHTIME = time() - StartTime
    autosub.SEARCHSTOP = False
    DbConnect.close()
    autosub.SEARCHBUSY = False
    # prevent kodi library update with every download, just once per checksub round.
    if Downloaded and autosub.NOTIFYKODI and autosub.KODIUPDATEONCE:
        send_update_library()
    sleep(0.01)
    return
