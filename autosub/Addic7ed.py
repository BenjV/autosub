#
# The Addic7ed method specific module
#

import re
import library.requests as requests
import library.requests.packages.chardet as chardet
import time
import sys
import urllib
import autosub
import autosub.Helpers
import autosub.Tvdb
from autosub.common import source,source_syn,quality,quality_syn,codec,codec_syn,rlsgrps_rest,rlsgrps_HD,rlsgrps_xvid,rlsgrps_webdl
from itertools import product


import logging

log = logging.getLogger('thelogger')


#Every part of the file_info got a list with regex. The first item in this list should be the standardnaming
#The second (and following) regex contains nonstandard naming (either typo's or other renaming tools (like sickbeard)) 
#Nonstandard naming should be renamed using the syn dictionary. 

_show = [re.compile('(.+)\s+\(?(\d{4})\)?', re.IGNORECASE),
              re.compile('(.+)\s+\(?(us)\)?', re.IGNORECASE),
              re.compile('(.+)\s+\(?(uk)\)?', re.IGNORECASE)]

def _regexRls(releaseGroupList, list=False):
    releasegrp_pre = '(' + '|'.join(releaseGroupList) + ')'
    regexReleasegrp = [re.compile(releasegrp_pre, re.IGNORECASE)]
    
    if list: return regexReleasegrp
    else: return regexReleasegrp.pop()

def _returnHits(regex, version_info):
    # Should have been filter out beforehand
    results=[]
    if not version_info:
        results.append(u'')        
        return results
    
    for reg in regex:
        results = re.findall(reg, version_info)
        if results:
            results = [x.lower() for x in results]
            results = [re.sub("[. _-]", "-", x) for x in results]
            break
    return results
        
                    
def _checkSynonyms(synonyms, results):
    for index, result in enumerate(results):
        if result in synonyms.keys() and synonyms[result]:
            results[index] = synonyms[result].lower()
        else: continue
    return results


def _getSource(file_info):
    results = _checkSynonyms(source_syn,
                            _returnHits(source, file_info))
    return results

def _getQuality(file_info, HD):
    results = _checkSynonyms(quality_syn,
                            _returnHits(quality, file_info))
    return results

def _getCodec(file_info):
    results = _checkSynonyms(codec_syn,
                            _returnHits(codec, file_info))
    
    return results

def _getReleasegrp(file_info):
    results = _returnHits(_regexRls(rlsgrps_rest + rlsgrps_HD + rlsgrps_xvid + rlsgrps_webdl, list=True), file_info)
    
    return results


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


def _ParseVersionInfo(version_info, HD):
    # Here the information in the a7 version columns get grouped 
    # Either source, quality, codec or releasegroup
    
    sourceList = _getSource(version_info)
    qualityList = _getQuality(version_info, HD)
    codecList = _getCodec(version_info)
    releasegroupList = _getReleasegrp(version_info)
    
    parametersList = [sourceList, qualityList, codecList, releasegroupList]   
    return parametersList

    
def _checkIfParseable(parametersList):
    # only 1 paramter list can contain more than 1 element
    for index,parameter in enumerate(parametersList):
        if len(parameter) > 1:
            tempLists = parametersList[:]
            tempLists.pop(index)
            for tempList in tempLists:
                if len(tempList) > 1:
                    return True
    return False


def _checkConflicts(versionDicts):
# Check if data is consistent in the dict
# If inconsistent, remove this dict
    toDelete = []
    for index, versionDict in enumerate(versionDicts):
        source = versionDict['source']
        quality = versionDict['quality']
        codec = versionDict['codec']
        releasegroup = versionDict['releasegrp']
        
        # The following combinations are inconsistent
        
    
        # Based on source
        if source == u'web-dl':
            if codec == u'xvid':
                toDelete.append(index)
                continue
        

        # Based on releasegroup
        if releasegroup:
            if re.match(_regexRls(rlsgrps_HD + rlsgrps_xvid), releasegroup):
                if source == u'web-dl':
                    toDelete.append(index)
                    continue
            if re.match(_regexRls(rlsgrps_HD + rlsgrps_webdl) , releasegroup):
                if codec == u'xvid':
                    toDelete.append(index)
                    continue
            if re.match(_regexRls(rlsgrps_HD + rlsgrps_webdl), releasegroup):
                if quality == u'sd':
                    toDelete.append(index)
                    continue
            if re.match(_regexRls(rlsgrps_xvid), releasegroup):
                if codec == u'h264':
                    toDelete.append(index)
                    continue
    
    # Delete duplicate indices
    toDelete = sorted(set(toDelete))    
    i = len(toDelete) -1
    
    while i>=0:
        versionDicts.pop(toDelete[i])
        i=i-1
    return versionDicts   

def _addInfo(versionDicts,HD):
    # assume missing codec is x264, error prone!
    for index, versionDict in enumerate(versionDicts):
        source = versionDict['source']
        quality = versionDict['quality']
        codec = versionDict['codec']
        releasegroup = versionDict['releasegrp']
    
        # Based on quality
        # Removed this one because 1080p is also available in HDTV now a day
        #if quality == u'1080p':
        #    if not source:
        #        versionDicts[index]['source'] = u'web-dl'

    
        # Based on source
        if any(source == x for x in (u'web-dl', u'hdtv', u'bluray')):
            if not codec:
                versionDicts[index]['codec'] = u'h264'
        if source == u'web-dl':
            # default quality for WEB-DLs is 720p
            if not quality:
                versionDicts[index]['quality'] = u'720p'

        # Based on specific Releasegroups  
        if releasegroup:
            if not codec:
                if re.match(_regexRls(rlsgrps_HD + rlsgrps_webdl), releasegroup):
                    versionDicts[index]['codec'] = u'h264'
                if re.match(_regexRls(rlsgrps_xvid), releasegroup):
                    versionDicts[index]['codec'] = u'xvid'
            if not source:
                if re.match(_regexRls(rlsgrps_webdl), releasegroup):
                    versionDicts[index]['source'] = u'web-dl'
                elif re.match(_regexRls(rlsgrps_HD), releasegroup):
                    versionDicts[index]['source'] = u'hdtv'
                else:
                    if quality == u'1080p' or quality == u'720p':
                        versionDicts[index]['source'] = u'web-dl'
                    elif HD:
                         versionDicts[index]['source'] = u'hdtv'
            if not quality:
                if re.match(_regexRls(rlsgrps_HD + rlsgrps_webdl), releasegroup):
                    versionDicts[index]['quality'] = u'720p'
    return versionDicts


def _MakeTwinRelease(originalDict):
    # This modules creates the SD/HD counterpart for releases with specific releasegroups
    # DIMENSION <> LOL
    # IMMERSE <> ASAP
    # 2HD <> 2HD 720p
    # BiA <> BiA 720p
    # FoV <> FoV 720p
    
    rlsgroup = originalDict['releasegrp']
    qual = originalDict['quality']
    source = originalDict['source']
    
    rlsSwitchDict = {u'dimension' : u'lol',
                     u'lol': u'dimension',
                     u'immerse': u'asap',
                     u'asap' : u'immerse',
                     u'2hd' : u'2hd',
                     u'bia' : u'bia',
                     u'fov' : u'fov'}
    
    qualSwitchDict_hdtv = {u'sd' : u'720p',
                           u'720p' : u'sd',
                           u'1080p' : u'720p',
                           u'480p' : u'720p'}
    
    qualSwitchDict_webdl =  {u'1080p' : u'720p',
                             u'720p' : u'1080p'}
    
    twinDict = originalDict.copy()
    if rlsgroup in rlsSwitchDict.keys():
        twinDict['releasegrp'] = rlsSwitchDict[rlsgroup]
        twinDict['quality'] = qualSwitchDict_hdtv[qual]
   
    # WEB-DLs 720p and 1080p are always synced
    if source == 'web-dl' and qual in qualSwitchDict_webdl.keys():
        twinDict['quality'] = qualSwitchDict_webdl[qual]
    
    diff = set(originalDict.iteritems())-set(twinDict.iteritems())
    
    if len(diff):
        return twinDict
    else:
        return None  
    

def ReconstructRelease(version_info, HD):
    # This method reconstructs the original releasename    
    # First split up all components
    parametersList = _ParseVersionInfo(version_info, HD)

    #First check for unresolvable versions (eg 3 sources combined with multiple qualities)
    problem = _checkIfParseable(parametersList)
    if problem:
        return False
      
    releasegroups = parametersList.pop()
    codecs = parametersList.pop()
    qualities = parametersList.pop()
    sources = parametersList.pop()
    
    for x in [sources, qualities, codecs, releasegroups]:
        if not x: x.append(None)
       
    # Make version dictionaries
    # Do a cartessian product    
    versionDicts = [
    {'source': sour, 'quality': qual, 'codec': cod, 'releasegrp': rls}
    for sour, qual, cod, rls in product(sources, qualities, codecs, releasegroups)
    ]

    
    # Check for conflicting entries
    versionDicts = _checkConflicts(versionDicts)
    if not versionDicts:
        return False

    # Fill in the gaps
    versionDicts = _addInfo(versionDicts, HD)

    twinDicts = []
    for originalDict in versionDicts:
        twinDict = _MakeTwinRelease(originalDict)
        if twinDict:
            twinDicts.append(twinDict)
    
    versionDicts.extend(twinDicts)
    
    return versionDicts


def makeReleaseName(versionInfo, title, season, episode):
    version = versionInfo.replace(' ','.')
    se = 'S' + season + 'E' + episode
    release = '.'.join([title,se,version])
    return release

    
class Addic7edAPI():
    def __init__(self):
        self.session = requests.Session()
        self.server = 'http://www.addic7ed.com'
        self.session.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Trident/7.0; rv:11.0) like Gecko', 'Referer' : 'http://www.addic7ed.com', 'Pragma': 'no-cache'}
                
    def login(self, addic7eduser=None, addic7edpasswd=None):        

        # Expose to test login
        # When fields are empty it will check the config file

        if addic7eduser or addic7edpasswd:
            Test = True
        else:
            Test = False
            addic7eduser   = autosub.ADDIC7EDUSER
            addic7edpasswd = autosub.ADDIC7EDPASSWD


        data = {'username': addic7eduser, 'password': addic7edpasswd, 'Submit': 'Log in'}
        try:
            r = self.session.post(self.server + '/dologin.php', data, timeout=10, allow_redirects=False)
        except Exception as error:
            log.error('Addic7edAPI: %s' % error)
            return False
        
        if r.status_code == 302:
            autosub.ADDIC7EDLOGGED_IN = True
            if self.checkCurrentDownloads():
                if Test:
                    log.info('Addic7edAPI: Test Logged in as: %s' % addic7eduser)
                    self.logout()
                else:
                    log.debug('Addic7edAPI: Logged in as: %s' % addic7eduser)
                return True
            else:
                log.info('Addic7edAPI: Could not login with username: %s' % addic7eduser)
                autosub.ADDIC7EDLOGGED_IN = False
                return False
        else:
            log.error('Addic7edAPI: Failed to login')
            autosub.ADDIC7EDLOGGED_IN = False
            return False

    def logout(self):
        if autosub.ADDIC7EDLOGGED_IN:
            autosub.ADDIC7EDLOGGED_IN = False
            try:
                r = self.session.get(self.server + '/logout.php', timeout=10)
                log.debug('Addic7edAPI: Logged out')
            except Exception as error:
                log.error('Addic7edAPI: %s' % error)
                return None
            
            if r.status_code != 200:
                log.error('Addic7edAPI: Request failed with status code %d' % r.status_code)
        self.session.close()

    def get(self, url, login=True):
        """
        Make a GET request on `url`
        :param string url: part of the URL to reach with the leading slash
        :rtype: text
        """
        time.sleep(10)
        try:
            r = self.session.get(self.server + url, timeout=15)
            r.encoding ='utf-8'
        except Exception as error:
            log.error('Addic7edAPI: Unexpected error: %s' % error)
            return None    
        
        if r.status_code > 399:
            log.error('Addic7edAPI: Request failed with status code %d' % r.status_code)
            return None
        return r.text

    def download(self, downloadlink):
        if not autosub.ADDIC7EDLOGGED_IN:
            log.error("Addic7edAPI: You are not properly logged in. Check your credentials!")
            return None
        log.debug("Addic7edAPI: Resting for 10 seconds to prevent a ban")
        time.sleep(10)
        try:
            r = self.session.get(self.server + downloadlink, timeout=10)
        except Exception as error:
            log.error('Addic7edAPI: %s' % error)
            return None
        except:
            log.error('Addic7edAPI: Unexpected error: %s' % sys.exc_info()[0])
            return None

        if r.status_code > 399:
            log.error('Addic7edAPI: Request failed with status code %d' % r.status_code)
        else:
            autosub.DOWNLOADS_A7 += 1
            log.debug('Addic7edAPI: Request successful downloaded a sub with status code %d' % r.status_code)
            if time.time() > autosub.DOWNLOADS_A7TIME + 43200:
                self.checkCurrentDownloads()
        if r.headers['Content-Type'] == 'text/html':
            log.error('Addic7edAPI: Expected srt file but got HTML; report this!')
            log.debug("Addic7edAPI: Response content: %s" % r.text)
            return None
        if 'UTF' in r.apparent_encoding.upper():
            r.encoding = r.apparent_encoding
        else:
            r.encoding = u'windows-1252'
        return r.text
    
    def checkCurrentDownloads(self):
        #if not autosub.ADDIC7EDLOGGED_IN:  
        #    self.login()
        
        time.sleep(10)
        try:
            PageBuffer = self.get('/panel.php')
            if re.findall(autosub.ADDIC7EDUSER,PageBuffer):
                Temp = re.findall(r'<a href=[\'"]mydownloads.php\'>([^<]+)', PageBuffer)[0].split(" ")
                autosub.DOWNLOADS_A7 = int(Temp[0])
                autosub.DOWNLOADS_A7MAX = int(Temp[2])
                autosub.DOWNLOADS_A7TIME = time.time()
                log.debug('Addic7edAPI: Current download count for today on addic7ed is: %d' % autosub.DOWNLOADS_A7)
            else:
                log.error("Addic7edAPI: Couldn't retrieve Addic7ed account info for %s. Maybe not logged in." % autosub.ADDIC7EDUSER)
                return False
        except Exception as error:
            log.error("Addic7edAPI: Couldn't retrieve Addic7ed account info. Error is: %s" % error.message)
            return False
        return True    
    
    def geta7ID(self,ShowName, TvdbShowName):
        # lookup official name and try to match with a7 show list


        try:
            Result = self.session.get(self.server + '/shows.php',timeout=20)
            Result.encoding ='utf-8'
            html = Result.text
        except Exception as error:
            log.debug('geta7ID: Problem tring to get the addic7ed show page. Message is: %s' % error)
            return None
        if not html:
            log.debug('geta7ID: Could not get the show page form the addic7ed website')
            return None
        #Put the showname's and Addic7ed's in a dict with the showname as key.
        show_ids={}
        AddicName = u''
        for url in re.findall(r'<a href=[\'"]/show/?([^<]+)', html, flags=re.IGNORECASE):
            AddicId = url.split("\">")[0]
            if AddicId.isdigit():
                try:
                    AddicName = url.split("\">")[1].replace('&amp;','&').lower()
                    show_ids[AddicName] = AddicId
                except:
                    pass

        # here we make a list of possible combinations of names and suffixes
        SearchList = []
        #First the file Show name from the parameterlist 
        if ShowName:
            SearchList.append(ShowName)
            # If there is a suffix add the combinations of suffixes e.g. with and without ()
            SearchName, Suffix = _getShow(ShowName)
            if Suffix:
                SearchList.append(SearchName)
                if '(' + Suffix +')' in ShowName:
                    SearchList.append(SearchName + ' ' + Suffix)
                else:
                    SearchList.append(SearchName + '(' + Suffix + ')')

        # If the Tvdb showname is different then we do the same for that name
        if TvdbShowName and TvdbShowName != ShowName:
            if TvdbShowName not in SearchList:
                SearchList.append(TvdbShowName)
            SearchName, Suffix = _getShow(TvdbShowName)
            if Suffix:
                if SearchName not in SearchList:
                    SearchList.append(SearchName)
                if '(' + Suffix +')' in TvdbShowName :
                    SearchList.append(SearchName + ' ' + Suffix)
                else:
                    SearchList.append(SearchName + ' (' + Suffix + ')')

        # Try all the combinations untill we find one
        for Name in SearchList:
            if Name.lower() in show_ids:
                log.debug("geta7IDApi: Addic7ed ID %s found using filename show name %s" % (show_ids[Name.lower()], ShowName))
                return show_ids[Name.lower()]

        log.info('geta7ID: The show %s could not be found on the Addic7ed website. Please make an Addic7ed map!' % ShowName)
        return None
