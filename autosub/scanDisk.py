#
# The Autosub scanDisk module
#

import logging
import os
import platform
import re
import time
import unicodedata
from library.requests.packages.chardet import detect
from collections import deque

# Autosub specific modules
import autosub
import autosub.Helpers as Helpers
from autosub.ProcessFilename import ProcessFilename
# Settings
log = logging.getLogger('thelogger')


def WalkError(error):
    log.error('scanDir: Error walking the folders. Message is %s' % error)

def walkDir(path):
    SkipListNL    = autosub.SKIPSTRINGNL.split(",")  if len(autosub.SKIPSTRINGNL) > 0  else []
    SkipListEN    = autosub.SKIPSTRINGEN.split(",")  if len(autosub.SKIPSTRINGEN) > 0  else []

    # Check for dutch folder skip
    if len(autosub.SKIPFOLDERSNL) == 0:
        SkipFoldersNL = []
    else:
        SkipFoldersNL = autosub.SKIPFOLDERSNL.split(",") if len(autosub.SKIPFOLDERSNL) > 0  else []
        for idx,folder in enumerate(SkipFoldersNL):
            SkipFoldersNL[idx] = os.path.normpath(os.path.join(path,folder.strip(" \/")))

    # Check for english folder skip
    if len(autosub.SKIPFOLDERSEN) == 0:
        SkipFoldersEN = []
    else:
        SkipFoldersEN = autosub.SKIPFOLDERSEN.split(",") if len(autosub.SKIPFOLDERSEN) > 0  else []
        for idx,folder in enumerate(SkipFoldersEN):
            SkipFoldersEN[idx] = os.path.normpath(os.path.join(path,folder.strip(" \/")))
    for dirname, dirnames, filenames in os.walk(path, True, WalkError):
        SkipThisFolderNL = False
        for skip in SkipFoldersNL:
            if dirname.startswith(skip):
                SkipThisFolderNL = True
                break
        SkipThisFolderEN = False
        for skip in SkipFoldersEN:
            if dirname.startswith(skip):
                SkipThisFolderEN = True
                break

        log.debug("scanDisk: directory name: %s" %dirname)
        if re.search('_unpack_', dirname, re.IGNORECASE):
            log.debug("scanDisk: found a unpack directory, skipping.")
            continue

        if autosub.SKIPHIDDENDIRS and os.path.split(dirname)[1].startswith(u'.'):
            continue

        if re.search('_failed_', dirname, re.IGNORECASE):
            log.debug("scanDisk: found a failed directory, skipping.")
            continue

        if re.search('@eaDir', dirname, re.IGNORECASE):
            log.debug("scanDisk: found a Synology indexing directory, skipping.")
            tmpdirs = dirnames[:]
            for dir in tmpdirs:
                dirnames.remove(dir)
            continue

        if re.search("@.*thumb", dirname, re.IGNORECASE):
            log.debug("scanDisk: found a Qnap multimedia thumbnail folder, skipping.")
            continue
        langs = []
        FileDict = {}
        for filename in filenames:
            if autosub.SEARCHSTOP:
                log.info('scanDisk: Forced Stop by user')
                return
            try:
                root,ext = os.path.splitext(filename)
                if ext[1:] in ('avi', 'mkv', 'wmv', 'ts', 'mp4'):
                    if re.search('sample', filename):
                        continue
                    if not platform.system() == 'Windows':
                        # Get best ascii compatible character for special characters
                        try:
                            if not isinstance(filename, unicode):
                                coding = detect(filename)['encoding']
                                filename = unicode(filename.decode(coding),errors='replace')
                            correctedFilename = ''.join((c for c in unicodedata.normalize('NFD', filename) if unicodedata.category(c) != 'Mn'))
                            if filename != correctedFilename:
                                os.rename(os.path.join(dirname, filename), os.path.join(dirname, correctedFilename))
                                log.info("scanDir: Renamed file %s" % correctedFilename)
                                filename = correctedFilename
                        except:
                            log.error("scanDir: Skipping directory, file %s, %s" % (dirname,filename))
                            continue
                    # What subtitle files should we expect?
                    langs = []
                    NLext = u'.' + autosub.SUBNL  + u'.srt' if autosub.SUBNL  else u'.srt'
                    ENext = u'.' + autosub.SUBENG + u'.srt' if autosub.SUBENG else u'.srt'
                    ENext = u'.en.srt'if NLext == ENext and autosub.DOWNLOADDUTCH else ENext
                    if not os.access(dirname, os.W_OK):
                        log.error('scandisk: No write access to folder: %s' % dirname)
                        continue
                    # Check which languages we want to download based on user settings.
                    log.debug('scanDir: Processing file: %s' % filename)
                    if autosub.DOWNLOADDUTCH and not SkipThisFolderNL:
                        Skipped = False
                        for SkipItem in SkipListNL:
                            if not SkipItem: break
                            if re.search(SkipItem.lower(), filename.lower()):
                                Skipped = True
                                break
                        if Skipped:
                            log.info("scanDir: %s found in %s so skipped for Dutch subs" % (SkipItem, filename))
                        elif os.path.exists(os.path.join(dirname, root + NLext)):
                            Skipped = True
                            log.debug("scanDir: %s skipped because the Dutch subtitle already exists" % filename) 
                        else:
                            # If the Dutch subtitle not skipped and doesn't exist, then add it to the wanted list
                            langs.append(autosub.DUTCH)

                    if (autosub.DOWNLOADENG or (autosub.FALLBACKTOENG and autosub.DOWNLOADDUTCH and not Skipped)) and not SkipThisFolderEN:
                        Skipped = False
                        for SkipItem in SkipListEN:
                            if not SkipItem: break
                            if re.search(SkipItem.lower(), filename.lower()):
                                Skipped = True
                                break
                        if Skipped:
                            log.info("scanDir: %s found in %s so skipped for English subs" % (SkipItem, filename))
                        elif os.path.exists(os.path.join(dirname, root + ENext)):
                            log.debug("scanDir: %s skipped because the English subtitle already exists" % filename) 
                        else:
                            # If the English subtitle not skipped and doesn't exist, then add it to the wanted list
                            if not os.path.exists(os.path.join(dirname, root + ENext)):
                                langs.append(autosub.ENGLISH)
                    if not langs:
                        # nothing to do for this file
                        continue
                    FileDict = ProcessFilename(os.path.splitext(filename)[0].strip(), ext)
                    if not FileDict:
                        log.debug('scanDisk: not enough info in the filename: %s' % filename)
                        continue
                    Skip = False
                    if   autosub.MINMATCHSCORE & 8 and not FileDict['source']    : Skip = True
                    elif autosub.MINMATCHSCORE & 4 and not FileDict['quality']   : Skip = True
                    elif autosub.MINMATCHSCORE & 2 and not FileDict['codec']     : Skip = True
                    elif autosub.MINMATCHSCORE & 1 and not FileDict['releasegrp']: Skip = True
                    if Skip:
                        log.debug('scanDisk: Filespec does not meet minmatchscore so skipping this one')
                        continue
                    FileDict['timestamp'] = unicode(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(os.path.join(dirname, filename)))))
                    FileDict['langs'] = langs
                    FileDict['NLext'] = NLext
                    FileDict['ENext'] = ENext
                    FileDict['file'] = root
                    FileDict['container'] = ext
                    FileDict['folder'] = dirname
                    FileDict['ImdbId'],FileDict['A7Id'], FileDict['TvdbId'], FileDict['title'] = Helpers.getShowid(FileDict['title'])
                    if autosub.Helpers.SkipShow(FileDict['ImdbId'],FileDict['title'], FileDict['season'], FileDict['episode']):
                        log.debug("scanDir: SKIPPED %s by Skipshow rules." % FileDict['file'])
                        continue
                    log.info("scanDir: %s WANTED FOR: %s" % (langs, filename))
                    autosub.WANTEDQUEUE.append(FileDict)
                    time.sleep(0)
            except Exception as error:
                log.error('scanDir: Problem scanning file %s. Error is: %s' %(filename, error))
    return


class scanDisk():
    """
    Scan the specified path for episodes without Dutch or (if wanted) English subtitles.
    If found add these Dutch or English subtitles to the WANTEDQUEUE.
    """
    def run(self):
        log.info("scanDisk: Starting round of local disk checking at %s" % autosub.SERIESPATH)

        seriespaths = [x.strip() for x in autosub.SERIESPATH.split(',')]
        for seriespath in seriespaths:

            if not os.path.exists(seriespath):
                log.error("scanDir: Serie Search path %s does not exist, aborting..." % seriespath)
                continue

            try:
                walkDir(seriespath)
            except Exception as error:
                log.error('scanDir: Something went wrong scanning the folders. Message is: %s' % error)
                return False

        log.info("scanDir: Finished round of local disk checking")
        return True