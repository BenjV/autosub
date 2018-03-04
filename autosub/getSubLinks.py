#
# The getSubLinks module
#
import logging
import time,sys,re,types
from HTMLParser import HTMLParser
import library.requests as requests
import autosub
from operator import itemgetter
from autosub.ProcessFilename import ProcessName
from autosub.OpenSubtitles import OS_NoOp

# Settings
log = logging.getLogger('thelogger')


def _scoreMatch(Release, Wanted):
    """
    Return how high the match is. Currently 31 is the best match
    This function give the flexibility to change the most important attribute for matching
    If source is matched,       score is increased with 16
    If distro is matched,       score is increased with 8
    If releasegroup is matched, score is increased with 4
    If quality is matched,      score is increased with 2
    If codec is matched,        score is increased with 1
    """
    Release['score'] = int(0)
    if Release['source'] and Wanted['source']:
        if Release['source'] == Wanted['source']:
            Release['score'] += 16
        elif autosub.EQUALMATCH and ((Release['distro'] and 'web' in Wanted['source']) or 
                                     (Wanted['distro'] and 'web' in Release['source'])
                                     ):
            Release['score'] += 16

    if Release['distro'] and Wanted['distro'] and Release['distro']  == Wanted['distro']:
        Release['score'] += 8

    if Release['quality'] and Wanted['quality']:
        if (   Release['quality'] == Wanted['quality']
           or (Release['quality'] == '720'  and Wanted['quality'] == '1080')
           or (Release['quality'] == '1080' and Wanted['quality'] == '720' )) :
            Release['score'] += 2

    if Release['codec'] and Wanted['codec'] and Release['codec'][1:] == Wanted['codec'][1:]:
        Release['score'] += 1
        # The releasegroup is done last, because if mustmatch is foud and no releasegroup then score is set to zero.

    Scored = False
    for rlsgrp in Release['rlsgrplst']:
        if rlsgrp in Wanted['rlsgrplst'] and not Scored:
            Release['score'] += 4 
            Scored = True
        else:
            if rlsgrp in autosub.MUSTMATCH:
                Release['score'] = 0
                break
    if Release['score'] >= autosub.MINMATCHSCORE:
        return True
    else:
        return False

def _SS_Search(Wanted, sourceWebsites, SubListNL, SubListEN):
        # Get the scored list for all SubtitleSeeker hits

    log.debug('Search started for %s on sites: %s ' % (Wanted['ImdbId'],sourceWebsites))
        # Compose the search URL for the subtitle and language we want.
    if len(Wanted['langs']) == 2 :
        langs = 'english,dutch'
    elif u'nl' in Wanted['langs']:
        langs = 'dutch'
    else:
        langs = 'english'
    SearchUrl = "%s&imdb=%s&season=%s&episode=%s&language=%s&return_type=json" % (autosub.SUBSEEKERAPI, Wanted['ImdbId'], Wanted['season'], Wanted['episode'], langs)
        # Check to see if Subtitle Seeker is available
    try:
        if not autosub.SS_SESSION.head('http://www.subtitleseeker.com',timeout=7).ok:
            log.error('SubTitleSeeker website is not reachable')
            return
    except Exception as error:
        log.debug(error.message)
        log.error('SubTitleSeeker website is not reachable')
        return
        # Let Subtitle seeker do a search voor the wanted sub
    try:
        Results = autosub.SS_SESSION.get(SearchUrl,timeout=10).json()
    except Exception as error:
        log.error(error.message)
        return

        # Check to see whether we have results or not
        # the json formatting from subtitleseeker is faulty in case of an error so we have to check the type insted of reading the error
    if not type(Results['results']) is types.DictType:
        log.error('Unreadable result form SubtitleSeeker, skipping it!')
        return
    log.debug('%d subs found' % Results['results']['total_matches'])
    if Results['results']['total_matches'] == 0:
        return
        # Score the subs and split the result in the two languages(if needed)
        # Only subs with high enough score get processed.
    for Item in Results['results']['items']:
        if Item['site'][:-4] and Item['site'][:-4].lower() in sourceWebsites:
            if not Item.get('release'):
                continue
            ReleaseName = HTMLParser().unescape(Item['release'])
            Release = ProcessName(ReleaseName)
            if not Release or not _scoreMatch(Release, Wanted):
                continue
            Release['show']     = Wanted['show']
            Release['season']   = Wanted['season']
            Release['episode']  = Wanted['episode']
            Release['url']      = Item.get('url')
            Release['website']  = Item.get('site','').lower()[:-4]
            Release['SubCodec'] = None
            Release['title']    = HTMLParser().unescape(Item['episode_title']) if Item.get('episode_title') else None
            Release['releaseName'] = Wanted['file']
            Release['language'] = autosub.DUTCH if Item.get('language') == u'Dutch' else autosub.ENGLISH
            log.debug('Score:%s Needed:%s for %s sub of %s.' % ('{0:05b}'.format(Release['score']).replace('1','X').replace('0','-'), autosub.MINMATCHDSP, Release['language'], Item['release']))
            if Release['language'] == autosub.DUTCH:
                SubListNL.append(Release)
            elif Release['language'] == autosub.ENGLISH:
                SubListEN.append(Release)
    return

def _A7_Search(Wanted,SubListNL,SubListEN):
    langs,langcodes = [],[]
    if autosub.ENGLISH in Wanted['langs']:
        langcodes = '|1|'
        langs.append(u'English')
    if autosub.DUTCH in Wanted['langs']:
        langcodes = langcodes +'17|' if langcodes else '|17|'
        langs.append(u'Dutch')
    Hi = '0' if autosub.HI else '-1'
    SearchUrl = '/ajax_loadShow.php?show=' + str(Wanted['A7Id']) + '&season=' + Wanted['season'].lstrip('0') + '&langs=' + langcodes + '&hd=0&hi=' + Hi
    if Wanted['A7Id'] > 0:
        log.debug('Addic7ed search started for %d.' % Wanted['A7Id'])
    else:
        log.debug('No Addic7Id for %s, so it is skipped. ' % Wanted['file'])
        return

    SubOverviewPage = autosub.ADDIC7EDAPI.getpage(SearchUrl)
    if not SubOverviewPage:
        log.debug('Could not get the sub overview page from Addic7ed')
        return
    try:
        Subs = re.findall('<tr class="epeven completed">(.*?)</tr>', SubOverviewPage, re.S)
    except Exception as error:
        return
    log.debug('Subs found, now checking them.')
    for SubLine in Subs:
            # Scraper information:
            # 0 = Season number
            # 1 = Episode number
            # 2 = Episode Title
            # 3 = Sub Language
            # 4 = Version ( e.g. free text from uploader) 
            # 5 = Status  (should be Completed otherwise it is a partial sub)
            # 6 = 'HI'(Hearing Impaired) flag 
            # 7 = 'Corrected' flag
            # 8 = 'HD' flag (should be set if sub has 720/1080 resolution)
            # 9 = Downloadlink on the Addic7ed site
        SubInfo = re.findall('<td.*?>(.*?)</td>', SubLine, re.S)
            # Check if the minimal info is available and is what we need
        if len(SubInfo) < 10 or \
           int(SubInfo[1]) != int(Wanted['episode']) or \
           SubInfo[3] not in langs or \
           not SubInfo[4] or \
           SubInfo[5] != u'Completed' or \
           not SubInfo[9]:
            continue
        Release = ProcessName(SubInfo[4])
        if not Release: continue
        if not _scoreMatch(Release, Wanted) : continue
        Release['show']     = Wanted['show']
        Release['season']   = Wanted['season']
        Release['episode']  = Wanted['episode']
        Release['website'] = u'addic7ed'
        Release['title']  = SubInfo[2].split('>')[1][:-3]
        Release['language'] = u'nl' if SubInfo[3] == 'Dutch' else u'en'
        Release['url']    = SubInfo[9].split('"')[1]
        Release['SubCodec'] = None
        Release['releaseName'] = Wanted['file']
        log.debug('Score:%s Needed:%s for %s sub of %s.' % ('{0:05b}'.format(Release['score']).replace('1','X').replace('0','-'), autosub.MINMATCHDSP, SubInfo[3], Release['releaseName']))
        if SubInfo[3] == u'Dutch' :
            SubListNL.append(Release)
        elif SubInfo[3] == u'English':
            SubListEN.append(Release)
    return

def _OS_Search(Wanted,SubListNL,SubListEN):
    # Format a dict for the opensubtitles API call
    Data = {}
    if len(Wanted['langs']) == 2 :
        Data['sublanguageid'] = 'eng,dut'
    elif 'nl' in Wanted['langs']:
        Data['sublanguageid'] = 'dut'
    else:
        Data['sublanguageid'] = 'eng'
    Data['imdbid' ] = Wanted['ImdbId']
    Data['season']  = Wanted['season']
    Data['episode'] = Wanted['episode']

    log.debug('Search started for %s on Opensubtitles.' % Wanted['ImdbId'])

    if not OS_NoOp():
        return
    time.sleep(1)
    try:
        Subs = autosub.OPENSUBTITLESSERVER.SearchSubtitles(autosub.OPENSUBTITLESTOKEN, [Data])
    except Exception as error:
        autosub.OPENSUBTITLESTOKEN = None
        log.error('Error from Opensubtitles. %s' % error)
        return
    if not Subs['status'] or Subs['status'] != '200 OK':
        log.debug('No subs found for %s on Opensubtitles.' % Wanted['file'])
        return
    log.debug('%d subs found, now checking them.' % len(Subs['data']))
    for Sub in Subs['data']:
        try:
            if (int(Sub.get('SeriesEpisode','0'))    != int(Wanted['episode'])
               or int(Sub.get('SeriesSeason','0'))   != int(Wanted['season'])
               or (Sub.get('SubBad','0')             != '0')
               or (Sub.get('SubAutoTranslation','0') != '0')
               or not Sub.get('MovieReleaseName')
               or not Sub.get('IDSubtitleFile')
               or (Sub.get('SubHearingImpaired') != '0' and not autosub.HI)
               or Sub['IDSubtitleFile'] in autosub.OPENSUBTITLESBADSUBS) :
                continue
        except:
            continue
        Release = ProcessName(Sub['MovieReleaseName'])
        if not Release or not _scoreMatch(Release, Wanted):
            continue
        log.debug('Score:%s Needed:%s for %s sub of %s.' % ('{0:05b}'.format(Release['score']).replace('1','X').replace('0','-'), autosub.MINMATCHDSP,Sub['ISO639'], Sub['MovieReleaseName']))
        Release['show']        = Wanted['show']
        Release['season']      = Wanted['season']
        Release['episode']     = Wanted['episode']
        Release['url']         = unicode(Sub.get('IDSubtitleFile',None))
        Release['website']     = u'opensubtitles'
        Release['SubCodec']    = unicode(Sub.get('SubEncoding', 'CP1252'))
        Release['title']       = unicode(Sub.get('MovieName').split('"')[2].lstrip())
        Release['releaseName'] = unicode(Sub.get('MovieReleaseName'))
        Release['language']    = unicode(Sub.get('ISO639'))
        if Release['language'] == autosub.DUTCH:
            SubListNL.append(Release)
        elif Release['language'] == autosub.ENGLISH:
            SubListEN.append(Release)
    return

def getSubLinks(Wanted):
    """
    Return all the hits that reach minmatchscore, sorted with the best at the top of the list
    Each element had the downloadlink, score, releasename, and source website)
    Matching is based on the provided release details.

    Keyword arguments:
    lang -- Language of the wanted subtitle, Dutch or English
    Wanted -- Dict containing the ImdbId, A7Id, quality, releasegrp, source season and episode.
    """
    log.debug("Imdb ID: %s - Addic7ed ID: %s - Language: %s - Title: %s" % (Wanted['ImdbId'],Wanted['A7Id'],Wanted['langs'],Wanted['show']))
    SubListNL, SubListEN, sourceWebsites = [],[],[]

    if not ( autosub.PODNAPISI or autosub.SUBSCENE or autosub.ADDIC7ED or autosub.OPENSUBTITLES):
        log.debug('No subtitle website selected in the config so nothing to do here!')
        return

    if autosub.PODNAPISI:
        sourceWebsites.append('podnapisi')
    if autosub.SUBSCENE:
        sourceWebsites.append('subscene')
        # If podnapisi or subscene is choosen call subtitleseeker
    if len(sourceWebsites) > 0 and not autosub.SEARCHSTOP:
        _SS_Search(Wanted, sourceWebsites, SubListNL, SubListEN)

        # Use Addic7ed if selected
        # and check if Addic7ed download limit has been reached
    if Wanted['A7Id'] and autosub.ADDIC7EDLOGGED_IN and not autosub.SEARCHSTOP:
        if autosub.DOWNLOADS_A7 < autosub.DOWNLOADS_A7MAX:
            _A7_Search(Wanted, SubListNL, SubListEN)
        else:
            log.debug("You have reached your 24h limit of %s  Addic7ed downloads!" % autosub.DOWNLOADS_A7MAX)

        # Use OpenSubtitles if selected
    if autosub.OPENSUBTITLES and autosub.OPENSUBTITLESTOKEN and Wanted['ImdbId'] and not autosub.SEARCHSTOP:
        _OS_Search(Wanted,SubListNL,SubListEN)

        # Sort the sublist for dutch subs
    if SubListNL:
        SubListNL = sorted(SubListNL, key=itemgetter('score', 'website'), reverse=True)
        log.info('Found %d DUTCH subs which matched the min match score.' % len(SubListNL))
        # Sort the Sublist for the English subs
    if SubListEN:
        SubListEN = sorted(SubListEN, key=itemgetter('score', 'website'), reverse=True)
        log.info('Found %d ENGLISH subs which matched the min match score.' % len(SubListEN))
    return SubListNL,SubListEN
