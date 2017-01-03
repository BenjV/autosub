#
# The Autosub common module
#
# Based on Sickbeard & Guesit, thanks!
# 

import re

#List with all the possible seperators used in filenaming
seperator = u', ._-()[]{}'

show_regex = [re.compile("^((?P<title>.+?)[. _-]+)?s(?P<season>\d+)[x. _-]*e(?P<episode>\d+)[x. _-]*(?P<extra_info>.+)*", re.IGNORECASE),
              re.compile("^((?P<title>.+?)[. _-]+)?(?P<season>\d+)x(?P<episode>\d+)[x. _-]*(?P<extra_info>.+)*", re.IGNORECASE),
              re.compile("^((?P<title>.+?)[. _-]+)?(?P<season>\d{1,2})(?P<episode>\d{2})[x. _-]*(?P<extra_info>.+)*", re.IGNORECASE)]

episode_regex = [re.compile("(s\d+[x. _-]*e\d+|\d+x\d+)", re.IGNORECASE)]

#Every part of the file_info got a list with regex. The first item in this list should be the standardnaming
#The second (and following) regex contains nonstandard naming (either typo's or other renaming tools (like sickbeard)) 
#Nonstandard naming should be renamed using the syn dictionary. 

source = [re.compile("(ahdtv|hdtv|web[. _-]*dl|blu[. _-]*ray|brrip|dvdrip|web[-]*rip|hddvd)", re.IGNORECASE),
          re.compile("(dvd|bdrip|web)", re.IGNORECASE)]

#A dictionary containing as keys, the nonstandard naming. Followed by there standard naming.
#Very important!!! Should be unicode and all LOWERCASE!!!
source_syn = {u'ahdtv'  : u'hdtv',
              u'dvd'    : u'dvdrip',
              u'bdrip'  : u'bluray',
              u'blu-ray': u'bluray',
              u'brrip'  : u'bluray',
              u'webdl'  : u'web-dl',
              u'web'    : u'web-dl',
              u'web-rip': u'webrip'}

quality = [re.compile("(1080p|720p)" , re.IGNORECASE), 
           re.compile("(1080[i]*|720|HD|SD)", re.IGNORECASE)]

quality_syn = {u'1080' : u'1080p',
               u'1080i': u'1080p',
               u'720'  : u'720p',
               u'hd'   : u'720p'}

#A dictionary containing as keys fileextensions followed by the matching quality.
#If the quality regex fails, ProcessFile will look in this dictionary. If the fileextension
#is not here, it will guess that the quality is SD. 
quality_fileext = {u'.mkv' : u'720p',
                   u'.mp4' : u'720p',
                   u'.avi' : u'sd'}

codec = [re.compile("([xh]*264|[xh]*265|xvid|dvix)" , re.IGNORECASE)]

#Note: x264 is the opensource implementation of h264.
codec_syn = {u'x264' : u'h264',
             u'264'  : u'h264',
             u'x265' : u'h265',
             u'265'  : u'h265'}

codec_fileext = {u'.mkv' : u'h264',
                 u'.mp4' : u'h264',
                 u'.avi' : u'xvid'}

#The following variables create the regexes used for guessing the releasegrp. Functions should not call them!
rlsgrps_rest = ['0TV',
                'aAF',
                'AG',
                'BATV',
                'BTN',
                'BWB',
                'C4TV',
                'ChameE',
                'CLUE',
                'CP',
                'CRAVERS',
                'DEMAND',
                'DHD',
                'DNR',
                'EbP',
                'eXcluSive',
                'FaiLED',
                'FUSiON',
                'GFY',
                'GreenBlade',
                'HoodBag',
                'hV',
                'LFF',
                'LP',
                'Micromkv',
                'MMI',
                'mSD',
                'NBS',
                'NFT',
                'NIN',
                'nodlabs',
                'OOO',
                'ORPHEUS',
                'P0W4',
                'P0W4HD',
                'playXD',
                'PublicHD',
                'RARBG',
                'RANDi',
                'REWARD',
                'ROVERS',
                'RRH',
                'SAiNTS',
                'SAPHiRE',
                'SCT',
                'SiNNERS',
                'SkyM',
                'SLOMO',
                'SNEAkY',
                'sozin',
                'sundox',
                'T00NG0D',
                'TASTETV',
                'TjHD',
                'TOKUS',
                'TOPAZ',
                'UP',
                'VASKITTU',
                'XS']

rlsgrps_HD =  ['0SEC',
                '2HD',
                'ASAP',
                'ascendance',
                'AVS',
                'BiA',
                'BRISK',
                'COMPULSiON',
                'CTU',
                'DIMENSION',
                'EVOLVE',
                'EXCELLENCE',
                'FLEET',
                'FoV',
                'FQM',
                'IMMERSE',
                'KNiFESHARP',
                'KILLERS',
                'KYR',
                'LOL',
                'MOMENTUM',
                'MORiTZ',
                'ORENJi',
                'ORGANiC',
                'QCF',
                'REMARKABLE',
                'SERIOUSLY',
                'SKGTV',
                'spamTV',
                'SVA',
                'TLA']

rlsgrps_xvid = ['AFG',
                 'FEVER',
                 'Hype',
                 'HAGGIS',
                 'NoTV',
                 'XOR']

rlsgrps_webdl = ['BS',
                'Coo7',
                'CtrlHD',
                'DEFLATE',
                'dbR',
                'DRACULA',
                'ECI',
                'FiRE',
                'FUM',
                'HWD',
                'KiNGS',
                'MAoS ',
                'NFHD',
                'NTb',
                'Oosh',
                'PCSYNDICATE',
                'PLLs',
                'POD',
                'QUEENS,'
                'R2D2',
                'ROFL',
                'TVSmash',
                'VietHD',
                'ViSUM',
                'YFN',
                'Zakh']

All_rlsgrps = rlsgrps_rest + rlsgrps_HD + rlsgrps_xvid + rlsgrps_webdl

_releasegrp_pre = '(' + '|'.join(All_rlsgrps) + ')'

releasegrp = [re.compile(_releasegrp_pre, re.IGNORECASE)]

#If the releasegrp is not in the list (_releasegrps), try our old regex.
releasegrp_fallback = [re.compile("(-(?P<releasegrp>[^- \.]+))?$", re.IGNORECASE)]

#If you know a result is invalid you can use the syn dict to renaming it to a None type.
releasegrp_syn = {u'dl': None}