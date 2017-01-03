#
# The Autosub helper functions
#

import logging
import re
import subprocess
import json
import zipfile, StringIO, urllib,filecmp

from string import capwords
import time
import urllib
import codecs
import os,sys
from ast import literal_eval
import library.requests as requests
from library import version
from autosub.version import autosubversion
import autosub
import Tvdb
from distutils.dir_util import copy_tree
from distutils.dir_util import remove_tree
from autosub.Db import idCache
import autosub.ID_lookup
from autosub.Addic7ed import Addic7edAPI

# Settings
log = logging.getLogger('thelogger')

REGEXES = [
        re.compile("^((?P<title>.+?)[. _-]+)?s(?P<season>\d+)[x. _-]*e(?P<episode>\d+)(([. _-]*e|-)(?P<extra_ep_num>(?!(1080|720)[pi])\d+))*[. _-]*((?P<quality>(1080|720|SD))*[pi]*[. _-]*(?P<source>(hdtv|dvdrip|bdrip|blu[e]*ray|web[. _-]*dl))*[. _]*(?P<extra_info>.+?)((?<![. _-])-(?P<releasegrp>[^-]+))?)?$", re.IGNORECASE),
        re.compile("^((?P<title>.+?)[\[. _-]+)?(?P<season>\d+)x(?P<episode>\d+)(([. _-]*x|-)(?P<extra_ep_num>(?!(1080|720)[pi])\d+))*[. _-]*((?P<quality>(1080|720|SD))*[pi]*[. _-]*(?P<source>(hdtv|dvdrip|bdrip|blu[e]*ray|web[. _-]*dl))*[. _]*(?P<extra_info>.+?)((?<![. _-])-(?P<releasegrp>[^-]+))?)?$", re.IGNORECASE),
        re.compile("^(?P<title>.+?)[. _-]+(?P<season>\d{1,2})(?P<episode>\d{2})([. _-]*(?P<quality>(1080|720|SD))*[pi]*[. _-]*(?P<source>(hdtv|dvdrip|bdrip|blu[e]*ray|web[. _-]*dl))*[. _]*(?P<extra_info>.+?)((?<![. _-])-(?P<releasegrp>[^-]+))?)?$", re.IGNORECASE)
        ]
SOURCE_PARSER = re.compile("(hdtv|tv|dvdrip|dvd|brrip|bdrip|blu[e]*ray|web[. _-]*dl)", re.IGNORECASE)
QUALITY_PARSER = re.compile("(1080|720|HD|SD)" , re.IGNORECASE)
LOG_PARSER = re.compile('^((?P<date>\d{4}\-\d{2}\-\d{2})\ (?P<time>\d{2}:\d{2}:\d{2},\d{3}) (?P<loglevel>\w+))', re.IGNORECASE)

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
            log.error("_getShow: Error while processing: %s %s" %(searchName, suffix))
            return searchName, suffix
        
        if m:
            searchName = m.group(1)
            suffix = m.group(2)
            break
    return searchName, suffix


def RunCmd(cmd):
    process = subprocess.Popen(cmd,
                            shell = True,
                            stdin = subprocess.PIPE,
                            stdout = subprocess.PIPE,
                            stderr = subprocess.PIPE)
    shell = process.stdout.read()
    shellerr = process.stderr.read()
    process.wait()
    return shell, shellerr

def CheckVersion():
    '''
    CheckVersion
    Return values:
    Current Release Number
    GitHub Release number
    '''

    GithubVersion = None
    try:
        response = requests.get(autosub.VERSIONURL)
        Temp = response.text.split("'")
        if 'Alpha' in Temp[1]:
            GithubVersion = Temp[1].split(' ')[1]
        else:
            GithubVersion = Temp[1]
    except Exception as error:
        log.error('CheckVersion: Problem getting the version form github. Error is: %s' % error)
        GithubVersion ='0.0.0'

    return GithubVersion

def RebootAutoSub():
    args =[]
    args = sys.argv[:]
    args.insert(0, sys.executable)
    args.append('-u')
    log.info('RebootAutoSub: Now restarting autosub...')
    log.debug('RebootAutoSub: Python exec arguments are %s,  %s' %(sys.executable,args))
    os.execv(sys.executable, args)


def UpdateAutoSub():
    '''
    Update Autosub.
    '''

    log.debug('UpdateAutoSub: Update started')

    # Piece of Code to let you test the reboot of autosub after an update, without actually updating anything
    #RestartTest = True
    #if RestartTest:
    #    log.debug('UpdateAutoSub: Module is in restart Test mode')
    #    args = []
    #    args = sys.argv[:]
    #    args.insert(0, sys.executable)
    #    args.append('-u')
    #    time.sleep(5)
    #    log.debug('UpdateAutoSub: Python exec arguments are %s' %(args))
    #    os.execv(sys.executable, args)
    # Get the version number from github
    GithubVersion = CheckVersion()
    if autosub.VERSION >= int(GithubVersion.split('.')[0]) * 1000 + int(GithubVersion.split('.')[1]) * 100 + int(GithubVersion.split('.')[2]) * 10:
        message = 'No update available. Current version: ' + autosubversion + '. GitHub version: ' + GithubVersion
        log.info('UpdateAutoSub: %s' % message)
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
        log.error('UpdateAutoSub: Could not get the zipfile from github. Error is %s' % error)
        return error
    log.debug('UpdateAutoSub: Zipfile located on Github')

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
                    log.debug('UpdateAutoSub: Problem removing old release folder. Error is: %s' %error)
                    return error
        else:
            return 'No correct zipfile could be downloaded'
        Result = zf.extractall(autosub.PATH)
        log.debug('UpdateAutoSub: Zipfile extracted')
    except Exception as error:
        log.error('UpdateAutoSub: Problem extracting zipfile from github. Error is %s' % error)
        return

    # copy the release 
    try:
    	copy_tree(ReleasePath,autosub.PATH)
    except Exception as error:
        log.error('UpdateAutoSub: Could not(fully) copy the updated tree. Error is %s' % error)
        return error
    log.debug('UpdateAutoSub: updated tree copied.')

    # remove the release folder after the update
    if os.path.isdir(ReleasePath):
        try:
            remove_tree(ReleasePath)
        except Exception as error:
            log.error('UpdateAutoSub: Problem removing old release folder. Error is: %s' % error)
            return error
    args =[]
    args = sys.argv[:]
    args.insert(0, sys.executable)
    args.append('-u')
    log.info('UpdateAutoSub: Update to version %s. Now restarting autosub...' % GithubVersion)
    log.debug('UpdateAutoSub: Python exec arguments are %s,  %s' %(sys.executable,args))
    os.execv(sys.executable, args)

def UpdateA7IdMapping():
# Get the latest id mapping for Addic7ed from github
    with requests.Session() as GithubSession:
        try:
            Result = GithubSession.get(autosub.ADDICMAPURL)
            Result.encoding ='utf-8'
            GithubMapping = {}
            GithubMapping = json.loads(Result.text)
            if GithubMapping:
                LastAddicId = GithubMapping[max(GithubMapping, key=GithubMapping.get)]
                if int(LastAddicId) > int(autosub.ADDICHIGHID):
                    autosub.ADDICHIGHID = LastAddicId
                    log.debug('UpdateNameMapping: Addic7ed Id mapping is updated.')
                    for NameMap in GithubMapping.iterkeys():
                        if NameMap.isdigit() and GithubMapping[NameMap].isdigit():
                            if not NameMap in autosub.ADDIC7EDMAPPING.keys():
                                autosub.ADDIC7EDMAPPING[NameMap] = GithubMapping[NameMap]
                        else:
                            log.debug('UpdateNameMapping: Addic7ed namemapping from github is coruptted. %s = %s' %(NameMap,GithubMapping[NameMap])) 
        except Exception as error:
            log.debug('UpdateA7IdMapping: Problem get AddicIdMapping from github. %s' % error)
    return

def CleanSerieName(series_name):
    """Clean up series name by removing any . and _
    characters, along with any trailing hyphens.

    Is basically equivalent to replacing all _ and . with a
    space, but handles decimal numbers in string, for example:

    >>> cleanRegexedSeriesName("an.example.1.0.test")
    'an example 1.0 test'
    >>> cleanRegexedSeriesName("an_example_1.0_test")
    'an example 1.0 test'

    Stolen from dbr's tvnamer
    """
    try:
        series_name = re.sub("(\D)\.(?!\s)(\D)", "\\1 \\2", series_name)
        series_name = re.sub("(\d)\.(\d{4})", "\\1 \\2", series_name)  # if it ends in a year then don't keep the dot
        series_name = re.sub("(\D)\.(?!\s)", "\\1 ", series_name)
        series_name = re.sub("\.(?!\s)(\D)", " \\1", series_name)
        series_name = series_name.replace("_", " ")
        series_name = re.sub("-$", "", series_name)
        
        words = [x.strip() for x in series_name.split()]
        tempword=[]
        for word in words:
            if not word.isupper():
                word = capwords(word)
            tempword.append(word)
        new_series_name = " ".join(tempword)

        return new_series_name.strip()
    except TypeError:
        log.debug("CleanSerieName: There is no SerieName to clean")


def ReturnUpper(text):
    """
    Return the text converted to uppercase.
    When not possible return nothing.
    """
    try:
        text = text.upper()
        return text
    except:
        pass

def matchQuality(quality, item):
    if quality == u"SD":
        if re.search('720', item):
            log.debug("matchQuality: Quality SD did not match to %s" % item)
            return None
        elif re.search('1080', item):
            log.debug("matchQuality: Quality SD did not match to %s" % item)
            return None
        else:
            log.debug("matchQuality: Quality matched SD to %s" % item)
            return 1
    elif quality == u"1080p" and re.search('1080', item):
        log.debug("matchQuality: Quality is 1080 matched to %s" % item)
        return 1
    elif quality == u"720p" and re.search('720', item):
        log.debug("matchQuality: Quality is 720 matched to %s" % item)
        return 1


def scoreMatch(release, wanted):
    """
    Return how high the match is. Currently 15 is the best match
    This function give the flexibility to change the most important attribute for matching or even give the user the possibility to set his own preference
    release is the filename as it is in the result from used websites
    If source is matched, score is increased with 8
    If quality is matched, score increased with 4
    If codec is matched, score is increased with 2
    If releasegroup is matched, score is increased with 1
    """

    score = int(0)
    if 'source' in release.keys() and 'source' in wanted.keys():
        if release['source']  == wanted['source']:
            score += 8
    if 'quality' in release.keys() and 'quality' in wanted.keys():
        if release['quality'] == wanted['quality']: 
            score += 4
        elif wanted['quality'] == '720p' and  release['quality'] == '1080p':
            score += 4
        elif wanted['quality'] == '1080p'  and release['quality'] == '720p'  :
            score += 4
    if 'codec' in release.keys() and 'codec' in wanted.keys():
        if release['codec']  == wanted['codec']:
            score += 2
    if 'releasegrp' in release.keys() and 'releasegrp' in wanted.keys():
        if release['releasegrp']  == wanted['releasegrp']:
            score += 1
    return score


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
                            log.debug("SkipShow: variable of %s is set to -1, skipping the complete Serie" % showName)
                            return True
                        try:
                            toskip = literal_eval(value)
                        except:
                            log.error("SkipShow: %s is not a valid parameter, check your Skipshow settings" % seasontmp)
                            continue
                        # Skip specific season:
                        if isinstance(toskip, int):
                            if int(season) == toskip:
                                log.debug("SkipShow: Season %s matches variable of %s, skipping season" % (season, showName))
                                return True
                        # Skip specific episode
                        elif isinstance(toskip, float):
                            seasontoskip = int(toskip)
                            episodetoskip = int(round((toskip-seasontoskip) * 100))
                            if int(season) == seasontoskip:
                                if episodetoskip == 0:
                                    log.debug("SkipShow: Season %s matches variable of %s, skipping season" % (season, showName))
                                    return True
                                elif int(episode) == episodetoskip:
                                    format = season + 'x' + episode
                                    log.debug("SkipShow: Episode %s matches variable of %s, skipping episode" % (format, showName))
                                    return True
        except:
            log.error('SkipShow: Problem with SkipShow, check the format in the settings.')
            return False


def checkAPICallsSubSeeker(use=False):
    """
    Checks if there are still API calls left
    Set true if a API call is being made.
    """
    currentime = time.time()
    lastrun = autosub.APICALLSLASTRESET_SUBSEEKER
    interval = autosub.APICALLSRESETINT_SUBSEEKER
    
    if currentime - lastrun > interval:
        log.info("API SubtitleSeeker: 24h limit, resetting API calls.")
        autosub.APICALLS_SUBSEEKER = autosub.APICALLSMAX_SUBSEEKER
        autosub.APICALLSLASTRESET_SUBSEEKER = time.time()
    
    if autosub.APICALLS_SUBSEEKER > 0:
        if use==True:
            autosub.APICALLS_SUBSEEKER-=1
        return True
    else:
        return False
        
def checkAPICallsTvdb(use=False):
    """
    Checks if there are still API calls left
    Set true if a API call can be made.
    """
    currentime = time.time()
    lastrun = autosub.APICALLSLASTRESET_TVDB
    interval = autosub.APICALLSRESETINT_TVDB
    
    if currentime - lastrun > interval:
        log.info("API TVDB: 24h limit, resetting API calls.")
        autosub.APICALLS_TVDB = autosub.APICALLSMAX_TVDB
        autosub.APICALLSLASTRESET_TVDB = time.time()
    
    if autosub.APICALLS_TVDB > 0:
        if use==True:
            autosub.APICALLS_TVDB-=1
        return True
    else:
        log.debug('checkAPICallsTvdb: Out of API calls for Tvdb')
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
    log.debug('getShowid: Trying to get info for %s' %ShowName)
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
                    elif checkAPICallsTvdb():
                        # still no tvdb name we fetch it form the tvdb website
                        TvdbShowName,TvdbId = Tvdb.getShowName(ImdbNameMappingId)
                        if TvdbShowName:
                            autosub.NAMEMAPPING[Name.upper()][1] = TvdbShowName
        else:
            # Not found in NameMapping so check the cache
            ImdbId, AddicId, TvdbId, TvdbShowName = idCache().getId(Name.upper())
            # No info in the cache we try Tvdb
            if not ImdbId and checkAPICallsTvdb():
                ImdbId, TvdbId, TvdbShowName = Tvdb.getShowidApi(Name)  
                if ImdbId:
                    UpdateCache = True
        if (ImdbNameMappingId or ImdbId):
            if not AddicId:
                Id = ImdbNameMappingId if ImdbNameMappingId else ImdbId
                if Id:
                    if Id in autosub.ADDIC7EDMAPPING.keys():
                        AddicId = autosub.ADDIC7EDMAPPING[Id]
                    elif Id in autosub.USERADDIC7EDMAPPING.keys():
                        AddicUserId = autosub.USERADDIC7EDMAPPING[Id]
                    elif autosub.ADDIC7EDLOGGED_IN:
                        AddicId = Addic7edAPI().geta7ID(ShowName, TvdbShowName)
                        if AddicId and ImdbId:
                            UpdateCache = True
            break
    if UpdateCache:
        idCache().setId(TvdbShowName.upper(), ImdbId, AddicId, TvdbId, TvdbShowName)
    if ImdbNameMappingId: ImdbId = ImdbNameMappingId
    if not TvdbShowName: TvdbShowName = ShowName
    if AddicUserId: AddicId = AddicUserId
    log.debug("getShowid: Returned ID's - IMDB: %s, Addic7ed: %s, ShowName: %s" %(ImdbId,AddicId,TvdbShowName))
    return ImdbId, AddicId, TvdbId, TvdbShowName
    # no ImdbId found for this showname
    log.debug('getShowid: No ImdbId found on Tvdb for %s.' % ShowName)
    return None, None, None, ShowName



def DisplayLogFile(loglevel):
    maxLines = 500
    data = []
    if os.path.isfile(autosub.LOGFILE):
        f = codecs.open(autosub.LOGFILE, 'r', autosub.SYSENCODING)
        data = f.readlines()
        f.close()
    
    finalData = []
    
    numLines = 0
    
    for x in reversed(data):
        try:
            matches = LOG_PARSER.search(x)
            matchdic = matches.groupdict()
            if (matchdic['loglevel'] == loglevel.upper()) or (loglevel == ''):
                numLines += 1
                if numLines >= maxLines:
                    break
                finalData.append(x)
        except:
            continue
    result = "".join(finalData)
    return result

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
                log.error('DisplaySubtitle: Permission Denied on %s' %subtitlefile)
            else: 
                result = "There was a problem with loading the subtitle."
                log.error('DisplaySubtitle: There was a problem with loading %s' %subtitlefile)
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

# Thanks to: http://stackoverflow.com/questions/1088392/sorting-a-python-list-by-key-while-checking-for-string-or-float
def getAttr(name):
    def inner_func(o):
        try:
            rv = float(o[name])
        except ValueError:
            rv = o[name]
        return rv
    return inner_func

#class API:
#    """
#    One place to rule them all, a function that handels all the request to the servers

#    Keyword arguments:
#    url - the URL that is requested
    
#    """
#    def __init__(self,url):
#        self.errorcode = None        
#        self.req = None
#        self.req = urllib2.Request(url)
#        self.req.add_header("User-agent", autosub.USERAGENT)
#        self.connect()
        
#    def connect(self):
#        import socket
#        socket.setdefaulttimeout(autosub.TIMEOUT)
        
#        try:
#            self.resp = urllib2.urlopen(self.req)
#            self.errorcode = self.resp.getcode()
#        except urllib2.HTTPError, e:
#            self.errorcode = e.getcode()
        
#        if self.errorcode == 200:
#            log.debug("API: HTTP Code: 200: OK!")
#        elif self.errorcode == 429:
#            # don't know if this code is valid for subtitleseeker
#            log.debug("API: HTTP Code: 429 You have exceeded your number of allowed requests for this period.")
#            log.error("API: You have exceeded your number of allowed requests for this period. (1000 con/day))")
#            log.warning("API: Forcing a 1 minute rest to relieve subtitleseeker.com. If you see this info more then once. Cleanup your wanted list!")
#            time.sleep(54)
#        elif self.errorcode == 503:
#            log.debug("API: HTTP Code: 503 You have exceeded your number of allowed requests for this period (MyMovieApi).")
#            log.error("API: You have exceeded your number of allowed requests for this period. (either 30 con/m or 2500 con/day))")
#            log.warning("API: Forcing a 1 minute rest to relieve mymovieapi.com. If you see this info more then once. Cleanup your wanted list!")
#            time.sleep(54)
        
#        log.debug("API: Resting for 6 seconds to prevent 429 errors")
#        time.sleep(6) #Max 0.5 connections each second
    
#    def close(self):
#        self.resp.close()