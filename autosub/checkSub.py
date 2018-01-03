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
import requests
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
    if autosub.A7MAPDATE > os.path.getmtime(autosub.A7MAPFILE):
            # Get the latest id mapping for Addic7ed from github
        try:
            Result = Session.get(autosub.ADDICMAPURL,verify=autosub.CERTIFICATEPATH,timeout=13)
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
            Result = Session.get(autosub.RLSGRPURL,verify=autosub.CERTIFICATEPATH,timeout=13)
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

class checkSub():
    """
    Check the SubtitleSeeker API for subtitles of episodes that are in the WANTEDQUEUE.
    If the subtitles are found, call DownloadSub
    """
    def run(self):
         # setup some objects
        autosub.SEARCHBUSY  = True
        autosub.ADDIC7EDAPI = Addic7edAPI()
        DbConnect = sqlite3.connect(autosub.DBFILE)
        autosub.DOWNLOADS = downloads(DbConnect)
        autosub.IDCACHE   = idCache(DbConnect)
        StartTime           = time()
        del autosub.WANTEDQUEUE[:]
        _UpdGithub()
        ScanDisk()
        Info = ''
        if autosub.ADDIC7ED:      Info  = 'Addic7ed, '
        if autosub.OPENSUBTITLES: Info += 'Opensubtitles, '
        if autosub.SUBSCENE:      Info += 'Subscene, '
        if autosub.PODNAPISI:     Info += 'Podnapisi, '
        if Info:
            Info = Info[:-2]
        else:
            log.info("No website selected in config" )
        Downloaded = False
        if autosub.WANTEDQUEUE and Info:
            log.info("Starting round of subs searching on %s" % Info )                  
            # Initiate a session to OpenSubtitles and log in if OpenSubtitles is choosen
            if autosub.OPENSUBTITLES and autosub.OPENSUBTITLESUSER and autosub.OPENSUBTITLESPASSWD:
                OS_Login()
            if autosub.ADDIC7ED and autosub.ADDIC7EDUSER and autosub.ADDIC7EDPASSWD:     
                autosub.ADDIC7EDAPI.A7_Login()
            if autosub.DOWNLOADS_A7 >= autosub.DOWNLOADS_A7MAX:
                log.info("Max downloads from Addic7ed reached for today.")
                autosub.ADDIC7EDAPI.A7_Logout()

            Index = 0
            End = len(autosub.WANTEDQUEUE)
            # loop through the wanted list and try to find subs for the video's
            # because we remove a video from the list we cannot use the internal counter from a for loop
            # so we track the position in the list with the variable 'Index'
            if not autosub.SEARCHSTOP:
                while Index < End:
                    if autosub.SEARCHSTOP:
                        log.info('Search stopped by User')
                        break
                    Wanted = {}               
                    Wanted = autosub.WANTEDQUEUE[Index]
                        #Check if not empty and searchable
                    if not (Wanted and Wanted['Search']):
                        Index += 1
                        continue

                    log.info("Searching for %s, for %s" % (Wanted['file'], Wanted['langs']))
                    # get all links above the minimal match score as input for downloadSub
                    SubsNL,SubsEN = getSubLinks(Wanted)

                    if not SubsNL and not SubsEN:
                        log.debug("No subs found with minmal match score for %s" % Wanted['file'])
                        Index += 1
                        continue
                    if SubsNL and not autosub.SEARCHSTOP:
                        log.debug('Dutch Subtitle(s) found with the minmatch score, trying to download the highest scored.')
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
                        log.debug('English Subtitle(s) found trying to download the highest scored.')
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
        else:
            log.info("Nothing to search for." ) 
        if autosub.ADDIC7EDLOGGED_IN:
            autosub.ADDIC7EDAPI.A7_Logout()
        del autosub.ADDIC7EDAPI
        if autosub.OPENSUBTITLESTOKEN:
            OS_Logout()                         
        log.info("Finished round of subs Search. Go to sleep until the next round.")
        autosub.SEARCHTIME = time() - StartTime
        autosub.SEARCHBUSY = False
        autosub.SEARCHSTOP = False
        DbConnect.close()
        # prevent kodi library update with every download, just once per checksub round.
        if Downloaded and autosub.NOTIFYKODI and autosub.KODIUPDATEONCE:
            send_update_library()
        return True
