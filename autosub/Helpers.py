#
# The Autosub helper functions
#
import logging
from logging import handlers
import re
import json
from zipfile import ZipFile
from StringIO import StringIO
import time,datetime
import os,sys
from ast import literal_eval
import requests
from autosub.version import autosubversion
import autosub
from distutils.dir_util import copy_tree,remove_tree
from autosub.Config import ReadConfig
# Settings
log = logging.getLogger('thelogger')

_suffix = [re.compile('(.+)\s+\(?(\d{4})\)?(?:$)', re.I|re.U),
           re.compile('(.+)\s+\(?(us)\)?(?:$)', re.I|re.U),
           re.compile('(.+)\s+\(?(uk)\)?(?:$)', re.I|re.U)]

def CleanName(title):
    for reg in _suffix:
        try:
            m = re.match(reg, title)
        except TypeError:
            log.error("Error while processing: %s" % title)
            return title, None
        if m:
            return m.group(1), ' (' + m.group(2) + ')'
    return title, None

def InitLogging():  
    # initialize logging
    # A log directory has to be created in the start directory
    print "AutoSub: Starting output to log. Bye!"
    Format = '%(asctime)s %(levelname)-3s %(funcName)-12s:%(message)s'
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
        #CONSOLE log handler
    try:
        autosub.CONSOLE = logging.StreamHandler()
        autosub.CONSOLE.setLevel(autosub.LOGLEVELCONSOLE)
        autosub.CONSOLE.setFormatter(fmt)
        log.addHandler(autosub.CONSOLE)
    except Exception as error:
        log.error('Problem Initialising the console logger. %s' % error)
        pass
    if autosub.DAEMON:
        autosub.CONSOLE.setLevel(50)
    return log

def CheckVersion():
    '''
    CheckVersion
    Return values:
    GitHub Release number
    '''
    try:
        with requests.Session() as GithubSession:
            response = GithubSession.get(autosub.VERSIONURL,verify=autosub.CERTIFICATEPATH,timeout=13)
            if response.ok:
                for Index, Line in enumerate(response.text.splitlines()):
                    Info = re.search(r'(\d+[.|-]\d+[.|-]\d+)',Line)
                    if Index == 0 and Info:
                        autosub.GITHUBVERSION = Info.group(1) if Info else '?.?.?'
                    elif Index == 3 and Info:
                        autosub.A7MAPDATE= time.mktime(time.strptime(Info.group(1),"%d-%m-%Y")) if Info else None
                    elif Index == 4 and Info:
                        autosub.RLSGRPDATE =  time.mktime(time.strptime(Info.group(1),"%d-%m-%Y")) if Info else None
            else:
                log.error('Could not get version info from github. %s' % response.reason)
    except Exception as error:
        log.error('Problem getting the version info from github. Error is: %s' % error)
        return error
    return response.reason

def RebootAutoSub():
    args =[]
    args = sys.argv[:]
    args.insert(0, sys.executable)
    args.append('-u')
    log.info('Now restarting autosub...')
    log.debug('Python exec arguments are %s,  %s' %(sys.executable,args))
    os.execv(sys.executable, args)


def UpdateAutoSub():
    '''
    Update Autosub.
    '''
    autosub.SEARCHSTOP = True
    log.debug('Update started')

    # Piece of Code to let you test the reboot of autosub after an update, without actually updating anything
    #RestartTest = True
    #if RestartTest:
    #    log.debug('Module is in restart Test mode')
    #    args = []
    #    args = sys.argv[:]
    #    args.insert(0, sys.executable)
    #    args.append('-u')
    #    time.sleep(5)
    #    log.debug('Python exec arguments are %s' %(args))
    #    os.execv(sys.executable, args)
    # Get the version number from github
    CheckVersion()
    Update = False
    New = autosub.GITHUBVERSION.split('.')
    Current = autosub.version.autosubversion.split('.')
    if int(New[0]) > int(Current[0]) or int(New[1]) > int(Current[1]) or int(New[2]) > int(Current[2]):
        Update = True
        autosub.UPDATED = False
    else:
        log.info('No update available. Current version: %s GitHub version: %s'%(autosub.version.autosubversion,autosub.GITHUBVERSION))
        return

        #First we make a connection to github to get the zipfile with the release
    log.info('Starting upgrade.')
    Session = requests.Session()
    try:
        Result = Session.get(autosub.ZIPURL,verify=autosub.CERTIFICATEPATH,timeout=16)
        ZipData= Result.content
    except Exception as error:
        log.error('Could not get the zipfile from github. Error is %s' % error)
        return error
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
                    log.debug(error.message)
                    return
        else:
            log.error('No correct zipfile could be downloaded')
            return
        Result = zf.extractall(autosub.PATH)
        log.debug('Zipfile extracted')
    except Exception as error:
        log.error(error.message)
        return
    Count = 0
    while autosub.SEARCHBUSY:
        time.sleep(1)
        Count += 1
        if Count > 35 :
            log.error('Update Failed. Could not stop the Search')
            return
    # remove old folders
    Folders = ['interface/media']
    for Folder in Folders:
        try:
            Folder = os.path.join(autosub.PATH,Folder)
            remove_tree(Folder)
        except Exception as error:
            log.error(error.message)
    # copy the release 
    try:
        copy_tree(ReleasePath,autosub.PATH)
        log.debug('updated tree copied.')
    except Exception as error:
        log.error('Could not(fully) copy the updated tree. Error is %s' % error)
        return

    # remove the release folder after the update
    if os.path.isdir(ReleasePath):
        try:
            remove_tree(ReleasePath)
        except Exception as error:
            log.error('Problem removing old release folder. Error is: %s' % error)
            return
        # if search still busy give the write sub time enough to finish
    if autosub.SEARCHBUSY:
        time.sleep(1)
    args =[]
    args = sys.argv[:]
    args.insert(0, sys.executable)
    args.append('-u')
    log.info('Update to version %s. Now restarting autosub...' % autosub.GithubVersion)
    log.debug('Python exec arguments are %s,  %s' %(sys.executable,args))
    os.execv(sys.executable, args)



def SkipShow(Imdb,showName, season, episode):
    if showName.upper() in autosub.SKIPSHOWUPPER.keys() or  Imdb in autosub.SKIPSHOWUPPER.keys():
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

def getAttr(name):
    def inner_func(o):
        try:
            rv = float(o[name])
        except ValueError:
            rv = o[name]
        return rv
    return inner_func