#
# The Autosub ProcessFilename module
#

from common import seperator, source, source_syn, quality, quality_syn, quality_fileext, codec, codec_syn, codec_fileext, releasegrp, releasegrp_syn, releasegrp_fallback
from common import show_regex, episode_regex
import re
import logging
from string import capwords
log = logging.getLogger('thelogger')

_noextrainfo = 0

def _cleanUpName(series_name):
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
        log.debug("There is no SerieName to clean")

def _checkTitle(title):
    if not title:
        return None
    
    for reg in episode_regex:
        results = re.findall(reg, title)
        if not results:
            return _cleanUpName(title)


def _returnHit(regex, file_info):
    if not file_info:
        return None
    
    for reg in regex:
        results = re.findall(reg, file_info)
        if results:
            for result in reversed(results):
                pos = file_info.find(result.lower())
                if pos != -1:
                    end = pos + len(result)
                    # make sure our word is always surrounded by separators
                    if ((pos > 0 and file_info[pos - 1] not in seperator) or
                        (end < len(file_info) and file_info[end] not in seperator)):
                        # note: sep is a regexp, but in this case using it as
                        #       a sequence achieves the same goal
                        continue
                    result = re.sub("[. _-]", "-", result)
                    return result.lower()

def _returnGroup(regex, tosearch):
    if not tosearch:
        return {}
    
    for reg in regex:
        match = re.search(reg, tosearch)
        if match:
            matchdic = match.groupdict()
            return matchdic

def _checkSynonyms(synonyms, result):
    if result in synonyms.keys():
        if synonyms[result]:
            return synonyms[result].lower()
    else:
        return result

def _getSource(file_info):
    result = _checkSynonyms(source_syn,
                            _returnHit(source, file_info))
    if not result:
        global _noextrainfo
        _noextrainfo += 1
    return result

def _getQuality(file_info, fileext):
    result = _checkSynonyms(quality_syn,
                            _returnHit(quality, file_info))
    
    if not result:
        global _noextrainfo
        _noextrainfo += 1
        if fileext in quality_fileext.keys():
            result = quality_fileext[fileext]
    
    if not result:
        result = u'sd'
    
    return result.lower()

def _getCodec(file_info, fileext):
    result = _checkSynonyms(codec_syn,
                            _returnHit(codec, file_info))
    
    if not result:
        global _noextrainfo
        _noextrainfo += 1
        if fileext in codec_fileext.keys():
            result = codec_fileext[fileext]
    
    return result

def _getReleasegrp(file_info):
    #result = _returnHit(releasegrp, file_info)
    result = None
    if not result:
        global _noextrainfo
        _noextrainfo += 1
        resultdict = _returnGroup(releasegrp_fallback, file_info)
        if 'releasegrp' in resultdict.keys():
            result = resultdict['releasegrp']
        result = _checkSynonyms(releasegrp_syn, result)
        if not result:
            result = _returnHit(releasegrp, file_info)
    if not result:
        result = _returnHit(releasegrp, file_info)
    return result

def _returnSceneNumber(number):
    if not number:
        return None
    
    number = int(number)
    if number <=9:
        number = '0' + str(number)
    else:
        number = str(number)
    return unicode(number)

def ProcessFile(filename, fileext):
    filename = filename.replace(',','.')
    filename = re.sub("[\[].*?[\]]", "", filename)
    show_info = _returnGroup(show_regex, filename)
    title = None
    season = None
    episode = None
    file_info = None
    source = None
    quality = None
    codec = None
    releasegrp = None
    extra_info = None

    global _noextrainfo
    _noextrainfo = 0

    if show_info:
        if 'title' in show_info.keys(): title = _checkTitle(show_info['title'])
        if 'season' in show_info.keys(): season = _returnSceneNumber(show_info['season'])
        if 'episode' in show_info.keys(): episode = _returnSceneNumber(show_info['episode'])
        if 'extra_info' in show_info.keys(): extra_info = show_info['extra_info']
    if extra_info:
        extra_info = extra_info.lower() 
        source = _getSource(extra_info)
        quality = _getQuality(extra_info, fileext)
        codec = _getCodec(extra_info, fileext)
        releasegrp = _getReleasegrp(extra_info)

    if title and season and episode: #and _noextrainfo < 4:
        show_dict = {}
        show_dict['title'] = title
        show_dict['season'] = season
        show_dict['episode'] = episode
        show_dict['source'] = source
        show_dict['quality'] = quality
        show_dict['codec'] = codec
        show_dict['releasegrp'] = releasegrp
        show_dict['container'] = fileext
        return show_dict
    else: 
        return {}
