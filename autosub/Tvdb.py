#
# Autosub Tvdb.py 
#
# The Tvdb API module
#

import logging

import urllib,requests
from difflib import SequenceMatcher as SM
try:
    import xml.etree.cElementTree as ET
except:
    import xml.etree.ElementTree as ET
from xml.dom import minidom
import autosub
import autosub.Helpers

# Settings
log = logging.getLogger('thelogger')



def FindName(Url,Root,Tag):

    Found = TvdbId = None
    Session = requests.Session()
    try:
        Result = Session.get(Url)
    except:
        return None
    try:
        PageRoot = ET.fromstring(Result.content)
    except Exception as error:
        log.error("FindName: error parsing info from Tvdb. Error =%s" %error)
        return None
    try:
        for node in PageRoot.findall(Root):
            try:
                Found = node.find(Tag).text
            except:
                log.error("FindName: Could not find %s in %s on Tvdb URL: % " % (Root,Tag,Url))
                log.error("FindName: message is: " % error)
                return None
            if Found:
                try:
                    TvdbId = node.find('seriesid').text
                except:
                    pass
                return Found, TvdbId
            else:
                log.error("Tvdb: Could not find %s in %s on Tvdb URL: " % (Root,Tag,Url))
                return None, None
    except Exception as error:
        log.error("FindName: Could not find %s in %s on Tvdb URL: " % (Root,Tag,Url))
        log.error("FindName: message is: " % error)
        return None, None
    log.error("FindName: Could not find %s in %s on Tvdb URL: " % (Root,Tag,Url))
    return None, None

def getShowidApi(showName):
    """
    Search for the IMDB ID by using the TvDB API and the name of the show.
    Keyword arguments:
    showName -- Name of the show to search the showid for
    """

    Url = "%sGetSeries.php?seriesname=%s" % (autosub.IMDBAPI, urllib.quote(showName.encode('utf8','xmlcharrefreplace')))
    Session = requests.Session()
    try:
        Result = Session.get(Url)
    except:
        log.debug('TvdbId:Problem connecting toTvdb. Check if the site is down')
        return None
    if not Result.ok:
        log.debug('TvdbId: No correct response from Tvdb. Check if the site is down')
        return None
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
            log.error("getShowidApi: Could not find %s in %s on Tvdb URL: " % (showName, Url))
            log.error("getShowidApi: message is: " % error)
    if ImdbId == '1489904':
        log.debug('getShowidAPI: Found a serie that is forbidden by Tvdb (1489904) so skipping it.')
        return None, None, None
    ImdbId = ImdbId.decode('utf-8') if isinstance(ImdbId,str) else ImdbId
    TvdbId = TvdbId.decode('utf-8') if isinstance(TvdbId,str) else TvdbId
    HighName = HighName.decode('utf-8') if isinstance(HighName,str) else HighName
    return ImdbId,TvdbId, HighName


def getShowName(ImdbId):
    """
    Search for the official TV show name using the IMDB ID
    """
    
    Url = autosub.IMDBAPI + 'GetSeriesByRemoteID.php?imdbid=' + ImdbId
    return FindName(Url, 'Series', 'SeriesName')

    
    
def GetEpisodeName(ImdbId,TvdbId, SeasonNum, EpisodeNum):
    Session = requests.Session()
    if not TvdbId:
        Url = autosub.IMDBAPI + 'GetSeriesByRemoteID.php?imdbid=' + ImdbId
        SerieName, TvdbId = FindName(Url, 'Series', 'seriesid')

    Url = "%sDECE3B6B5464C552/series/%s/default/%s/%s" % (autosub.IMDBAPI,TvdbId,SeasonNum.lstrip('0'),EpisodeNum.lstrip('0'))
    EpisodeName, TvdbId = FindName(Url,'Episode','EpisodeName')
    return EpisodeName
