#
# The getSubLinks module
#

import logging
import time,sys,re
from xml.dom import minidom
try:
    import xml.etree.cElementTree as ET
except:
    import xml.etree.ElementTree as ET
import library.requests as requests
from operator import itemgetter
import autosub.Helpers
from autosub.ProcessFilename import ProcessFilename
from autosub.OpenSubtitles import OpenSubtitlesNoOp
import autosub.Addic7ed
# Settings
log = logging.getLogger('thelogger')


def SubtitleSeeker(Wanted, sourceWebsites):
    # Get the scored list for all SubtitleSeeker hits
    ScoreListNL, ScoreListEN = [],[]
    log.debug('getSubLinks: SubtitlesSeeker search started for %s on sites: %s ' % (Wanted['ImdbId'],sourceWebsites))

    # Compose the search URL for the subtitle and language we want.
    langs = Wanted['langs'][0] + ',' + Wanted['langs'][1] if len(Wanted['langs']) == 2 else Wanted['langs'][0]
    SearchUrl = "%s&imdb=%s&season=%s&episode=%s&language=%s&return_type=json" % (autosub.API, Wanted['ImdbId'], Wanted['season'], Wanted['episode'], langs)

    # Let Subtitle seeker do a search voor the wanted sub
    if autosub.Helpers.checkAPICallsSubSeeker(use=True):
        try:
            SubseekerSession = requests.session()
            Result = SubseekerSession.get(SearchUrl).json()
            SubseekerSession.close()
        except Exception as error:
            log.error("getSubLink: The SubtitleSeeker server returned an error. Message is %s" % error)
            return ScoreListNL,ScoreListEN
    else:
        log.error("getSubLink: out of api calls for SubtitleSeeker.com")
        return ScoreListNL,ScoreListEN

    # Check to see whether we have results or not
    try:
        if not 'total_matches' in Result['results'].keys():
            return ScoreListNL,ScoreListEN
    except Exception as error:
        log.info('getSublink: No subtitle found on Subtitleseeker for this video : %s' % Wanted['file'])
        return ScoreListNL,ScoreListEN
    if int(Result['results']['total_matches']) == 0:
        return ScoreListNL,ScoreListEN

    # Split the result in the two languages(if needed) and score the subs
    NameDict = {}
    for Item in Result['results']['items']:
        if Item['site'].lower() in sourceWebsites:
            Item['release'] = Item['release'][:-4] if Item['release'].lower().endswith(".srt") else Item['release']
            NameDict.clear()
            NameDict = ProcessFilename(Item['release'],Wanted['container'])
            if not NameDict:
                continue
            score = autosub.Helpers.scoreMatch(NameDict,Wanted)
            if score == 0:
                continue
            log.debug('SubtitleSeeker: Score = %s of %s for %s sub of %s on %s.' % (score, autosub.MINMATCHSCORE, Item['language'], Item['release'], Item['site']))
            if score >= autosub.MINMATCHSCORE:
                if Item['language'] == autosub.ENGLISH:
                    ScoreListEN.append({'score':score, 'url':Item['url'] , 'website':Item['site'].lower(),'Lang':Item['language'], 'releaseName':Item['release'],'SubCodec':u''})
                if Item['language'] == autosub.DUTCH:
                    ScoreListNL.append({'score':score, 'url':Item['url'] , 'website':Item['site'].lower(),'Lang':Item['language'], 'releaseName':Item['release'],'SubCodec':u''})
    return ScoreListNL,ScoreListEN


def Addic7ed( Wanted):

    ScoreListNL,ScoreListEN = [],[]
    langs = u''
    if autosub.ENGLISH in Wanted['langs']:
        langs = '|1|'
    if autosub.DUTCH in Wanted['langs']:
        langs = langs +'17|' if langs else '|17|'

    SearchUrl = '/ajax_loadShow.php?show=' + Wanted['A7Id'] + '&season=' + Wanted['season'].lstrip('0') + '&langs=' + langs + '&hd=0&hi=0'
    if int(Wanted['A7Id']) > 0:
        log.debug('getSubLinks: Addic7ed search started for %s.' % Wanted['A7Id'])
    else:
        log.debug('getSubLinks: No Addic7Id for %s, so it is skipped. ' % Wanted['file'])
        return ScoreListNL,ScoreListEN

    SubOverviewPage = autosub.ADDIC7EDAPI.get(SearchUrl)
    if not SubOverviewPage:
        log.debug('getSubLinks: Could not get the sub overview page from Addic7ed')
        return ScoreListNL,ScoreListEN

    try:
        SubLines = re.findall('<tr class="epeven completed">(.*?)</tr>', SubOverviewPage, re.S)
    except Exception as error:
        return ScoreListNL,ScoreListEN
    if SubLines:
        for SubLine in SubLines:
            SubInfo = re.findall('<td.*?>(.*?)</td>', SubLine, re.S)
            if len(SubInfo) != 11:
                continue
            if int(SubInfo[1]) != int(Wanted['episode']):
                continue
            if SubInfo[5] != u'Completed':
                continue
            if not SubInfo[3]:
                continue
            elif SubInfo[3] not in Wanted['langs']:
                continue
            if not SubInfo[9]:
                continue
            else:
                downloadUrl = SubInfo[9].split('"')[1]
            if not SubInfo[4]:
                continue
            else:
                details = SubInfo[4].lower()
            HD = True if SubInfo[8] else False
            hearingImpaired = True if SubInfo[6] else False
            if (hearingImpaired and not autosub.HI):
                continue
            releasename = autosub.Addic7ed.makeReleaseName(details, Wanted['title'], Wanted['season'] , Wanted['episode'])

            # Return is a list of possible releases that match
            versionDicts = autosub.Addic7ed.ReconstructRelease(details, HD)
            if not versionDicts:
                continue
            for version in versionDicts:
                score = autosub.Helpers.scoreMatch(version, Wanted)
                if score == 0:
                    continue
                log.debug('Addic7ed: Score = %s of %s for %s sub of %s.' % (score, autosub.MINMATCHSCORE, SubInfo[3], releasename))
                if score >= autosub.MINMATCHSCORE:
                    if not 'EpisodeTitle' in Wanted.keys():
                        try:
                            Wanted['EpisodeTitle'] = re.findall('">(.*?)</a>', SubInfo[2])[0]
                        except:
                            pass
                    if SubInfo[3] == autosub.DUTCH:
                        ScoreListNL.append({'score':score , 'releaseName':releasename, 'website':'addic7ed.com' , 'url':downloadUrl , 'Lang':SubInfo[3], 'SubCodec':''})
                    elif SubInfo[3] == autosub.ENGLISH:
                        ScoreListEN.append({'score':score , 'releaseName':releasename, 'website':'addic7ed.com' , 'url':downloadUrl , 'Lang':SubInfo[3], 'SubCodec':''})


    else:
        log.debug('Addic7ed: No subs for this season found.')
    return ScoreListNL,ScoreListEN




def Opensubtitles(Wanted):
    ScoreListNL, ScoreListEN = [],[]
    # Format a dict for the opensubtitles API call
    Data = {}
    Data['sublanguageid'] = Wanted['langs'][0][:3] if len(Wanted['langs']) == 1 else  Wanted['langs'][0][:3] + ',' +  Wanted['langs'][1][:3]
    Data['imdbid' ] = Wanted['ImdbId']
    Data['season']  = Wanted['season']
    Data['episode'] = Wanted['episode']
    log.debug('getSubLinks: Opensubtitles search started for %s.' % Wanted['ImdbId'])
    time.sleep(3)
    if not OpenSubtitlesNoOp():
        return ScoreListNL,ScoreListEN

    try:
        Subs = autosub.OPENSUBTITLESSERVER.SearchSubtitles(autosub.OPENSUBTITLESTOKEN, [Data])
    except:
        autosub.OPENSUBTITLESTOKEN = None
        log.error('Opensubtitles: Error from Opensubtitles search API')
        return ScoreListNL,ScoreListEN
    if Subs['status'] != '200 OK':
        log.debug('Opensubtitles: No subs found for %s on Opensubtitles.' % Wanted['file'])
        return ScoreListNL,ScoreListEN
    NameDict = {}
    for Sub in Subs['data']:
        try:
            if int(Sub['SubBad']) > 0 or not Sub['MovieReleaseName'] or not Sub['IDSubtitleFile'] or (Sub['SubHearingImpaired'] != '0' and not autosub.HI):
                continue
        except:
            continue
        NameDict.clear()
        NameDict = ProcessFilename(Sub['MovieReleaseName'],Wanted['container'])
        if not NameDict:
            continue
         # here we score the subtitle and if it's high enough we add it to the list 
        score = autosub.Helpers.scoreMatch(NameDict,Wanted)
        if score == 0:
            continue
        log.debug('Opensubtitles: Score = %s of %s for %s sub of %s.' % (score, autosub.MINMATCHSCORE, Sub['LanguageName'], Sub['MovieReleaseName']))
        if score >= autosub.MINMATCHSCORE:
            if Sub['LanguageName'] == autosub.DUTCH:
                ScoreListNL.append({'score':score, 'url':Sub['IDSubtitleFile'] , 'website':'opensubtitles.org','releaseName':Sub['MovieReleaseName'], 'SubCodec':Sub['SubEncoding'],'Lang':Sub['LanguageName']})
            if Sub['LanguageName'] == autosub.ENGLISH:
                ScoreListEN.append({'score':score, 'url':Sub['IDSubtitleFile'] , 'website':'opensubtitles.org','releaseName':Sub['MovieReleaseName'], 'SubCodec':Sub['SubEncoding'],'Lang':Sub['LanguageName']})
    return ScoreListNL,ScoreListEN


def getSubLinks(Wanted):
    """
    Return all the hits that reach minmatchscore, sorted with the best at the top of the list
    Each element had the downloadlink, score, releasename, and source website)
    Matching is based on the provided release details.

    Keyword arguments:
    lang -- Language of the wanted subtitle, Dutch or English
    Wanted -- Dict containing the ImdbId, A7Id, quality, releasegrp, source season and episode.
    """
    log.debug("getSubLinks: Show ID: %s - Addic7ed ID: %s - Language: %s - Title: %s" % (Wanted['ImdbId'],Wanted['A7Id'],Wanted['langs'],Wanted['title']))
    sourceWebsites, fullScoreListNL, fullScoreListEN   = [],[],[]
    scoreListSubSeekerNL    , scoreListSubSeekerEN     = [],[]
    scoreListAddic7edNL     , scoreListAddic7edEN      = [],[]
    scoreListOpensubtitlesNL, scoreListOpensubtitlesEN = [],[]

    if not ( autosub.PODNAPISI or autosub.SUBSCENE or autosub.ADDIC7ED or autosub.OPENSUBTITLES):
        log.debug('getSubLinks: No subtitle website selected in the config so nothing to do here!')
        return fullScoreListNL,fullScoreListEN

    if autosub.PODNAPISI:
        sourceWebsites.append('podnapisi.net')
    if autosub.SUBSCENE:
        sourceWebsites.append('subscene.com')

    # If podnapisi or subscene is choosen call subtitleseeker

    if len(sourceWebsites) > 0:
        scoreListSubSeekerNL,scoreListSubSeekerEN = SubtitleSeeker(Wanted, sourceWebsites)

    # Use Addic7ed if selected
    # and check if Addic7ed download limit has been reached
    if Wanted['A7Id'] and autosub.ADDIC7EDLOGGED_IN:
        if autosub.DOWNLOADS_A7 < autosub.DOWNLOADS_A7MAX:
            scoreListAddic7edNL,scoreListAddic7edEN = Addic7ed(Wanted)
        else:
            log.debug("checkSub: You have reached your 24h limit of %s  Addic7ed downloads!" % autosub.DOWNLOADS_A7MAX)

    # Use OpenSubtitles if selected
    if autosub.OPENSUBTITLES and autosub.OPENSUBTITLESTOKEN and Wanted['ImdbId']:
        scoreListOpensubtitlesNL,scoreListOpensubtitlesEN = Opensubtitles(Wanted)

    # merge the Dutch subs and sort them on the highest score
    # If there are results with the same score, the download links which comes last (anti-alphabetically) will be returned
    for list in [scoreListSubSeekerNL, scoreListAddic7edNL, scoreListOpensubtitlesNL]:
        if list: fullScoreListNL.extend(list)
    if fullScoreListNL:
        fullScoreListNL = sorted(fullScoreListNL, key=itemgetter('score', 'website'), reverse=True)
        log.info('getSubLinks: Found %d DUTCH subs which matched the min match score.' % len(fullScoreListNL))
    # the same for the English subs
    for list in [scoreListSubSeekerEN, scoreListAddic7edEN, scoreListOpensubtitlesEN]:
        if list: fullScoreListEN.extend(list)
    if fullScoreListEN:
        fullScoreListEN = sorted(fullScoreListEN, key=itemgetter('score', 'website'), reverse=True)
        log.info('getSubLinks: Found %d ENGLISH subs which matched the min match score.' % len(fullScoreListEN))
    return fullScoreListNL,fullScoreListEN
