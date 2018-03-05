#
# The Autosub helper functions
#
import logging
from logging import handlers
import cherrypy
from re import search
from zipfile import ZipFile
from StringIO import StringIO
import time,datetime,os,sys
from ast import literal_eval
import library.requests as requests
import autosub
from distutils.dir_util import copy_tree,remove_tree
# Settings
log = logging.getLogger('thelogger')

def InitLogging():  
    # initialize logging
    # A log directory has to be created in the start directory
    Format = '%(asctime)s %(levelname)-3s %(funcName)-15s:%(message)s'
    try:
        fmt = logging.Formatter(Format,datefmt='%d-%m %H:%M:%S')
        logging.addLevelName(10,'DBG')
        logging.addLevelName(20,'INF')
        logging.addLevelName(30,'WRN')
        logging.addLevelName(40,'ERR')
        logging.addLevelName(50,'CRI')
        log = logging.getLogger("thelogger")   
        log.setLevel(autosub.LOGLEVEL)
        autosub.LOGHANDLER = logging.handlers.RotatingFileHandler(autosub.LOGFILE, 'a', autosub.LOGSIZE, autosub.LOGNUM)
        autosub.LOGHANDLER.setFormatter(fmt)
        autosub.LOGHANDLER.setLevel(autosub.LOGLEVEL)
        log.addHandler(autosub.LOGHANDLER)
    except Exception as error:
        log.error('Problem Initialising the logger. %s' % error)
        sys.exit()
    return log

def CheckVersion():
    '''
    CheckVersion
    Return values:
    GitHub Release number
    '''
    autosub.GITHUBVERSION = '?.?.?'
    try:
        with requests.Session() as GithubSession:
            response = GithubSession.get(autosub.VERSIONURL,verify=autosub.CERT,timeout=13)
            if response.ok:
                for Index, Line in enumerate(response.text.splitlines()):
                    Info = search(r'(\d+[.|-]\d+[.|-]\d+)',Line)
                    if Index == 0 and Info:
                        autosub.GITHUBVERSION = Info.group(1) if Info else '?.?.?'
                    elif Index == 3 and Info:
                        autosub.A7MAPDATE= time.mktime(time.strptime(Info.group(1),"%d-%m-%Y")) if Info else None
                    elif Index == 4 and Info:
                        autosub.RLSGRPDATE =  time.mktime(time.strptime(Info.group(1),"%d-%m-%Y")) if Info else None
            else:
                log.error('Could not get version info from github. %s' % response.reason)
    except Exception as error:
        log.error(error.message)
        return error.message
    return response.reason

def UpdateAutoSub():
    '''
    Update Autosub.
    '''
    autosub.MESSAGE = ''
    if time() - autosub.STARTTIME < 30:
        autosub.UPDATING = False
        return
    if autosub.SEARCHBUSY:
        autosub.SEARCHSTOP = True
    log.debug('Update started')
    CheckVersion()
    if autosub.GITHUBVERSION == '?.?.?':
        autosub.UPDATING = False
        autosub.MESSAGE = "Could not get a correct version from Github"
        return
    New = autosub.GITHUBVERSION.split('.')
    Current = autosub.version.autosubversion.split('.')
    if not (int(New[0]) > int(Current[0]) or int(New[1]) > int(Current[1]) or int(New[2]) > int(Current[2])):
        autosub.MESSAGE = "No higer version on github available"
        log.info('No update available. Current version: %s GitHub version: %s'%(autosub.version.autosubversion,autosub.GITHUBVERSION))
        autosub.UPDATING = False
        return

        #First we make a connection to github to get the zipfile with the release
    log.info('Starting upgrade.')
    with requests.Session() as Session:
        try:
            Result = Session.get(autosub.ZIPURL,verify=autosub.CERT,timeout=16)
        except Exception as error:
            autosub.MESSAGE = error.message
            log.error(error.message)
            autosub.UPDATING = False
            return
        log.debug('Zipfile downloaded from Github')

        # exstract the zipfile to the autosub root directory
    try:
        zf  = ZipFile(StringIO(Result.content))
        ZipRoot = zf.namelist()[0][:-1]
        if ZipRoot:
            ReleasePath = os.path.join(autosub.PATH,ZipRoot)
            if os.path.isdir(ReleasePath):
                try:
                    remove_tree(ReleasePath)
                except Exception as error:
                    autosub.MESSAGE = error.message
                    log.error(error.message)
                    autosub.UPDATING = False
                    return
        else:
            autosub.MESSAGE = 'The zipfile was corrupted'
            log.error(autosub.MESSAGE)
            autosub.UPDATING = False
            return
        Result = zf.extractall(autosub.PATH)
        log.debug('Zipfile extracted')
    except Exception as error:
        autosub.MESSAGE = error.message
        log.error(error.message)
        autosub.UPDATING = False
        return

    # copy the release 
    try:
        copy_tree(ReleasePath,autosub.PATH)
        log.debug('updated tree copied.')
    except Exception as error:
        autosub.MESSAGE = error.message
        log.error('Could not(fully) copy the updated tree. Error is %s' % error)
        autosub.UPDATING = False
        return

    # remove the release folder after the update
    if os.path.isdir(ReleasePath):
        try:
            remove_tree(ReleasePath)
        except Exception as error:
            autosub.MESSAGE = error.message
            log.error('Problem removing old release folder. Error is: %s' % error)
            autosub.UPDATING = False
            return

        Count = 0
        # Wait untill the Search thread has finished
    while autosub.SEARCHBUSY:
        time.sleep(1)
        Count += 1
        if Count > 35 :
            log.error('Update problem. Had to use a forced stop on the Search')

    autosub.Scheduler.stop(99)


def SkipShow(Imdb,showName, season, episode):
    if (showName and showName.upper() in autosub.SKIPSHOWUPPER.keys()) or  (Imdb and Imdb in autosub.SKIPSHOWUPPER.keys()):
        try:
            for ShowId, SkipList in autosub.SKIPSHOWUPPER.iteritems():
                if ShowId == Imdb or  showName.upper() == ShowId:
                    if '-1' in SkipList:
                        return True
                # Skip entire TV show
                    for value in SkipList:
                        if value == '-1':
                            log.debug("variable of %s is set to -1, skipping the complete Serie" % showName)
                            return True
                        try:
                            toskip = literal_eval(value)
                        except:
                            log.error("%s is not a valid parameter, check your Skipshow settings" % seasontmp)
                            continue
                        # Skip specific season:
                        if isinstance(toskip, int):
                            if int(season) == toskip:
                                log.debug("Season %s matches variable of %s, skipping season" % (season, showName))
                                return True
                        # Skip specific episode
                        elif isinstance(toskip, float):
                            seasontoskip = int(toskip)
                            episodetoskip = int(round((toskip-seasontoskip) * 100))
                            if int(season) == seasontoskip:
                                if episodetoskip == 0:
                                    log.debug("Season %s matches variable of %s, skipping season" % (season, showName))
                                    return True
                                elif int(episode) == episodetoskip:
                                    format = season + 'x' + episode
                                    log.debug("Episode %s matches variable of %s, skipping episode" % (format, showName))
                                    return True
        except:
            log.error('Problem with SkipShow, check the format in the settings.')
            return False