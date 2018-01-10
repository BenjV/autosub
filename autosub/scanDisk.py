#
# The Autosub scanDisk module
#
import logging
import os
import platform
import re
import time
from datetime import datetime
import unicodedata
from requests.packages import chardet
from collections import deque
# Autosub specific modules
import autosub
from autosub.Helpers import SkipShow, CleanName
from Tvdb import GetShowName,GetTvdbId
from ProcessFilename import ProcessName
# Settings
log = logging.getLogger('thelogger')

_ignore = re.compile('_failed_|_unpack_|@eaDir|@.*thumb',re.I)

def _walkError(error):
    log.error('Error walking the folders. Message is %s' % error)

def _decode(Name):
    if platform.system() != 'Windows':
        try:
            NewName = Name.decode('utf8')
        except:
            try:
                NewName = Name.decode('cp1252')
                os.rename(Name, NewName)
                return NewName
            except:
                log.error('Unknown folder or filename coding, so skipping this one. %s' % Name)
                return None
    else:
        try:
            NewName = Name.decode('cp1252')
        except:
            log.debug('Unknown folder or filename coding, so skipping this one. %s' % Name)
            NewName = None
    return NewName

def _getShowid(ShowName):
    ImdbId = AddicId = AddicUserId= TvdbId = ImdbNameMappingId = TvdbShowName = None
    UpdateCache = False
    PartName, Suffix = CleanName(ShowName)
    TvdbShowName = PartName + Suffix.upper() if Suffix else ShowName
    UpdateCache = False
    log.debug('Trying to get info for %s' %ShowName)
                # First see if the ShowName is in the mappings
    Name = u''
    if ShowName.upper() in autosub.NAMEMAPPING:
        ImdbNameMappingId, Name = autosub.NAMEMAPPING[ShowName.upper()]
    elif TvdbShowName.upper() in autosub.NAMEMAPPING:
        ImdbNameMappingId, Name = autosub.NAMEMAPPING[TvdbShowName.upper()]
    if Name: TvdbShowName = Name
    if not ImdbNameMappingId:
            # Not in the mappings then look in the cache
        ImdbId, AddicId, TvdbId, TvdbShowName = autosub.IDCACHE.getId(TvdbShowName)
        if not ImdbId:
                # Still not found ask the Tvdb website but use the correct suffix if aplicable
            ImdbId, TvdbId, TvdbShowName = GetTvdbId(TvdbShowName)
            if ImdbId:
                UpdateCache = True
        # If an Id found try to find the addicId in mappings or on the addic7d website
    if (ImdbNameMappingId or ImdbId) and not AddicId:
        Id = ImdbId if ImdbId else ImdbNameMappingId
        AddicId = autosub.USERADDIC7EDMAPPING.get(Id)
        if not AddicId:
            AddicId = autosub.ADDIC7EDMAPPING.get(Id)
        if not AddicId:
            AddicId = autosub.ADDIC7EDAPI.geta7ID(TvdbShowName)
    if UpdateCache:
        autosub.IDCACHE.setId(TvdbShowName, ImdbId, AddicId, TvdbId)
    if ImdbNameMappingId: ImdbId = ImdbNameMappingId
    if not AddicId: AddicId = 0
    log.debug("Id's are: IMDB: %s, Addic7ed: %d, ShowName: %s, TvdbName: %s" %(ImdbId,AddicId,ShowName,TvdbShowName))
    return ImdbId, AddicId, TvdbId, TvdbShowName


def _checkdate(FileTime):
        # check how old the video is and apply old video rules
        # Filedate is a list of year(yyyy), weeknum(1-52), daynum(1-7)
    FileDate = datetime.fromtimestamp(FileTime).isocalendar()
    Now = time.time()
    ToDay = datetime.fromtimestamp(Now).isocalendar()
    Diff = Now - FileTime
    if Diff < 2419200: # untill 4 weeks: always
        return True
    elif Diff < 9676800: # between 4 weeks and 16 weeks on one day a week
        if FileDate[2] == ToDay[2]:
            return True
        else:
            return False
    elif FileDate[1] & 4 and FileDate[2] == ToDay[2]: # above 16 weeks once per 4 weeks on one day
        return True
    else:
        return False 

def _walkDir(path):
    SkipListNL    = autosub.SKIPSTRINGNL.split(",")  if len(autosub.SKIPSTRINGNL) > 0  else []
    SkipListEN    = autosub.SKIPSTRINGEN.split(",")  if len(autosub.SKIPSTRINGEN) > 0  else []
    NLext = u'.' + autosub.SUBNL  + u'.srt' if autosub.SUBNL  else u'.srt'
    ENext = u'.' + autosub.SUBENG + u'.srt' if autosub.SUBENG else u'.srt'
    ENext = u'.en.srt'if NLext == ENext and autosub.DOWNLOADDUTCH else ENext
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
            #check for non video folders
        if not os.access(dirnamebytes, os.W_OK):
            log.error('No write access to folder: %s' % dirnamebytes)
            continue
        dirname = _decode(dirnamebytes)
            # skip all not normal folders
        if not dirname or _ignore.search(dirname) or (autosub.SKIPHIDDENDIRS and os.path.split(dirname)[1].startswith(u'.')):
            log.debug('Folder: %s skipped!' % dirname)
            continue
          #check if the user asked to skip this folder
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
            # walk through the files in this folder
        for filenamebytes in filenames:
            filename = _decode(filenamebytes)
            if not filename: continue
            if autosub.SEARCHSTOP:
                log.info('Forced Stop by user')
                return
            try:
                Name,ext = os.path.splitext(filename)
                if ext[1:] in ('avi', 'mkv', 'wmv', 'ts', 'mp4'):
                    if re.search('sample', filename, re.I): continue
                        # Check which languages we want to download based on user settings.
                    log.debug('Processing file: %s' % filename)
                    langs = []
                        # Do the dutch subs
                    if autosub.DOWNLOADDUTCH and not SkipThisFolderNL:
                        Skipped = False
                        for SkipItem in SkipListNL:
                            if not SkipItem: continue 
                            if re.search(SkipItem, filename,re.I|re.U):
                                log.info("%s Dutch sub skipped by skiprules" % filename)
                                Skipped = True
                                break
                        if Skipped:
                            log.info("%s found in %s so skipped for Dutch subs" % (SkipItem, filename))
                        elif os.path.exists(os.path.join(dirname, Name + NLext)):
                            Skipped = True
                            log.debug("%s skipped because the Dutch subtitle already exists" % filename) 
                        else:
                            langs.append(autosub.DUTCH)
                        # Do the English subs
                    if (autosub.DOWNLOADENG or (autosub.FALLBACKTOENG and autosub.DOWNLOADDUTCH and not Skipped)) and not SkipThisFolderEN:
                        Skipped = False
                        for SkipItem in SkipListEN:
                            if not SkipItem: continue 
                            if re.search(SkipItem, filename, re.I|re.U):
                                log.info("%s English sub skipped by skiprules" % filename)
                                Skipped = True
                                break
                        if Skipped:
                            log.info("%s found in %s so skipped for English subs" % (SkipItem, filename))
                        elif os.path.exists(os.path.join(dirname, Name + ENext)):
                            Skipped = True
                            log.debug("scanDir: %s skipped because the English subtitle already exists" % filename) 
                        else:
                            langs.append(autosub.ENGLISH)
                    if not langs:
                        continue
                    Wanted = ProcessName(Name,True)
                    if not Wanted:
                        log.info('Not enough info in the filename: %s so skipping it' % filename)
                        continue
                    FileSpecs = os.path.join(dirname, filename)
                    Wanted['SortTime'] = os.path.getmtime(FileSpecs)
                    Search = _checkdate(Wanted['SortTime'])
                    if autosub.MINMATCHSCORE & 16   and not Wanted['source']   : Search = False
                    elif autosub.MINMATCHSCORE & 8  and not Wanted['distro']   : Search = False
                    elif autosub.MINMATCHSCORE & 4  and not Wanted['rlsgrplst']: Search = False
                    elif autosub.MINMATCHSCORE & 2  and not Wanted['quality']  : Search = False
                    elif autosub.MINMATCHSCORE & 1  and not Wanted['codec']    : Search = False
                    Wanted['timestamp'] = unicode(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(Wanted['SortTime'])))
                    Wanted['langs'] = langs
                    Wanted['NLext'] = NLext
                    Wanted['ENext'] = ENext
                    Wanted['file'] = Name
                    Wanted['container'] = ext
                    Wanted['folder'] = dirname
                    Wanted['Search'] = Search
                    Wanted['ImdbId'],Wanted['A7Id'], Wanted['TvdbId'], Wanted['show'] = _getShowid(Wanted['show'])
                    if not Wanted['ImdbId']:
                        continue
                    if SkipShow(Wanted['ImdbId'],Wanted['show'], Wanted['season'], Wanted['episode']):
                        log.debug("SKIPPED %s by Skipshow rules." % Wanted['file'])
                        continue
                    log.info("%s WANTED FOR: %s" % (langs, filename))
                    autosub.WANTEDQUEUE.append(Wanted)
                    time.sleep(0.01)
            except Exception as error:
                log.error('Problem scanning file %s. Error is: %s' %(filename, error.message))
    autosub.WANTEDQUEUE.sort(key=lambda k:k['SortTime'],reverse=True )
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
            log.error("Serie Search path %s does not exist, aborting..." % seriespath)
            continue
        try:
            _walkDir(seriespath)
        except Exception as error:
            log.error('Something went wrong scanning the folders. Message is: %s' % error)
            return False
    log.info("Finished round of local disk checking")
    return