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
from autosub.Helpers import getShowid, SkipShow
from autosub.ProcessFilename import ProcessFile
# Settings
log = logging.getLogger('thelogger')


def _walkError(error):
    log.error('Error walking the folders. Message is %s' % error)

def _walkDir(path):
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
    for dirnamebytes, dirnames, filenames in os.walk(str(path), True, _walkError):
        try:
            dirname = dirnamebytes.decode('utf8')
        except:
            try:
                dirname = dirnamebytes.decode('windows-1252')
                os.rename(dirnamebytes, dirname)
            except:
                log.debug('Unknown foldername formatting, so skipping a folder.')
                continue
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

        log.debug("directory name: %s" %dirname)
        if re.search('_unpack_', dirname, re.IGNORECASE):
            log.debug("found a unpack directory, skipping.")
            continue

        if autosub.SKIPHIDDENDIRS and os.path.split(dirname)[1].startswith(u'.'):
            continue

        if re.search('_failed_', dirname, re.IGNORECASE):
            log.debug("Found a failed directory, skipping.")
            continue

        if re.search('@eaDir', dirname, re.IGNORECASE):
            log.debug("Found a Synology indexing directory, skipping.")
            tmpdirs = dirnames[:]
            for dir in tmpdirs:
                dirnames.remove(dir)
            continue

        if re.search("@.*thumb", dirname, re.IGNORECASE):
            log.debug("Found a Qnap multimedia thumbnail folder, skipping.")
            continue
        langs = []
        FileDict = {}
        for filenamebytes in filenames:
            try:
                filename = filenamebytes.decode(autosub.SYSENCODING)
            except:
                try:
                    filename = filenamebytes.decode('windows-1252')
                    try:
                        os.rename(filenamebytes, filename)
                    except Exception as error:
                        log.debug('Problem renaming a file. Error is: %s' % error)
                except Exception as error:
                    log.debug('Unknown filename formatting, so skipping this file.')
                    continue
            if autosub.SEARCHSTOP:
                log.info('Forced Stop by user')
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
                                log.info("Renamed file %s" % correctedFilename)
                                filename = correctedFilename
                        except:
                            log.error("Skipping directory, file %s, %s" % (dirname,filename))
                            continue
                    # What subtitle files should we expect?
                    langs = []
                    NLext = u'.' + autosub.SUBNL  + u'.srt' if autosub.SUBNL  else u'.srt'
                    ENext = u'.' + autosub.SUBENG + u'.srt' if autosub.SUBENG else u'.srt'
                    ENext = u'.en.srt'if NLext == ENext and autosub.DOWNLOADDUTCH else ENext
                    if not os.access(dirname, os.W_OK):
                        log.error('No write access to folder: %s' % dirname)
                        continue
                    # Check which languages we want to download based on user settings.
                    log.debug('Processing file: %s' % filename)
                    if autosub.DOWNLOADDUTCH and not SkipThisFolderNL:
                        Skipped = False
                        for SkipItem in SkipListNL:
                            if not SkipItem: break
                            if re.search(SkipItem.lower(), filename.lower()):
                                Skipped = True
                                break
                        if Skipped:
                            log.info("%s found in %s so skipped for Dutch subs" % (SkipItem, filename))
                        elif os.path.exists(os.path.join(dirname, root + NLext)):
                            Skipped = True
                            log.debug("%s skipped because the Dutch subtitle already exists" % filename) 
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
                            log.info("%s found in %s so skipped for English subs" % (SkipItem, filename))
                        elif os.path.exists(os.path.join(dirname, root + ENext)):
                            log.debug("%s skipped because the English subtitle already exists" % filename) 
                        else:
                            # If the English subtitle not skipped and doesn't exist, then add it to the wanted list
                            if not os.path.exists(os.path.join(dirname, root + ENext)):
                                langs.append(autosub.ENGLISH)
                    if not langs:
                        # nothing to do for this file
                        continue
                    FileDict = ProcessFile(os.path.splitext(filename)[0].strip(), ext)
                    if not FileDict:
                        log.info('Not enough info in the filename: %s' % filename)
                        continue
                    Skip = False
                    if   autosub.MINMATCHSCORE & 8 and not FileDict['source']    : Skip = True
                    elif autosub.MINMATCHSCORE & 4 and not FileDict['quality']   : Skip = True
                    elif autosub.MINMATCHSCORE & 2 and not FileDict['codec']     : Skip = True
                    elif autosub.MINMATCHSCORE & 1 and not FileDict['releasegrp']: Skip = True
                    if Skip:
                        log.debug('Filespec does not meet minmatchscore so skipping this one')
                        continue
                    FileDict['timestamp'] = unicode(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(os.path.join(dirname, filename)))))
                    FileDict['langs'] = langs
                    FileDict['NLext'] = NLext
                    FileDict['ENext'] = ENext
                    FileDict['file'] = root
                    FileDict['container'] = ext
                    FileDict['folder'] = dirname
                    FileDict['ImdbId'],FileDict['A7Id'], FileDict['TvdbId'], FileDict['title'] = getShowid(FileDict['title'])
                    if SkipShow(FileDict['ImdbId'],FileDict['title'], FileDict['season'], FileDict['episode']):
                        log.debug("SKIPPED %s by Skipshow rules." % FileDict['file'])
                        continue
                    log.info("%s WANTED FOR: %s" % (langs, filename))
                    autosub.WANTEDQUEUE.append(FileDict)
                    time.sleep(0.01)
            except Exception as error:
                log.error('Problem scanning file %s. Error is: %s' %(filename, error))
    return


def ScanDisk():
    """
    Scan the specified path for episodes without Dutch or (if wanted) English subtitles.
    If found add these Dutch or English subtitles to the WANTEDQUEUE.
    """
    log.info("Starting round of local disk checking at %s" % autosub.SERIESPATH)
    if autosub.SERIESPATH == u'':
        log.info('No seriepath defined.')
        return True
    seriespaths = [x.strip() for x in autosub.SERIESPATH.split(',')]
    for seriespath in seriespaths:
        if not os.path.exists(seriespath):
            continue
        if not os.path.exists(seriespath):
            log.error("Serie Search path %s does not exist, aborting..." % seriespath)
            continue
        try:
            _walkDir(seriespath)
        except Exception as error:
            log.error('Something went wrong scanning the folders. Message is: %s' % error)
            return False
    log.info("Finished round of local disk checking")
    return True