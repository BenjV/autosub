# Autosub checkSub.py
#
# The Autosub checkSub module
#

import logging
import os
import time
from json import loads
import sqlite3
import requests
# Autosub specific modules
import autosub
import autosub.Addic7ed
from autosub.getSubLinks import getSubLinks
from autosub.scanDisk import ScanDisk
from autosub.downloadSubs import DownloadSub
from autosub.OpenSubtitles import OS_Login, OS_Logout
from autosub.notify import kodimediaserver
from autosub.Helpers import CheckVersion
# Settings
log = logging.getLogger('thelogger')

def _updGithub():
# Get the latest id mapping for Addic7ed from github
    with requests.Session() as GithubSession:
        try:
            Result = GithubSession.get(autosub.ADDICMAPURL,verify=autosub.CERTIFICATEPATH)
            Result.encoding ='utf-8'
            GithubMapping = {}
            GithubMapping = loads(Result.text)
            if GithubMapping and autosub.ADDICHIGHID != len(GithubMapping):
                autosub.ADDICHIGHID = len(GithubMapping)
                log.info('Addi7ed namemapping is updated from github.')
                for NameMap in GithubMapping.iterkeys():
                    if NameMap.isdigit() and GithubMapping[NameMap].isdigit():
                        autosub.ADDIC7EDMAPPING[NameMap] = GithubMapping[NameMap]
                    else:
                        log.debug('Addic7ed namemapping from github is coruptted. %s = %s' %(NameMap,GithubMapping[NameMap])) 
        except Exception as error:
            log.error('Problem get AddicIdMapping from github. %s' % error)
        CheckVersion()
    return

class checkSub():
    """
    Check the SubtitleSeeker API for subtitles of episodes that are in the WANTEDQUEUE.
    If the subtitles are found, call DownloadSub
    """
    def run(self):
        autosub.SEARCHBUSY = True
        autosub.REFRESH_LOGPAGE = True
        autosub.DOWNLOADED = False
        StartTime = time.time()
        autosub.DBCONNECTION = sqlite3.connect(autosub.DBFILE)
        del autosub.WANTEDQUEUE[:]

        _updGithub()
        ScanDisk()
        Info = None
        if autosub.ADDIC7ED:
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
            log.info("No website selected in config" )
        if autosub.WANTEDQUEUE and Info:
            log.info("Starting round of subs searching on %s" % Info )                  
            # Initiate a session to OpenSubtitles and log in if OpenSubtitles is choosen
            if autosub.OPENSUBTITLES and autosub.OPENSUBTITLESUSER and autosub.OPENSUBTITLESPASSWD:
                OS_Login()
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
                        log.info('Search stopped by User')
                        break
                    Wanted = {}
                    Wanted = autosub.WANTEDQUEUE[Index]
                    if not Wanted:
                        Index += 1
                        continue

                    log.info("Searching downloadlink(s) for %s, for %s" % (Wanted['file'], Wanted['langs']))
                    # get all links above the minimal match score as input for downloadSub
                    SubsNL,SubsEN = getSubLinks(Wanted)

                    if not SubsNL and not SubsEN:
                        log.debug("No subs found with minmal match score for %s" % Wanted['file'])
                        Index += 1
                        continue
                    if SubsNL:
                        log.debug('Dutch Subtitle(s) found trying to download the highest scored.')
                        if DownloadSub(Wanted,SubsNL):
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
            log.info("Nothing to search for." ) 
        if autosub.ADDIC7EDAPI:
            autosub.ADDIC7EDAPI.logout()
        if autosub.OPENSUBTITLESTOKEN:
            OS_Logout()                         
        log.info("Finished round of subs Search. Go to sleep until the next round.")
        autosub.DBCONNECTION.close()
        autosub.SEARCHTIME = time.time() - StartTime
        autosub.SEARCHBUSY = False
        autosub.SEARCHSTOP = False
        autosub.REFRESH_LOGPAGE = False
        # prevent kodi library update with every download, just once per checksub round.
        if autosub.DOWNLOADED and autosub.NOTIFYKODI and autosub.KODIUPDATEONCE:
            kodimediaserver.send_update_library()
        return True
