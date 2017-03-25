#
# The Autosub downloadSubs module
# Scrapers are used for websites:
# Podnapisi.net, Subscene.com, OpenSubtitles
# and addic7ed.com
#
import autosub
import logging
from autosub.OpenSubtitles import OpenSubtitlesNoOp
import library.requests as requests
import zipfile
from StringIO import StringIO
import re 
from urlparse import urljoin

import os, shutil, errno, subprocess
import time
from autosub.Tvdb import GetEpisodeName
from autosub.Db import lastDown
import autosub.notify as notify
import autosub.Helpers

try:
    import xml.etree.cElementTree as ET
except:
    import xml.etree.ElementTree as ET
import library.requests as requests
from library.requests.packages.chardet import detect
import xmlrpclib, io, gzip
# Settings
log = logging.getLogger('thelogger')


def unzip(Session, url):
    # returns a file-like StringIO object    
    try:
        Result = Session.get(url,verify=autosub.CERTIFICATEPATH)
    except:
        log.debug("unzip: Zip file at %s couldn't be retrieved" % url)
        return None
    try: 
       zip =  zipfile.ZipFile(io.BytesIO(Result.content))
    except Exception as error:
        log.debug("unzip: Expected a zip file but got error for link %s" % url)
        log.debug("unzip: %s is likely a dead link" % url)
        return None
    nameList = zip.namelist()
    for name in nameList:
        # sometimes .nfo files are in the zip container
        if name.lower().endswith('srt'):
            try:
                Data = zip.read(name)
                Codec = detect(Data)['encoding']
                fpr = io.TextIOWrapper(zip.open(name),errors='replace',encoding = Codec,newline='')
                SubData = fpr.read()
                fpr.close()
                if SubData:
                    return SubData
            except Exception as error:
                pass
    log.debug("unzip: No subtitle files was found in the zip archive for %s" % url)
    return None
  

def openSubtitles(SubId, SubCodec):

    log.debug("OpenSubtitles: Download subtitle: %s" % SubId)
    time.sleep(6)
    if not OpenSubtitlesNoOp():
        return None
    try:
        Result = autosub.OPENSUBTITLESSERVER.DownloadSubtitles(autosub.OPENSUBTITLESTOKEN, [SubId])
    except:
        autosub.OPENSUBTITLESTOKEN = None
        log.error('Opensubtitles: Error from Opensubtitles download API. DownloadId is: %s' %SubId)
        return None 

    if Result['status'] == '200 OK':
        try:
            CompressedData = Result['data'][0]['data'].decode('base64')
        except Exception as error:
            log.error('downloadSubs: Error decompressing sub from opensubtitles. Message is: %s' % error) 
            return None
        if not CompressedData:
            log.debug('DownloadSub: No data returned from DownloadSubtitles API call. Skipping this one.')
            return None
        SubDataBytes = gzip.GzipFile(fileobj=io.BytesIO(CompressedData)).read()
        # Opensubtitles makes no difference in UTF-8 and UTF8-SIG so we check with chardet the correct encoding
        # if Opensubtile does not know the encoding we assume windows-1252 is used.
        if SubCodec:
            if 'UTF' in SubCodec.upper() or SubCodec == 'Unknown':
                SubCodec = detect(SubDataBytes)['encoding']
            if not SubCodec:
                SubCodec = u'windows-1252'
        else:
            SubCodec = u'windows-1252'
        try:
            SubData = SubDataBytes.decode(SubCodec,errors='replace')
        except Exception as error:
            log.error('downloadSubs: Error decoding sub from opensubtitles. Message is: %s' % error)
            return None
        return(SubData)
    else:
        if Result['status'][:3] == '407':
            autosub.OPENSUBTITLESTOKEN = None
        log.error('Opensubtitles: Error from Opensubtitles downloadsubs API. Message : %s' % Result['status'])
        return None

def subseeker(subSeekerLink,website):

    Session = requests.session()
    time.sleep(6)
    try:
        SubLinkPage = Session.get(subSeekerLink)
    except Exception as error:
        log.error("subseeker: Failed to find the link on SubtitleSeekers. Message : %s" % error)        
        return None
    
    try:
        SubLink = re.findall('Download : <a href="(.*?)"', SubLinkPage.text)[0]
    except Exception as error:
        log.error("subseeker: Failed to find the redirect link on SubtitleSeekers. Message : %s" % error)        
        return None
    try:
        Result= Session.get(SubLink,verify=autosub.CERTIFICATEPATH)
    except Exception as error:
        log.error("subseeker: Failed to get the downloadpage from %s. Message : %s" % (website,error)) 
        return None

    if Result.status_code > 399 or not Result.text:
        return False
    Result.encoding = 'utf-8'

    if website == 'podnapisi.net':
        try:
            DownLoadLink = re.findall('form-inline download-form\" action=(.*?)>', Result.text)[0]
        except:
            log.error("subseeker: Could not find the subseeker link on the podnapisi website.") 
            return None
        DownLoadLink = urljoin('https://www.podnapisi.net', DownLoadLink) if DownLoadLink else None
    elif website =='subscene.com':
        try:
            DownLoadLink = re.findall('<a href=\"/subtitle/download(.*?)\"', Result.text)[0]
        except:
            log.error("subseeker: Could not find the subseeker link on the subscene website.") 
            return None
        DownLoadLink = urljoin('http://www.' + website  + '/subtitle/download', DownLoadLink) if DownLoadLink else None
    if not DownLoadLink:
        log.error('downloadsubs: Could not find the downloadlink %s on %s' % (DownLoadLink, website))
        return None
    SubData = unzip(Session, DownLoadLink)
    if SubData:
        return(SubData)
    else:
        return None

def WriteSubFile(SubData,SubFileOnDisk):
# this routine tries to download the sub and check if it is a correct sub
# this is done by checking the first two line for the correct subtitles format
    if SubData[0] == u'1':
        StartPos = 3 if SubData[1] == u'\r' else 2
        if re.match("\d{2}:\d{2}:\d{2},\d{3}\s*-->\s*\d{2}:\d{2}:\d{2},\d{3}",SubData[StartPos:StartPos + 29]):
            try:
                log.debug("downloadSubs: Saving the subtitle file %s to the filesystem." % SubFileOnDisk)
                fp = io.open(SubFileOnDisk, 'wb')
                fp.write(SubData.encode(autosub.SUBCODEC,errors='replace'))
                fp.close()
                os.chmod(SubFileOnDisk, 0o666)
                return True
            except Exception as error:
                log.error('WriteSubFile: Problem writing subfile. Message is: %s' %error)
                pass
        else:
            log.debug('WriteSubFile: File is not a valid subtitle format. skipping it.')
    return False  

def MyPostProcess(Wanted,SubSpecs,Language):

    VideoSpecs = os.path.join(Wanted['folder'],Wanted ['file']+ Wanted['container'])
    SerieName  = Wanted['title'][:-1] if  Wanted['title'].endswith('.') else Wanted['title']
    SerieName  = re.sub(r'[\0/:*?"<>|\\]', r'',SerieName)
    SeasonNum  = Wanted['season']
    EpisodeNum = Wanted['episode']
    ImdbId     = Wanted['ImdbId']
    TvdbId     = Wanted['TvdbId']
    DstRoot    = os.path.normpath('/volume1/video/Alleen Series')
    ffmpegLoc  = os.path.normpath('ffmpeg')


    log.debug('PostProcess: Starting Postprocess')
    SeasonDir     = 'Season ' + SeasonNum
    if 'EpisodeTitle' in Wanted.keys():
        EpisodeName = Wanted['EpisodeTitle']
    else:
        try:
            EpisodeName = GetEpisodeName(ImdbId,TvdbId,SeasonNum, EpisodeNum)
        except:
            EpisodeName = 'unknown name'
        try:
            EpisodeName = re.sub(r'[\0/:*?"<>|\\]', r'',EpisodeName)
        except Exception as error:
            log.debug('MyPostProcess: Error removing chars from EpisodeName')

    Head,SubExt   = os.path.splitext(SubSpecs)
    log.debug('PostProcess: EpisodeName is %s' % EpisodeName)

    # Here we create the various file specifications
    DstDir        = os.path.join(DstRoot, SerieName, SeasonDir)
    DstVidSpecs   = os.path.join(DstDir, EpisodeNum + ' ' + EpisodeName + Wanted['container'])
    TempFileSpecs = os.path.join(DstDir, EpisodeNum + ' ' + EpisodeName + '.tmp')
    DstSubSpecs   = os.path.join(DstDir, EpisodeNum + ' ' + EpisodeName + SubExt)
    Muxing = True

    # Now we check whether the "Season" directory already exists
    # if not we create it.
    try:
        os.makedirs(DstDir)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            log.debug('PostProcess: Could not create destination folder')
            return
    log.debug('PostProcess: Destination Dir is %s' % DstDir)
    # muxing is not possible for all containers only .mkv and .mp4 are supported
    # if muxing is off, the video and the sub will be copied to the desitnation.
    if Wanted['container'].lower() != '.mkv' and  Wanted['container'].lower() != '.mp4':
        Muxing = False

    # Here we set the language identifier for the sub during muxing
    if Language == autosub.ENGLISH:
        LangId = 'language=eng'
    else:
        LangId = 'language=dut'

    # Here we check whether the video file already exits and create the ffmpeg commandline.
    # If this videofile already exists we conclude that this is a second subtitle and we mux the the video + audio + sub from that file + this sub into a temp file.
    # afterwards we remove the origional file and rename this temp file with the original filename.
    if os.path.isfile(DstVidSpecs):
        SecondSub = True
        ffmpegCmd = [ffmpegLoc,'-loglevel','error','-n','-i',DstVidSpecs,'-i',SubSpecs,'-c', 'copy' ,'-map','0:v', '-map','0:a', '-map','0:s', '-map','1:s','-metadata:s:s:1',LangId,TempFileSpecs]
    else:
        SecondSub = False
        ffmpegCmd = [ffmpegLoc,'-loglevel','error','-n','-i',VideoSpecs,'-i',SubSpecs,'-c', 'copy' ,'-map','0:v', '-map','0:a', '-map','1:s','-metadata:s:s:0',LangId,DstVidSpecs]
    log.debug('PostProcess: ffmpegCmd is %s' % ffmpegCmd)
    if Muxing:
        Merge = subprocess.Popen(ffmpegCmd, stderr = subprocess.PIPE)
        output,error = Merge.communicate()
        if error:
            log.error("PostProcess: Error message from ffmpeg is: %s" % error)
            # Remove possible leftovers from failed muxing.
            RemoveFile = TempFileSpecs if SecondSub else DstVidSpecs
            try:
                os.remove(RemoveFile)
            except:
                pass
        else:
            if SecondSub and os.path.isfile(TempFileSpecs):
                try:
                    os.remove(DstVidSpecs)
                    try:
                        os.rename(TempFileSpecs, DstVidSpecs)
                    except:
                        log.debug("PostProcess:Problem renaming temp videofile after adding second sub.")
                except:
                    log.debug("PostProcess:Problem removing videofile after adding second sub.")
            # remove the original file if the muxed one is in place
            if os.path.isfile(DstVidSpecs) :
                try:
                    os.remove(VideoSpecs)       
                except:
                    log.debug("PostProcess:Error while removing the original videofile")
    if not Muxing or error:
        # If it is the second sub we only copy the sub to the destination
        if SecondSub:
            try:
                shutil.copy2(SubSpecs,DstSubSpecs)
            except Exception as error:
                log.error("PostProcess: Problem moving subfile. Message is: %s" % error)
                return
        else:
        # If it is the first sub we move the video to the destination 
        # also we copy the subfile to the destination leaving a copy of the sub behind
            try:
                shutil.move(VideoSpecs,DstVidSpecs)
                shutil.copy2(SubSpecs,DstSubSpecs)
            except Exception as error:
                log.error("PostProcess: Problem moving files. Message is: %s" % error)
                return
    return

def DownloadSub(Wanted,SubList):    
      
    log.debug("downloadSubs: Download dict: %r" % Wanted)
    destdir = Wanted['folder']
    destsrt = os.path.join(Wanted['folder'], Wanted['file'])
    if autosub.DUTCH in SubList[0]['Lang'] :
        destsrt += Wanted['NLext']
    elif autosub.ENGLISH in SubList[0]['Lang'] :
        destsrt += Wanted['ENext']
    else:
        return False

    SubData = None
    Downloaded = False 
    for Sub in SubList:
        log.debug("downloadSubs: Trying to download %s subtitle(s) from %s using this link %s" % (Wanted['langs'],Sub['website'],Sub['url']))      

        if Sub['website'] == 'opensubtitles.org':
            log.debug("downloadSubs: Api for opensubtitles.org is chosen for subtitle %s" % Wanted['file'])
            SubData = openSubtitles(Sub['url'],Sub['SubCodec'])
                #Add the subfile tot the bad sub list if not a correct sub to prevent downloading it again.
            if not SubData and autosub.OPENSUBTITLESTOKEN:
                autosub.OPENSUBTITLESBADSUBS.append(Sub['IDSubtitleFile'])
        elif Sub['website'] == 'addic7ed.com':
            log.debug("downloadSubs: Scraper for Addic7ed.com is chosen for subtitle %s" % Wanted['file'])
            SubData = autosub.ADDIC7EDAPI.download(Sub['url'])
        else:
            log.debug("downloadSubs: Scraper for %s is chosen for subtitle %s" % (Sub['website'],Wanted['file']))
            SubData = subseeker(Sub['url'],Sub['website'])
        if SubData:
            if WriteSubFile(SubData,destsrt):
                Downloaded = True           
                break
    if Downloaded:
        log.info("downloadSubs: Subtitle %s is downloaded from %s" % (Sub['releaseName'],Sub['website']))
        autosub.DOWNLOADED =True
    else:
        log.debug("downloadSubs: Could not download any correct subtitle file for %s" % Wanted['file'])
        return False   
    Wanted['subtitle'] = "%s downloaded from %s" % (Sub['releaseName'].strip(),Sub['website'])
    VideoTimeStamp = Wanted['timestamp']
    Wanted['timestamp'] = unicode(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(os.path.getmtime(destsrt))))
    lastDown().setlastDown(Sub['Lang'],dict = Wanted)
    Wanted['timestamp'] = VideoTimeStamp
    # Send notification 

    VideoFile = os.path.join(Wanted['folder'] , Wanted['file'] + Wanted['container'])
    notify.notify(Sub['Lang'], destsrt.encode('ascii','replace'), VideoFile.encode('ascii','replace'), Sub['website'].split('.')[0])

    if autosub.POSTPROCESSCMD:
        postprocesscmdconstructed = autosub.POSTPROCESSCMD + ' "' + destsrt + '" "' + VideoFile + '" "' + Sub['Lang'] + '" "' + Wanted["title"] + '" "' + Wanted["season"] + '" "' + Wanted["episode"] + '" '
        log.debug("downloadSubs: Postprocess: running %s" % postprocesscmdconstructed)
        log.info("downloadSubs: Running PostProcess")
        postprocessoutput, postprocesserr = autosub.Helpers.RunCmd(postprocesscmdconstructed)
        log.debug("downloadSubs: PostProcess Output:% s" % postprocessoutput)
        if postprocesserr:
            log.error("downloadSubs: PostProcess: %s" % postprocesserr)
    if autosub.NODE_ID == 73855751279:
        log.debug('DownloadSub: Starting my postprocess')
        MyPostProcess(Wanted,destsrt,Sub['Lang'])
    log.debug('downloadSubs: Finished for %s' % Wanted["file"])
    return True