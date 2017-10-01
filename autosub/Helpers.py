#
# The Autosub helper functions
#

import logging
import re
import json
import zipfile, StringIO, filecmp
import time
import codecs
import os,sys,shutil
from ast import literal_eval
import requests
from autosub.version import autosubversion
import autosub
import Tvdb
from distutils.dir_util import copy_tree,remove_tree
from autosub.Db import idCache
import autosub.ID_lookup
import autosub.Addic7ed
from autosub.Config import ReadConfig
# Settings
log = logging.getLogger('thelogger')

REGEXES = [
        re.compile("^((?P<title>.+?)[. _-]+)?s(?P<season>\d+)[x. _-]*e(?P<episode>\d+)(([. _-]*e|-)(?P<extra_ep_num>(?!(1080|720)[pi])\d+))*[. _-]*((?P<quality>(1080|720|SD))*[pi]*[. _-]*(?P<source>(hdtv|dvdrip|bdrip|blu[e]*ray|web[. _-]*dl))*[. _]*(?P<extra_info>.+?)((?<![. _-])-(?P<releasegrp>[^-]+))?)?$", re.IGNORECASE),
        re.compile("^((?P<title>.+?)[\[. _-]+)?(?P<season>\d+)x(?P<episode>\d+)(([. _-]*x|-)(?P<extra_ep_num>(?!(1080|720)[pi])\d+))*[. _-]*((?P<quality>(1080|720|SD))*[pi]*[. _-]*(?P<source>(hdtv|dvdrip|bdrip|blu[e]*ray|web[. _-]*dl))*[. _]*(?P<extra_info>.+?)((?<![. _-])-(?P<releasegrp>[^-]+))?)?$", re.IGNORECASE),
        re.compile("^(?P<title>.+?)[. _-]+(?P<season>\d{1,2})(?P<episode>\d{2})([. _-]*(?P<quality>(1080|720|SD))*[pi]*[. _-]*(?P<source>(hdtv|dvdrip|bdrip|blu[e]*ray|web[. _-]*dl))*[. _]*(?P<extra_info>.+?)((?<![. _-])-(?P<releasegrp>[^-]+))?)?$", re.IGNORECASE)
        ]
SOURCE_PARSER = re.compile("(hdtv|tv|dvdrip|dvd|brrip|bdrip|blu[e]*ray|web[. _-]*dl)", re.IGNORECASE)
QUALITY_PARSER = re.compile("(1080|720|HD|SD)" , re.IGNORECASE)

_show = [re.compile('(.+)\s+\(?(\d{4})\)?', re.IGNORECASE),
              re.compile('(.+)\s+\(?(us)\)?', re.IGNORECASE),
              re.compile('(.+)\s+\(?(uk)\)?', re.IGNORECASE)]

def _getShow(title):
    searchName = title
    suffix = ''
    for reg in _show:
        try:
            m = re.match(reg, title)
        except TypeError:
            log.error("Error while processing: %s %s" %(searchName, suffix))
            return searchName, suffix
        
        if m:
            searchName = m.group(1)
            suffix = m.group(2)
            break
    return searchName, suffix


def Backup():
    if not autosub.BCKPATH:
        return 'No backup/restore folder in config defined.'

    if not os.path.exists(autosub.BCKPATH):
        return 'Backup/restore folder does not exists.'

    dest = os.path.join(autosub.BCKPATH, os.path.splitext(os.path.split(autosub.CONFIGFILE)[1])[0] + '.bck')
    try:
        shutil.copy(autosub.CONFIGFILE,dest)
    except Exception as error:
        log.error('%s, error is: %s' %(autosub.CONFIGFILE,error))
        return error
    try:
        src = os.path.join(autosub.PATH,'database.db')
        shutil.copy(src,os.path.join(autosub.BCKPATH,'database.bck'))
    except Exception as error:
        log.error('%s, error is: %s' %(src,error))
        return error
    log.info('Config and Database backuped to %s' % autosub.BCKPATH)
    return 'Succesfully backuped the config and database files to:<BR> %s' % autosub.BCKPATH

def Restore():
    if not autosub.BCKPATH:
        return 'No backup/restore folder in config defined.'

    if not os.path.exists(autosub.BCKPATH):
        return 'Backup/restore folder does not exists.'

    src = os.path.join(autosub.BCKPATH,'database.bck')
    dest = os.path.join(os.path.split(autosub.CONFIGFILE)[0],'database.db')
    if os.path.isfile(src):
        try:
            shutil.copy(src,dest)
            DatabaseRestored = True
        except Exception as error:
            log.error('%s, error is: %s' %(src,error))
    else:
        log.info('No database backup found so keeping the old one')

    src =  os.path.join(autosub.BCKPATH, os.path.splitext(os.path.split(autosub.CONFIGFILE)[1])[0] + '.bck')
    if os.path.isfile(src):
        try:
            shutil.copy(src,autosub.CONFIGFILE)
            ReadConfig()
        except Exception as error:
            log.error('%s, error is: %s' %(src,error))
            return error
    else:
        log.info('No config found so keeping the old one')
        return 'No config backup found, keeping the old one.'
    if DatabaseRestored :
        log.info('Config and Database restored from %s' % autosub.BCKPATH)
        return 'Succesfully restored the config and database from:<BR> %s' % autosub.BCKPATH
    else:
        log.info('Only Config restored from %s' % autosub.BCKPATH)
        return 'Succesfully restored the config but not the database from:<BR> %s' % autosub.BCKPATH

def CheckVersion():
    '''
    CheckVersion
    Return values:
    GitHub Release number
    '''
    try:
        response = requests.get(autosub.VERSIONURL,verify=autosub.CERTIFICATEPATH)
        Temp = response.text.split("'")
        if 'Alpha' in Temp[1]:
            autosub.GITHUBVERSION = Temp[1].split(' ')[1]
        else:
            autosub.GITHUBVERSION = Temp[1]
    except Exception as error:
        log.error('Problem getting the version form github. Error is: %s' % error)
    return autosub.GITHUBVERSION

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
    GithubVersion = CheckVersion()
    Update = False
    if int(GithubVersion.split('.')[0]) > int(autosub.version.autosubversion.split('.')[0]) :
        Update = True
    elif int(GithubVersion.split('.')[1]) > int(autosub.version.autosubversion.split('.')[1]) :
        Update = True
    elif int(GithubVersion.split('.')[2]) >int(autosub.version.autosubversion.split('.')[2]) :
        Update = True

    if not Update:
        message = 'No update available. Current version: ' + autosub.version.autosubversion + '. GitHub version: ' + GithubVersion
        log.info('%s' % message)
        return message
    else:
        autosub.UPDATED = False

    #First we make a connection to github to get the zipfile with the release
    log.info('Starting upgrade.')
    Session = requests.Session()
    try:
        Result = Session.get(autosub.ZIPURL,verify=autosub.CERTIFICATEPATH)
        ZipData= Result.content
    except Exception as error:
        log.error('Could not get the zipfile from github. Error is %s' % error)
        return error
    log.debug('Zipfile located on Github')

    # exstract the zipfile to the autosub root directory
    try:
        zf  = zipfile.ZipFile(StringIO.StringIO(Result.content))
        ZipRoot = zf.namelist()[0][:-1]
        if ZipRoot:
            ReleasePath = os.path.join(autosub.PATH,ZipRoot)
            if os.path.isdir(ReleasePath):
                try:
                    remove_tree(ReleasePath)
                except Exception as error:
                    log.debug('Problem removing old release folder. Error is: %s' %error)
                    return error
        else:
            return 'No correct zipfile could be downloaded'
        Result = zf.extractall(autosub.PATH)
        log.debug('Zipfile extracted')
    except Exception as error:
        log.error('Problem extracting zipfile from github. Error is %s' % error)
        return

    # copy the release 
    try:
    	copy_tree(ReleasePath,autosub.PATH)
    except Exception as error:
        log.error('Could not(fully) copy the updated tree. Error is %s' % error)
        return error
    log.debug('updated tree copied.')

    # remove the release folder after the update
    if os.path.isdir(ReleasePath):
        try:
            remove_tree(ReleasePath)
        except Exception as error:
            log.error('Problem removing old release folder. Error is: %s' % error)
            return error
    args =[]
    args = sys.argv[:]
    args.insert(0, sys.executable)
    args.append('-u')
    log.info('Update to version %s. Now restarting autosub...' % GithubVersion)
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
 
def getShowid(ShowName):
    ImdbId = AddicId = AddicUserId= TvdbId = ImdbNameMappingId = TvdbShowName = None
    UpdateCache = False
    SearchName, Suffix = _getShow(ShowName)
    SearchList =[]
    if Suffix:
        SearchList.append(SearchName +  ' (' + Suffix +')' )
        SearchList.append(SearchName +  ' ' + Suffix )
    SearchList.append(SearchName)
    log.debug('Trying to get info for %s' %ShowName)
    for Name in SearchList:
        # First we try the User Namemapping
        if Name.upper() in autosub.NAMEMAPPING.keys():
            ImdbNameMappingId,TvdbShowName = autosub.NAMEMAPPING[Name.upper()]
            if ImdbNameMappingId:
                    # Now look for info in the cache
                AddicId, TvdbId, TvdbCacheName = idCache().getInfo(ImdbNameMappingId)
                    # no Tvdb name, then it is a user mappen and we missing the formal tvdb name
                if not TvdbShowName:
                    # if name in cache we add to the user mapping
                    if TvdbCacheName:
                        TvdbShowName = TvdbCacheName
                    else:
                            # still no tvdb name we fetch it from the tvdb website
                        TvdbShowName,TvdbId = Tvdb.GetShowName(ImdbNameMappingId)
                        if TvdbShowName:
                            autosub.NAMEMAPPING[Name.upper()][1] = TvdbShowName
        else:
            # Not found in NameMapping so check the cache
            ImdbId, AddicId, TvdbId, TvdbShowName = idCache().getId(Name.upper())
            # No info in the cache we try Tvdb
            if not ImdbId:
                ImdbId, TvdbId, TvdbShowName = Tvdb.GetTvdbId(Name)  
                if ImdbId:
                    UpdateCache = True
            # if ImdbId found, try to find the Addic7edId for it
        if (ImdbNameMappingId or ImdbId):
            if not AddicId:
                Id = ImdbNameMappingId if ImdbNameMappingId else ImdbId
                if Id:
                    if Id in autosub.ADDIC7EDMAPPING.keys():
                        AddicId = autosub.ADDIC7EDMAPPING[Id]
                    elif Id in autosub.USERADDIC7EDMAPPING.keys():
                        AddicUserId = autosub.USERADDIC7EDMAPPING[Id]
                    else:
                        AddicId = autosub.ADDIC7EDAPI.geta7ID(ShowName, TvdbShowName)
                        if AddicId and ImdbId:
                            UpdateCache = True
            break
    if UpdateCache:
        idCache().setId(ShowName.upper(), ImdbId, AddicId, TvdbId, TvdbShowName)
    if ImdbNameMappingId: ImdbId       = ImdbNameMappingId
    if not TvdbShowName:  TvdbShowName = ShowName
    if AddicUserId:       AddicId      = AddicUserId
    log.debug("Returned ID's - IMDB: %s, Addic7ed: %s, ShowName: %s" %(ImdbId,AddicId,TvdbShowName))
    return ImdbId, AddicId, TvdbId, TvdbShowName
    # no ImdbId found for this showname
    log.debug('No ImdbId found on Tvdb for %s.' % ShowName)
    return None, None, None, ShowName


def ClearLogFile():
    if os.path.isfile(autosub.LOGFILE):
        try:
            open(autosub.LOGFILE, 'w').close()
            message = "Logfile has been cleared!"
        except IOError:
            message = "Logfile is currently being used by another process. Please try again later."
        return message

def DisplaySubtitle(subtitlefile):
    if os.path.isfile(subtitlefile):
        try:
            f = codecs.open(subtitlefile, 'rb', autosub.SYSENCODING, 'replace')
            data = f.readlines()
            f.close()
        except IOError, e:
            if e.errno == 13:
                result = "Permission Denied: <br>Unable to read subtitle."
                log.error('Permission Denied on %s' %subtitlefile)
            else: 
                result = "There was a problem with loading the subtitle."
                log.error('There was a problem with loading %s' %subtitlefile)
            return result
    if len(data) < 30:
        result = "This seems to be an invalid subtitle, it has less than 30 lines to preview."
    else:
        try:
            result = "<br>".join(x.replace('"', "'") for x in data[len(data)-30:])
        except:
            result = "Problem with parsing the last 30 lines of the file"
    return result

def ConvertTimestamp(datestring):
    try:
        date_object = time.strptime(datestring, "%Y-%m-%d %H:%M:%S")
        message = "%02i-%02i-%04i %02i:%02i" %(date_object[2], date_object[1], date_object[0], date_object[3], date_object[4])
    except ValueError:
        message = "Timestamp error"
    return message

def ConvertTimestampTable(datestring):
        #used for the sorted table
    date_object = time.strptime(datestring, "%Y-%m-%d %H:%M:%S")
    return "%04i-%02i-%02i" %(date_object[0], date_object[1], date_object[2])

def CheckMobileDevice(req_useragent):
    for MUA in autosub.MOBILEUSERAGENTS:
        if MUA.lower() in req_useragent.lower():
            return True
    return False

def getAttr(name):
    def inner_func(o):
        try:
            rv = float(o[name])
        except ValueError:
            rv = o[name]
        return rv
    return inner_func