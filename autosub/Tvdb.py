# 
# Autosub Tvdb.py 
#
# The Tvdb API V1 and V2 module
#

from logging import getLogger
import requests
from json import dumps
from time import time
from urllib import quote
from difflib import SequenceMatcher as SM
try:
    import xml.etree.cElementTree as ET
except:
    import xml.etree.ElementTree as ET
import autosub
from datetime import date

# Settings
log = getLogger('thelogger')

def _checkToken():
    # if token expired or no token available, get a new token
    if time() - autosub.TVDBTIME > 86400 or 'Authorization' not in autosub.TVDBSESSION.headers:
       return GetToken()
    # if token is about to expire refresh the token lease time
    elif time() - autosub.TVDBTIME > 80000:
        autosub.TVDBTIME = time()
        TvdbResult = autosub.TVDBSESSION.get(autosub.TVDBAPI + 'refresh_token',data=autosub.TVDBSESSION.headers['Authorization'][7:]).json()
        if not 'Error' in TvdbResult and 'token' in TvdbResult:
            return True
        else:
            # token lease refresh failed so we try to get a new token.
            return GetToken()
    #Token is available and lease is not expired so everthing is ok
    return True


def _findName(ImdbId):
    if not _checkToken():
        return None, None
    Result = autosub.TVDBSESSION.get(autosub.TVDBAPI + 'search/series?imdbId=tt' + ImdbId, data=autosub.TVDBSESSION.headers['Authorization'][7:]).json()
    if 'Error' in Result:
        log.error("Tvdb returned an error: %s" % Result['Error'])
        return None, None
    return Result['data'][0]['seriesName'], str(Result['data'][0]['id'])


def _findId(ShowName):
    if not _checkToken():
        return None, None, None
    Result = autosub.TVDBSESSION.get(autosub.TVDBAPI + 'search/series?name=' + ShowName, data=autosub.TVDBSESSION.headers['Authorization'][7:]).json()
    if 'Error' in Result:
        log.debug("Tvdb returnd an error: %s" % Result['Error'])
        return None,None,None

    TvdbId = None
    HighName = None
    HighScore = 0
    for Data in Result['data']:
        Score = SM(None, Data['seriesName'].upper(), ShowName.upper()).ratio()
        if Score >= HighScore and Score > 0.666 :
            TvdbId = str(Data['id'])
            HighScore = Score
            HighName = Data['seriesName']
    if HighName:
        Result = autosub.TVDBSESSION.get(autosub.TVDBAPI + 'series/' + TvdbId, data=autosub.TVDBSESSION.headers['Authorization'][7:]).json()
        ImdbId = Result['data']['imdbId'][2:]
        TvdbId = str(Result['data']['id']).decode("utf-8")
        return ImdbId, TvdbId, HighName
    log.debug("Tvbd did not return a match for: %s" % ShowName)
    return None, None, None

def _FindImdbId(TvdbId):
   if not _checkToken():
        return False
   Result = autosub.TVDBSESSION.get(autosub.TVDBAPI + 'series/' + TvdbId, data=autosub.TVDBSESSION.headers['Authorization'][7:]).json()
   if 'Error' in Result:
       log.debug("Tvdb returnd an error: %s" % Result['Error'])
       return None,None,None
   return Result['data']['imdbId'][2:]


def _FindName(Url,Root,Tag):

    Found = TvdbId = None
    Session = requests.Session()
    try:
        Result = Session.get(Url)
    except:
        return None,None
    try:
        PageRoot = ET.fromstring(Result.content)
    except Exception as error:
        log.error("Error parsing info from Tvdb. Error =%s" %error)
        return None,None
    try:
        for node in PageRoot.findall(Root):
            try:
                Found = node.find(Tag).text
            except:
                log.error("Could not find %s in %s on Tvdb URL: % " % (Root,Tag,Url))
                log.error("Message is: " % error)
                return None,None
            if Found:
                try:
                    TvdbId = node.find('seriesid').text
                except:
                    pass
                return Found, TvdbId
            else:
                log.error("Could not find %s in %s on Tvdb URL: " % (Root,Tag,Url))
                return None, None
    except Exception as error:
        log.error("Could not find %s in %s on Tvdb URL: " % (Root,Tag,Url))
        log.error("Message is: " % error)
        return None, None
    log.error("Could not find %s in %s on Tvdb URL: " % (Root,Tag,Url))
    return None, None

def GetToken(user=None,id=None):
    auth_data = dict() 
    auth_data['apikey'] = autosub.TVDBAPIKEY
        # check if this is a test from the user interface or a normal call from autosub itself
    if user and id and (user != autosub.TVDBUSER or id != autosub.TVDBACCOUNTID) :
        Test = True
        auth_data['username'] = user
        auth_data['userkey']  = id
        log.info("Tvdb verification test with user: %s and code: %s" %(user,id))
    else:
        Test = False
        auth_data['username'] = autosub.TVDBUSER
        auth_data['userkey']  = autosub.TVDBACCOUNTID   
    Data = dumps(auth_data)
    TvdbResult = autosub.TVDBSESSION.post(autosub.TVDBAPI + 'login',data=Data).json()
    if 'Error' in TvdbResult:
        if Test:
            log.info('Message from Tvdb API is: "%s"' % TvdbResult['Error'])
        else:
            log.error('Error from Tvdb API is: "%s"' % TvdbResult['Error'])
        return False
        # Check if we got a token
    if 'token' in TvdbResult:
            # if not a Test from userinterface, store the data in the session header, otherwise ignore the data and just return success
        if not Test:
            autosub.TVDBTIME = time()
            autosub.TVDBSESSION.headers.update({"Authorization": "Bearer " + TvdbResult['token']})
        return True
    else:
        log.error("No Token returned from Tvdb API. Maybe connection problems?")
        return False


def GetTvdbId(showName):
    """
    Search for the IMDB ID by using the TvDB API and the name of the show.
    Keyword arguments:
    showName -- Name of the show to search the showid for
    """
    if autosub.TVDBACCOUNTID:
        if _checkToken() :
            return _findId(showName)
        else:
            return None,None,None
    elif date.today() >= date(2017,10,15):
        log.error('No account credentials found for Tvdb')
        return None,None,None

    Url = "%sGetSeries.php?seriesname=%s" % (autosub.TVDBSERVER, quote(showName.encode('utf8','xmlcharrefreplace')))
    Session = requests.Session()
    try:
        Result = Session.get(Url)
    except:
        log.debug('Problem connecting toTvdb. Check if the site is down')
        return None,None,None
    if not Result.ok:
        log.debug('No correct response from Tvdb. Check if the site is down')
        return None, None, None
    try:
        root = ET.fromstring(Result.content)
    except Exception as error:
        pass
    ImdbId = None
    TvdbId = None
    HighName = None
    HighScore = 0
    # Here we walk through al matches and try to find the best match.
    try:
        for node in root.findall('Series'):
            try:
                FoundName = node.find('SeriesName').text
                FoundName = FoundName.decode('utf-8') if isinstance(FoundName,str) else FoundName
                Score = SM(None, FoundName.upper(), showName.upper()).ratio()
                if Score >= HighScore:
                    ImdbId = None
                    try:
                        ImdbId = node.find('IMDB_ID').text[2:]
                        TvdbId = node.find('seriesid').text
                    except:
                        pass
                    if ImdbId:
                        HighScore = Score
                        HighName = FoundName
            except Exception as error:
                pass
    except Exception as error:
            log.error("Could not find %s in %s on Tvdb URL: " % (showName, Url))
            log.error("Message is: " % error)
    if ImdbId == '1489904':
        log.debug('Found a serie that is forbidden by Tvdb (1489904) so skipping it.')
        return None, None, None
    ImdbId = ImdbId.decode('utf-8') if isinstance(ImdbId,str) else ImdbId
    TvdbId = TvdbId.decode('utf-8') if isinstance(TvdbId,str) else TvdbId
    HighName = HighName.decode('utf-8') if isinstance(HighName,str) else HighName
    return ImdbId,TvdbId, HighName


def GetShowName(ImdbId):
    """
    Search for the official TV show name using the IMDB ID
    """
    if autosub.TVDBACCOUNTID:
        if _checkToken() :
            return _findName(ImdbId)
        else:
            return None,None
    else:
        if  date.today() < date(2017,10,1):
            return _FindName(autosub.TVDBSERVER + 'GetSeriesByRemoteID.php?imdbid=' + ImdbId, 'Series', 'SeriesName')
        else:
            log.error('Not Tvdb credentials found')
            return None,None


def FindNameById(Id, Sea, Ep):
    if not _checkToken():
        return False
    Cmd = autosub.TVDBAPI + 'series/%s/episodes/query?airedSeason=%s&airedEpisode=%s'%(Id,Sea,Ep)
    Result = autosub.TVDBSESSION.get(Cmd).json()
    if 'Error' in Result:
        log.debug("Tvdb returnd an error: %s" % Result['Error']) 
    return Result['data'][0]['episodeName']