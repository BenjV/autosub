# 
# Autosub Tvdb.py 
#
# The Tvdb API V2 module
#
from logging import getLogger
import library.requests as requests
from json import dumps
from time import time
from difflib import SequenceMatcher as SM
try:
    import xml.etree.cElementTree as ET
except:
    import xml.etree.ElementTree as ET
import autosub

log = getLogger('thelogger')

def _checkToken():
        # if token expired or no token available, get a new token
    if time() - autosub.TVDBTIME > 86400 or 'Authorization' not in autosub.TVDBSESSION.headers:
       return GetToken()
        # if token is about to expire refresh the token lease time
    elif time() - autosub.TVDBTIME > 80000:
        autosub.TVDBTIME = time()
        try:
            TvdbResult = autosub.TVDBSESSION.get(autosub.TVDBAPI + '/refresh_token',data=autosub.TVDBSESSION.headers['Authorization'][7:],timeout=10).json()
            if not 'Error' in TvdbResult and 'token' in TvdbResult:
                return True
            else:
                    # token lease refresh failed so we try to get a new token.
                return GetToken()
        except Exception as error:
            log.error(error.message)
            return False
        #Token is available and lease is not expired so everthing is ok
    return True

def GetToken(user=None,id=None):
    if not autosub.TVDBACCOUNTID:
        return False
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
        #auth_data['username'] = autosub.TVDBUSER
        #auth_data['userkey']  = autosub.TVDBACCOUNTID
    Data = dumps(auth_data)
    try:
        TvdbResult = autosub.TVDBSESSION.post(autosub.TVDBAPI + '/login',data=Data,verify=autosub.CERT,timeout=10).json()
        if 'Error' in TvdbResult:
            log.error('Error from Tvdb API is: "%s"' % TvdbResult['Error'])
            return False
            # Check if we got a token
        elif 'token' in TvdbResult:
                # if not a Test from userinterface, store the data in the session header, otherwise ignore the data and just return success
            if not Test:
                autosub.TVDBTIME = time()
                autosub.TVDBSESSION.headers.update({"Authorization": "Bearer " + TvdbResult['token']})
            return True
        else:
            log.error("No Token returned from Tvdb API. Maybe connection problems?")
            return False
    except Exception as error:
        log.error(error.message)
        return False

def GetTvdbId(ShowName):
    """
    Search for the IMDB ID by using the TvDB API and the name of the show.
    Keyword arguments:
    ShowName -- Name of the show to search the showid for
    """
    Name = ShowName.replace("&"," ")
    if not(autosub.TVDBACCOUNTID and _checkToken()) :
        return None, None, ShowName
    try:
        Result = autosub.TVDBSESSION.get(autosub.TVDBAPI + '/search/series?name=' + Name, verify=autosub.CERT,timeout=10).json()
        if 'Error' in Result:
            log.error("Tvdb returnd an error: %s" % Result['Error'])
            return None,None,ShowName
    except Exception as error:
        log.error(error.message)
        return None, None, ShowName

    HighScore = 0
    HighName = None
    for Data in Result['data']:
        Score = SM(None, Data['seriesName'], ShowName).ratio()
        if Score >= HighScore and Score > 0.666 :
            TvdbId = str(Data['id'])
            HighScore = Score
            HighName = Data['seriesName']
    Data = sorted(Data, key=itemgetter('score'), reverse=True)
    if HighName:
        try:
            Result = autosub.TVDBSESSION.get(autosub.TVDBAPI + '/series/' + TvdbId, data=autosub.TVDBSESSION.headers['Authorization'][7:],verify=autosub.CERT,timeout=10).json()
            if 'Error' in Result:
                log.error("Tvdb returned an error: %s" % Result['Error'])
                return None, None, ShowName
            else:
                ImdbId = Result['data']['imdbId'][2:] if len( Result['data']['imdbId']) > 2 else None
                TvdbId = str(Result['data']['id']).decode("utf-8") if Result['data']['id'] else None
                return ImdbId, TvdbId, HighName
        except Exception as error:
            log.error(error.message)
            return None, None, ShowName
    log.debug("Tvbd did not return a match for: %s" % ShowName)
    return None, None, ShowName


def GetShowName(ImdbId):
    """
    Search for the official TV show name using the IMDB ID
    """
    if not (autosub.TVDBACCOUNTID and _checkToken()):
        return None, None
    try:
        Result = autosub.TVDBSESSION.get(autosub.TVDBAPI + '/search/series?imdbId=tt' + ImdbId, data=autosub.TVDBSESSION.headers['Authorization'][7:],verify=autosub.CERT,timeout=10).json()
    except Exception as error:
        log.error(error.message)
        return None, None
    if 'Error' in Result:
        log.error("Tvdb returned an error: %s" % Result['Error'])
        return None, None
    return Result['data'][0]['seriesName'], str(Result['data'][0]['id'])

def FindEpTitle(TvdbId, Season, Episode):
    if not(autosub.TVDBACCOUNTID and _checkToken()) :
        return None
    Cmd = autosub.TVDBAPI + '/series/%s/episodes/query?airedSeason=%s&airedEpisode=%s'%(TvdbId,Season,Episode)
    try:
        Result = autosub.TVDBSESSION.get(Cmd,verify=autosub.CERT,timeout=10).json()
    except Exception as error:
        log.error(error.message)
        return None
    if 'Error' in Result:
        log.error("Tvdb returnd an error: %s" % Result['Error'])
        return None
    return Result['data'][0]['episodeName']