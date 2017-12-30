#
# The Autosub ProcessFilename module
#
# Below the rule for standard filenaming from the scene
#           Weekly.TV.Show.SXXEXX[Episode.Part].[Episode.Title].<TAGS>.[LANGUAGE].720p.<FORMAT>.x264-GROUP
# Allowed <TAGS> are
#   ALTERNATIVE.CUT, CONVERT, COLORIZED, DC, DIRFIX, DUBBED, EXTENDED, FINAL, INTERNAL, NFOFIX, OAR, OM, PPV, PROPER, REAL, REMASTERED, READNFO, REPACK, RERIP, SAMPLEFIX, SOURCE.SAMPLE, SUBBED, UNCENSORED, UNRATED, UNCUT, WEST.FEED, and WS
#

import re
import logging
from string import capwords
import autosub
log = logging.getLogger('thelogger')


#List with all the possible seperators used in filenaming
Seps ='[][_. {}-]'

show_regex = [re.compile("^((?P<show>.+?){0}+)?s(?P<season>\d+){0}*e(?P<episode>\d+){0}+(?P<info>.+)*".format(Seps), re.I|re.U),
              re.compile("^((?P<show>.+?){0}+)?(?P<season>\d+)*x(?P<episode>\d+){0}*(?P<info>.+)*".format(Seps), re.I|re.U)]

source = re.compile("(?:^|{0})(ahdtv|hdtv|web[.\s_-]?dl|blu[.\s_-]?ray|brrip|dvdrip|web[-_\s]?rip|hddvd|dvd|bdrip|web)(?:{0}|$)".format(Seps), re.U|re.I)
distro = re.compile("(?:^|{0})(amazon|amzn|netflix|nf|hulu|stz|starz|hbo|syfy|brav[o]?|usan|byu|byutv)(?:{0}|$)".format(Seps), re.U|re.I)

quality = re.compile("(?:^|{0}){0}*(4K|uhd|2160[p]*|1080[ip]*|720[ip]*|hd|sd)(?:{0}|$)".format(Seps), re.U|re.I)
codec =   re.compile("(?:^|{0})([xh]+264|[xh]+.264|[xh]+265|[xh]+.265|xvid|dvix)(?:{0}|$)".format(Seps), re.U|re.I)

audio = re.compile("(?:^|{0})([da][dd][acd][cp3]?[ 521]*[ .]?[o01]?|dts-hd[ .]?[ma]*|hdts|dts)(?:{0}|$)".format(Seps),re.U|re.I)

#List of formal tags and other known words that can appear but have no meaning for autosub
tags = [
    '10bit',
    'alternative.cut',
    'buymore',
    'colorized',
    'convert',
    'dc',
    'dirfix',
    'dubbed',
    'english',
    'extended',
    'final',
    'hevc',
    'internal',
    'nfofix',
    'nzbgeek',
    'oar',
    'om',
    'ppv',
    'pre',
    'proper',
    'readnfo',
    'real',
    'remastered',
    'repack',
    'rerip',
    'samplefix',
    'scrambled',
    'source.sample',
    'subbed',
    'uncensored',
    'uncut',
    'unrated',
    'west.feed',
    'ws'
    ]

# Dictionaries containing as keys, the nonstandard naming. Followed by there standard naming.
# Very important!!! Should be unicode and all LOWERCASE!!!

distro_syn = {
    u'amazon'  : u'amzn',
    u'netflix' : u'nf',
    u'starz'   : u'stz',
    u'bravo'   : u'brav',
    u'byutv'   : u'byu'
    }

source_syn = {
    u'ahdtv'  : u'hdtv',
    u'dvdrip' : u'dvdrip',
    u'dvd'    : u'dvdrip',
    u'bdrip'  : u'bluray',
    u'blu-ray': u'bluray',
    u'brrip'  : u'bluray',
    u'webdl'  : u'web-dl'
    }

quality_syn = {
    u'2160p': u'4K',
    u'2160' : u'4K',
    u'UHD'  : u'4K',
    u'1080i': u'1080',
    u'1080p': u'1080',
    u'720p' : u'720',
    u'720i' : u'720',
    u'hd'   : u'720'
    }


#Note: just 264(5)  we assume x264(5).
codec_syn = {
    u'x.264' : u'x264',
    u'h.264' : u'h264',
    u'x265'  : u'x265',
    u'x.265' : u'x265',
    u'h.265' : u'h265'
    }


# Dict with compatible release groups
twin_rlsgrp = {
    u'dimension' : u'lol',
    u'lol'       : u'dimension',
    u'immerse'   : u'asap',
    u'asap'      : u'immerse',
    u'avs'       : u'sva',
    u'sva'       : u'avs',
    u'fleet'     : u'killers',
    u'killers'   : u'fleet'
    }

#The following variables create the regexes used for guessing the releasegrp. Functions should not call them!

rlsgrps_hdtv =  [
    '0sec',
    '2hd',
    'asap',
    'ascendance',
    'avs',
    'bia',
    'brisk',
    'compulsion',
    'ctu',
    'dimension',
    'evolve',
    'excellence',
    'fleet',
    'fov',
    'fqm',
    'immerse',
    'knifesharp',
    'killers',
    'kyr',
    'lol',
    'momentum',
    'moritz',
    'orenji',
    'organic',
    'qcf',
    'remarkable',
    'seriously',
    'skgtv',
    'spamtv',
    'sva',
    'tla'
    ]

rlsgrps_xvid = [
    'afg',
    'fever',
    'hype',
    'haggis',
    'notv',
    'xor'
    ]

rlsgrps_webdl = [
    'bs',
    'coo7',
    'ctrlhd',
    'deflate',
    'dbr',
    'dracula',
    'eci',
    'fire',
    'fum',
    'hwd',
    'kings',
    'maos ',
    'nfhd',
    'ntb',
    'oosh',
    'pcsyndicate',
    'plls',
    'pod',
    'queens,'
    'r2d2',
    'rofl',
    'tvsmash',
    'viethd',
    'visum',
    'yfn',
    'zakh'
    ]

rlsgrps_web = ['tbs']

def _cleanUp(series_name):
    """Clean up series name by removing any . and _
    characters, along with any trailing hyphens.
    Is basically equivalent to replacing all _ and . with a
    space, but handles decimal numbers in string, for example:
    >>> cleanRegexedSeriesName("an.example.1.0.test")
    'an example 1.0 test'
    >>> cleanRegexedSeriesName("an_example_1.0_test")
    'an example 1.0 test'
    """
    try:
        series_name = re.sub("(\D)\.(?!\s)(\D)", "\\1 \\2", series_name)
        series_name = re.sub("(\d)\.(\d{4})", "\\1 \\2", series_name)  # if it ends in a year then don't keep the dot
        series_name = re.sub("(\D)\.(?!\s)", "\\1 ", series_name)
        series_name = re.sub("\.(?!\s)(\D)", " \\1", series_name)
        series_name = series_name.replace("_", " ")
        series_name = re.sub("-$", "", series_name)
        return capwords(series_name)
    except:
        log.error("Cleanup problem of: %s" % serie_name)
        return None

def ProcessName(Info,FullName=False):
    try:
        show_dict = {}
        if FullName:
            for reg in show_regex:
                match = re.search(reg, Info)
                if match:
                    show_dict.update(match.groupdict())
                    show_dict['show']  = _cleanUp(show_dict['show'])
                    show_dict['info'] = match.groupdict()['info'].lower()
                    break
            if not (show_dict.get('show') and show_dict.get('season') and show_dict.get('episode')):
                return None
        else:
            show_dict['info'] = Info.lower()
                # Search for the different info fields with the regexes.

        Pos = len(show_dict['info'])
        Match = quality.search(show_dict['info'])
        if Match:
            show_dict['quality'] = quality_syn.get(Match.group(1),Match.group(1))
            if Match.start(1) < Pos :
                Pos = Match.start(1)
            show_dict['info'] = show_dict['info'].replace(Match.group(1),'')
        else:
            show_dict['quality'] = None

        Match = distro.search(show_dict['info'])
        if Match:
            show_dict['distro'] = distro_syn.get(Match.group(1),Match.group(1))
            if Match.start(1) < Pos :
                Pos = Match.start(1)
            show_dict['info'] = show_dict['info'].replace(Match.group(1),'')
        else:
            show_dict['distro'] = None

        Match = source.search(show_dict['info'])
        if Match:
            show_dict['source'] = source_syn.get(Match.group(1),Match.group(1))
            if Match.start(1) < Pos :
                Pos = Match.start(1)
            show_dict['info'] = show_dict['info'].replace(Match.group(1),'')
        else:
            show_dict['source'] = None

        Match = codec.search(show_dict['info'])
        if Match:
            show_dict['codec'] = codec_syn.get(Match.group(1),Match.group(1))
            if Match.start(1) < Pos :
                Pos = Match.start(1)
            show_dict['info'] = show_dict['info'].replace(Match.group(1),'')
        else:
            show_dict['codec'] = None

            # Remove audio identifiers
        Match = audio.search(show_dict['info'])
        if Match:
            if Match.start(1) < Pos : Pos = Match.start(1)
            show_dict['info'] = show_dict['info'].replace(Match.group(1),'')
        for tag in tags:
            Found = show_dict['info'].find(tag)
            if Found != -1:
                show_dict['info'] = show_dict['info'].replace(tag,'')
                if  Found < Pos:
                    Pos = Found
            # Remove everything (normaly the episode title) before the attributes (quality,tag, distro,source and codec)
        show_dict['info'] = show_dict['info'][Pos:]
        show_dict['info'] = re.sub("[][. {}]+",".",show_dict['info'])

            # Check if a releasegroup name is in the info string
        show_dict['rlsgrplst'] = []
        try:
            End = len(show_dict['info'])
            for item in autosub.RLSGRPS:
                    # Make sure the releasegroup is surrounded with seperators
                Pos = show_dict['info'].find(item)
                if Pos != -1:
                    if (Pos == 0 or show_dict['info'][Pos-1] in Seps) and (Pos + len(item) == End or show_dict['info'][Pos+len(item)] in Seps):
                        show_dict['rlsgrplst'].append(item)
                        if Pos > 0 and show_dict['info'][Pos-1] == '-':
                            show_dict['info'] = show_dict['info'].replace('-' + item,'')
                        else:
                            show_dict['info'] = show_dict['info'].replace(item,'')
                        End = len(show_dict['info'])
        except Exception as error:
            log.error('Problem finding group. %s' % error)

            # unknown release group, try to find it via the nameing convention (e.g. starts with -)
        if not show_dict['rlsgrplst'] and show_dict['info']:
            Matches = re.findall("-(\w*)",show_dict['info'])
            for Match in Matches:
                if Match:
                    show_dict['rlsgrplst'].append(Match)
    # Check if we can add info by combining known info
        if not show_dict['source'] and show_dict['rlsgrplst']:
            for rlsgrp in show_dict['rlsgrplst']:
                if rlsgrp in rlsgrps_webdl  : show_dict['source'] = u'web-dl'
                if rlsgrp in rlsgrps_web    : show_dict['source'] = u'web'
                if rlsgrp in rlsgrps_hdtv   : show_dict['source'] = u'hdtv'
                if rlsgrp in rlsgrps_xvid   : show_dict['source'] = u'xvid'
        if not show_dict['quality'] and show_dict['source'] != u'xvid':
            show_dict['quality'] = u'720'
        if show_dict['rlsgrplst']:
            show_dict['releasegrp'] = show_dict['rlsgrplst'][0]
        else:
            show_dict['releasegrp'] = None
        return show_dict
    except Exception as error:
        log.err(error)
        return None