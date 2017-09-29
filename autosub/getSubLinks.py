#
# The getSubLinks module
#
import logging
import time,sys,re
import requests
from operator import itemgetter
from autosub.ProcessFilename import ProcessFile
from autosub.OpenSubtitles import OS_NoOp
import autosub.Addic7ed

# Settings
log = logging.getLogger('thelogger')

def _scoreMatch(release, wanted):
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

def _SS_Search(Wanted, sourceWebsites):
    # Get the scored list for all SubtitleSeeker hits
    ScoreListNL, ScoreListEN = [],[]
    log.debug('SubtitlesSeeker search started for %s on sites: %s ' % (Wanted['ImdbId'],sourceWebsites))

    # Compose the search URL for the subtitle and language we want.
    langs = Wanted['langs'][0] + ',' + Wanted['langs'][1] if len(Wanted['langs']) == 2 else Wanted['langs'][0]
    SearchUrl = "%s&imdb=%s&season=%s&episode=%s&language=%s&return_type=json" % (autosub.SUBSEEKERAPI, Wanted['ImdbId'], Wanted['season'], Wanted['episode'], langs)

    # Let Subtitle seeker do a search voor the wanted sub
    try:
        SubseekerSession = requests.session()
        Subs = SubseekerSession.get(SearchUrl).json()
        SubseekerSession.close()
    except Exception as error:
        log.error("The SubtitleSeeker server returned an error. Message is %s" % error)
        return ScoreListNL,ScoreListEN

    # Check to see whether we have results or not
    try:
        if not 'total_matches' in Subs['results'].keys():
            return ScoreListNL,ScoreListEN
    except Exception as error:
        log.info('No subtitle found on Subtitleseeker for this video : %s' % Wanted['file'])
        return ScoreListNL,ScoreListEN
    if int(Subs['results']['total_matches']) == 0:
        return ScoreListNL,ScoreListEN

    # Split the result in the two languages(if needed) and score the subs
    NameDict = {}
    log.debug('%d subs found, now checking them.' % Subs['results']['total_matches'])
    for Sub in Subs['results']['items']:
        if Sub['site'].lower() in sourceWebsites:
            Sub['release'] = Sub['release'][:-4] if Sub['release'].lower().endswith(".srt") else Sub['release']
            NameDict.clear()
            NameDict = ProcessFile(Sub['release'],Wanted['container'])
            if not NameDict:
                continue
            score = _scoreMatch(NameDict,Wanted)
            if score == 0:
                continue
            log.debug('Score:%s Needed:%s for %s sub of %s from %s' % ('{0:04b}'.format(score).replace('1','X').replace('0','-'), autosub.MINMATCHDSP,Sub['language'], Sub['release'],Sub['site']))
            if autosub.MINMATCHSCORE & score >= autosub.MINMATCHSCORE:
                if Sub['language'] == autosub.ENGLISH:
                    ScoreListEN.append({'score':score, 'url':Sub['url'] , 'website':Sub['site'].lower(),'Lang':Sub['language'], 'releaseName':Sub['release'],'SubCodec':u''})
                if Sub['language'] == autosub.DUTCH:
                    ScoreListNL.append({'score':score, 'url':Sub['url'] , 'website':Sub['site'].lower(),'Lang':Sub['language'], 'releaseName':Sub['release'],'SubCodec':u''})
    return ScoreListNL,ScoreListEN


def _A7_Search( Wanted):

    ScoreListNL,ScoreListEN = [],[]
    langs = u''
    if autosub.ENGLISH in Wanted['langs']:
        langs = '|1|'
    if autosub.DUTCH in Wanted['langs']:
        langs = langs +'17|' if langs else '|17|'

    SearchUrl = '/ajax_loadShow.php?show=' + Wanted['A7Id'] + '&season=' + Wanted['season'].lstrip('0') + '&langs=' + langs + '&hd=0&hi=0'
    if int(Wanted['A7Id']) > 0:
        log.debug('Addic7ed search started for %s.' % Wanted['A7Id'])
    else:
        log.debug('No Addic7Id for %s, so it is skipped. ' % Wanted['file'])
        return ScoreListNL,ScoreListEN

    SubOverviewPage = autosub.ADDIC7EDAPI.get(SearchUrl)
    if not SubOverviewPage:
        log.debug('Could not get the sub overview page from Addic7ed')
        return ScoreListNL,ScoreListEN

    try:
        Subs = re.findall('<tr class="epeven completed">(.*?)</tr>', SubOverviewPage, re.S)
    except Exception as error:
        return ScoreListNL,ScoreListEN

    log.debug('%d subs found, now checking them.' % len(Subs))
    for SubLine in Subs:
            # Scraper information:
            # 0 = Season number
            # 1 = Episode number
            # 2 = Episode Title
            # 3 = Sub Language
            # 4 = Version ( e.g. free text from uploader) 
            # 5 = Status  (should be Completed otherwise it is a partial sub)
            # 6 = Hearing Impaired flag 
            # 7 = Corrected flag
            # 8 = HD flag (should be set if sub has 720/1080 resolution)
            # 9 = Downloadlink on the Addic7ed site
        SubInfo = re.findall('<td.*?>(.*?)</td>', SubLine, re.S)
            # Check if the minimal info is available and is what we need
        if (len(SubInfo) < 10 or int(SubInfo[1]) != int(Wanted['episode']) or SubInfo[3] not in Wanted['langs'] or not SubInfo[4] or SubInfo[5] != u'Completed' or not SubInfo[9]):
            continue
        else:
            downloadUrl = SubInfo[9].split('"')[1]
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
            score = _scoreMatch(version, Wanted)
            if score == 0:
                continue
            log.debug('Score:%s Needed:%s for %s sub of %s.' % ('{0:04b}'.format(score).replace('1','X').replace('0','-'), autosub.MINMATCHDSP, SubInfo[3], releasename))
            if autosub.MINMATCHSCORE & score >= autosub.MINMATCHSCORE:
                if not 'EpisodeTitle' in Wanted.keys():
                    try:
                        Wanted['EpisodeTitle'] = SubInfo[2]
                    except:
                        pass
                if SubInfo[3] == autosub.DUTCH:
                    ScoreListNL.append({'score':score , 'releaseName':releasename, 'website':'addic7ed.com' , 'url':downloadUrl , 'Lang':SubInfo[3], 'SubCodec':''})
                elif SubInfo[3] == autosub.ENGLISH:
                    ScoreListEN.append({'score':score , 'releaseName':releasename, 'website':'addic7ed.com' , 'url':downloadUrl , 'Lang':SubInfo[3], 'SubCodec':''})
    return ScoreListNL,ScoreListEN


def _OS_Search(Wanted):
    ScoreListNL, ScoreListEN = [],[]
    # Format a dict for the opensubtitles API call
    Data = {}
    Data['sublanguageid'] = Wanted['langs'][0][:3] if len(Wanted['langs']) == 1 else  Wanted['langs'][0][:3] + ',' +  Wanted['langs'][1][:3]
    Data['imdbid' ] = Wanted['ImdbId']
    Data['season']  = Wanted['season']
    Data['episode'] = Wanted['episode']

    log.debug('Search started for %s.' % Wanted['ImdbId'])
    time.sleep(3)
    if not OS_NoOp():
        return ScoreListNL,ScoreListEN

    try:
        Subs = autosub.OPENSUBTITLESSERVER.SearchSubtitles(autosub.OPENSUBTITLESTOKEN, [Data])
    except:
        autosub.OPENSUBTITLESTOKEN = None
        log.error('Error from Opensubtitles search API')
        return ScoreListNL,ScoreListEN
    if Subs['status'] != '200 OK':
        log.debug('No subs found for %s on Opensubtitles.' % Wanted['file'])
        return ScoreListNL,ScoreListEN
    NameDict = {}
    log.debug('%d subs found, now checking them.' % len(Subs['data']))
    for Sub in Subs['data']:
        try:
            if ( int(Sub['SeriesEpisode']) != int(Wanted['episode']) or
               int(Sub['SeriesSeason']) != int(Wanted['season'])     or
               int(Sub['SubBad']) > 0                                or 
               not Sub['MovieReleaseName']                           or 
               not Sub['IDSubtitleFile']                             or 
               (Sub['SubHearingImpaired'] != '0' and not autosub.HI) or
               Sub['IDSubtitleFile'] in autosub.OPENSUBTITLESBADSUBS):
                continue
        except:
            continue
        NameDict.clear()
        NameDict = ProcessFile(Sub['MovieReleaseName'],Wanted['container'])
        if not NameDict:
            NameDict = ProcessFile(Sub['SubFileName'],Wanted['container'])
            if not NameDict:
                continue
         # here we score the subtitle and if it's high enough we add it to the list 
        score = _scoreMatch(NameDict,Wanted)
        if score == 0:
            continue
        log.debug('Score:%s Needed:%s for %s sub of %s.' % ('{0:04b}'.format(score).replace('1','X').replace('0','-'), autosub.MINMATCHDSP,Sub['LanguageName'], Sub['MovieReleaseName']))
        if autosub.MINMATCHSCORE & score >= autosub.MINMATCHSCORE:
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
    log.debug("Imdb ID: %s - Addic7ed ID: %s - Language: %s - Title: %s" % (Wanted['ImdbId'],Wanted['A7Id'],Wanted['langs'],Wanted['title']))
    sourceWebsites, fullScoreListNL, fullScoreListEN   = [],[],[]
    scoreListSubSeekerNL    , scoreListSubSeekerEN     = [],[]
    scoreListAddic7edNL     , scoreListAddic7edEN      = [],[]
    scoreListOpensubtitlesNL, scoreListOpensubtitlesEN = [],[]

    if not ( autosub.PODNAPISI or autosub.SUBSCENE or autosub.ADDIC7ED or autosub.OPENSUBTITLES):
        log.debug('No subtitle website selected in the config so nothing to do here!')
        return fullScoreListNL,fullScoreListEN

    if autosub.PODNAPISI:
        sourceWebsites.append('podnapisi.net')
    if autosub.SUBSCENE:
        sourceWebsites.append('subscene.com')
        # If podnapisi or subscene is choosen call subtitleseeker
    if len(sourceWebsites) > 0:
        scoreListSubSeekerNL,scoreListSubSeekerEN = _SS_Search(Wanted, sourceWebsites)
        # Use Addic7ed if selected
        # and check if Addic7ed download limit has been reached
    if Wanted['A7Id'] and autosub.ADDIC7EDLOGGED_IN:
        if autosub.DOWNLOADS_A7 < autosub.DOWNLOADS_A7MAX:
            scoreListAddic7edNL,scoreListAddic7edEN = _A7_Search(Wanted)
        else:
            log.debug("You have reached your 24h limit of %s  Addic7ed downloads!" % autosub.DOWNLOADS_A7MAX)
        # Use OpenSubtitles if selected
    if autosub.OPENSUBTITLES and autosub.OPENSUBTITLESTOKEN and Wanted['ImdbId']:
        scoreListOpensubtitlesNL,scoreListOpensubtitlesEN = _OS_Search(Wanted)

        # merge the Dutch subs and sort them on the highest score
        # If there are results with the same score, the download links which comes last (anti-alphabetically) will be returned
    for list in [scoreListSubSeekerNL, scoreListAddic7edNL, scoreListOpensubtitlesNL]:
        if list: fullScoreListNL.extend(list)
    if fullScoreListNL:
        fullScoreListNL = sorted(fullScoreListNL, key=itemgetter('score', 'website'), reverse=True)
        log.info('Found %d DUTCH subs which matched the min match score.' % len(fullScoreListNL))
    # the same for the English subs
    for list in [scoreListSubSeekerEN, scoreListAddic7edEN, scoreListOpensubtitlesEN]:
        if list: fullScoreListEN.extend(list)
    if fullScoreListEN:
        fullScoreListEN = sorted(fullScoreListEN, key=itemgetter('score', 'website'), reverse=True)
        log.info('Found %d ENGLISH subs which matched the min match score.' % len(fullScoreListEN))
    return fullScoreListNL,fullScoreListEN
