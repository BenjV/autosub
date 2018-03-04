#
# The Autosub downloadSubs module
# Scrapers are used for websites:
# Podnapisi.net, Subscene.com
# and addic7ed.com
#
import autosub
import logging
from OpenSubtitles import OS_NoOp
import library.requests as requests
import zipfile
import re 
from urlparse import urljoin
import os, shutil, errno, subprocess, sys,codecs
import time
from Tvdb import FindEpTitle
from subprocess import Popen, PIPE
from library.requests.packages import chardet

import xmlrpclib, io, gzip
# Settings
log = logging.getLogger('thelogger')


def _getzip(Session, url):
    # returns a file-like String object    
    try:
        Result = Session.get(url,verify=autosub.CERT,timeout=15)
    except:
        log.debug("Zip file at %s couldn't be retrieved" % url)
        return None
    try: 
       zip =  zipfile.ZipFile(io.BytesIO(Result.content))
    except Exception as error:
        log.debug("Expected a zip file but got error for link %s" % url)
        log.debug("%s is likely a dead link" % url)
        return None
    nameList = zip.namelist()
    for name in nameList:
        # sometimes .nfo files are in the zip container
        if name.lower().endswith('srt'):
            try:
                Data = zip.read(name)
                if Data.startswith(codecs.BOM_UTF8 ):
                    SubData = unicode(Data[3:],'UTF-8')
                else:
                    Codec = chardet.detect(Data)['encoding']
                    SubData = unicode(Data,Codec)
                if SubData:
                    return SubData
            except Exception as error:
                log.error(error.message)
    log.debug("No subtitle files was found in the zip archive for %s" % url)
    return None
  

def _OSdownload(SubId, SubCodec):

    log.debug("Download subtitle: %s" % SubId)
    time.sleep(1)
    if not OS_NoOp():
        return None
    try:
        Result = autosub.OPENSUBTITLESSERVER.DownloadSubtitles(autosub.OPENSUBTITLESTOKEN, [SubId])
    except:
        autosub.OPENSUBTITLESTOKEN = None
        log.error('Error from Opensubtitles download API. DownloadId is: %s' %SubId)
        return None 

    if Result['status'] == '200 OK':
        try:
            CompressedData = Result['data'][0]['data'].decode('base64')
        except Exception as error:
            log.error('Error decompressing sub from opensubtitles. Message is: %s' % error) 
            return None
        if not CompressedData:
            log.debug('No data returned from DownloadSubtitles API call. Skipping this one.')
            return None
        SubDataBytes = gzip.GzipFile(fileobj=io.BytesIO(CompressedData)).read()
        # Opensubtitles makes no difference in UTF-8 and UTF8-SIG so we check with chardet the correct encoding
        # if Opensubtile does not know the encoding we assume windows-1252 is used.
        if SubCodec:
            if 'UTF' in SubCodec.upper() or SubCodec == 'Unknown':
                SubCodec = chardet.detect(SubDataBytes)['encoding']
            elif '1252' in SubCodec:
                SubCodec = u'cp1252'
            elif '850' in SubCodec:
                SubCodec = u'cp850'
        else:
            SubCodec = chardet.detect(SubDataBytes)['encoding']
            if not 'UTF' in SubCodec.upper():
                SubCodec = u'cp1252'
        try:
            SubData = SubDataBytes.decode(SubCodec,errors='replace')
        except Exception as error:
            log.error('Error decoding sub from opensubtitles. Message is: %s' % error)
            return None
        return(SubData)
    else:
        if Result['status'][:3] == '406':
            autosub.OPENSUBTITLESTOKEN = None
        log.error('Message : %s' % Result['status'])
        return None

def _SSdownload(subSeekerLink,website):

    time.sleep(1)
    try:
        SubLinkPage = autosub.SS_SESSION.get(subSeekerLink,timeout=10)
    except Exception as error:
        log.error("Failed to find the link on SubtitleSeekers. Message : %s" % error)        
        return None
    
    try:
        SubLink = re.findall('Download : <a href="(.*?)"', SubLinkPage.text)[0]
    except Exception as error:
        log.error("Failed to find the redirect link on SubtitleSeekers. Message : %s" % error.message)        
        return None
    try:
        Result= autosub.SS_SESSION.get(SubLink,verify=autosub.CERT,timeout=10)
    except Exception as error:
        log.error("Failed to get the downloadpage from %s. Message : %s" % (website,error.message)) 
        return None
    if Result.status_code > 399 or not Result.text:
        return False
    Result.encoding = 'utf-8'

    DownLoadLink = None
    if website == 'podnapisi':
        try:
            DownLoadLink = re.findall('form-inline download-form\" action=(.*?)>', Result.text)[0]
        except:
            log.error("Could not find the subseeker link on the podnapisi website.") 
            return None
        DownLoadLink = urljoin('https://www.podnapisi.net', DownLoadLink) if DownLoadLink else None
    elif website =='subscene':
        try:
            DownLoadLink = re.findall('<a href=\"/subtitle/download(.*?)\"', Result.text)[0]
        except:
            log.error("Could not find the subseeker link on the subscene website.") 
            return None
        DownLoadLink = urljoin('http://www.subscene.com/subtitle/download', DownLoadLink) if DownLoadLink else None
    if not DownLoadLink:
        log.error('Could not find the downloadlink %s on %s' % (DownLoadLink, website))
        return None
    SubData = _getzip(Session, DownLoadLink)
    if SubData:
        return(SubData)
    else:
        return None

def WriteSubFile(SubData, SubFileOnDisk):
        # this routine tries to write the sub but first check if it is a correct sub
        # this is done by checking the first two line for the correct subtitles format
    StartPos = 3 if SubData[1] == u'\r' else 2
    if SubData[0] == '1' and re.match("\d{2}:\d{2}:\d{2},\d{3}\s*-->\s*\d{2}:\d{2}:\d{2},\d{3}",SubData[StartPos:StartPos + 29]):
        try:
            if not autosub.SEARCHSTOP:
                autosub.WRITELOCK = True
                with io.open(SubFileOnDisk, 'wb') as fp:
                    fp.write(SubData.encode(autosub.SUBCODEC,errors='replace'))
                autosub.WRITELOCK = False
                log.debug("%s is saved." % SubFileOnDisk)
                try:
                    if sys.platform != "win32":
                        Permission = int(str(autosub.SUBRIGHTS['owner']) + str(autosub.SUBRIGHTS['group']) + str(autosub.SUBRIGHTS['world']),8)
                        os.chmod(SubFileOnDisk, Permission)
                except Exception as error:
                    log.error(error.message)
            else:
                log.info("Stopped by User intervention.")
                return False
            return True
        except Exception as error:
            autosub.WRITELOCK = False
            log.error(error.message)
    else:
        log.error('File is not a valid subtitle format. skipping it.')
    return False  

def MyPostProcess(Wanted,SubSpecs,Sub):
    VideoSpecs = os.path.join(Wanted['folder'],Wanted ['file']+ Wanted['container'])
    SerieName  = Wanted['show'][:-1] if  Wanted['show'].endswith('.') else Wanted['show']
    SerieName  = re.sub(r'[\0/:*?"<>|\\]', r'',SerieName)
    DstRoot    = os.path.normpath('/volume1/video/Alleen Series')
    ffmpegLoc  = os.path.normpath('/volume1/@appstore/ffmpeg/bin/ffmpeg')

    log.debug('Starting Postprocess')
    SeasonDir     = 'Season ' + Wanted['season']
    EpisodeName = Sub.get('title')
    if not EpisodeName:
        EpisodeName = FindEpTitle(Wanted['TvdbId'],Wanted['season'], Wanted['episode'])
        try:
            EpisodeName = re.sub(r'[\0/:*?"<>|\\]', r'',EpisodeName)
        except Exception as error:
            log.debug('Error removing chars from EpisodeName')
    # Here we create the various file specifications
    DstDir        = os.path.join(DstRoot, SerieName, SeasonDir)
    DstVidSpecs   = os.path.join(DstDir, Wanted['episode'] + ' ' + EpisodeName + Wanted['container'])
    DstSubSpecs   = os.path.join(DstDir, Wanted['episode'] + ' ' + EpisodeName + '.srt')

    # Now we check whether the "Season" directory already exists
    # if not we create it.
    try:
        os.makedirs(DstDir)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            log.debug('Could not create destination folder')
            return
    log.debug('Destination Dir is %s' % DstDir)
    # muxing is not possible for all containers only .mkv and .mp4 are supported
    # if muxing is off, the video and the sub will be copied to the desitnation.
    if Wanted['container'] == '.mkv' or  Wanted['container'] == '.mp4':
        Muxing = True
    else:
        Muxing = False

    Cmd = [ffmpegLoc, '-loglevel error -n -i',VideoSpecs,'-i',SubSpecs,'-c copy -map 0:V -map 0:a -map 1:s -metadata:s:s:0 language=dut -disposition:s:s:0 +default+forced', DstVidSpecs]
    log.debug('ffmpegCmd is %s' % Cmd)
    ToRemove = VideoSpecs
    if Muxing:
        try:
            error = None
            ffmpeg_error = None
            Merge = subprocess.Popen(Cmd, stderr = subprocess.PIPE)
            output,ffmpeg_error = Merge.communicate()
            if ffmpeg_error:
                log.error("ffmpeg error: %s" % error)
                Muxing = False
                ToRemove = DstVidSpecs
        except Exception as error:
            log.error(error.message)
            Muxing = False
            ToRemove = DstVidSpecs
            # if muxing failed remove the leftover else remove the original video.
        try:
            os.remove(ToRemove)
        except Exception as error:
            log.error(error.message)

        # No muxing done so we copy the video and the sub to the destination
    if not Muxing:
        try:
            shutil.move(VideoSpecs,DstVidSpecs)
            shutil.copy2(SubSpecs,DstSubSpecs)
            try:
                os.remove(VideoSpecs)
            except Exception as error:
                log.error(error.message)
        except Exception as error:
            log.error(error.message)

def _add_to_down(Wanted, Found):
    Downloaded = []
    Downloaded.append(0)
    Downloaded.append(Wanted['show'])       #1
    Downloaded.append(Wanted['season'])     #2
    Downloaded.append(Wanted['episode'])    #3
    Downloaded.append(Found['timestamp'])   #4
    Downloaded.append(Found['source'])      #5
    Downloaded.append(Found['distro'])      #6
    Downloaded.append(Found['releasegrp'])  #7
    Downloaded.append(Found['quality'])     #8
    Downloaded.append(Found['codec'])       #9
    Downloaded.append(Found['website'])     #10
    Downloaded.append(Found['language'])    #11
    Downloaded.append(Found['title'])       #12
    Downloaded.append(Found['location'])    #13
    Downloaded[0] = autosub.DOWNLOADS.addDown(Downloaded[1:])
    if Downloaded[0] != 0:
        autosub.DOWNLOADED.append(tuple(Downloaded[0:12]))

def DownloadSub(Wanted,SubList):    
    destdir = Wanted['folder']
    destsrt = os.path.join(Wanted['folder'], Wanted['file'])
    if autosub.DUTCH in SubList[0]['language'] :
        destsrt += Wanted['NLext']
    elif autosub.ENGLISH in SubList[0]['language'] :
        destsrt += Wanted['ENext']
    else:
        return False

    SubData = None
    Downloaded = False 
    for Sub in SubList:
        log.debug("Downloading %s subtitle(s) from %s with: %s" % (Sub['language'],Sub['website'],Sub['url']))      
        if Sub['website'] == 'opensubtitles':
            log.debug("Api for OpenSubtitles is chosen for subtitle %s" % Wanted['file'])
            SubData = _OSdownload(Sub['url'],Sub['SubCodec'])
                #Add the subfile tot the bad sub list if not a correct sub to prevent downloading it again.
            if not SubData:
                autosub.OPENSUBTITLESBADSUBS.append(Sub['url'])
        elif Sub['website'] == 'addic7ed':
            log.debug("Scraper for Addic7ed is chosen for subtitle %s" % Wanted['file'])
            SubData = autosub.ADDIC7EDAPI.A7_download(Sub['url'])
        else:
            log.debug("Scraper for %s is chosen for subtitle %s" % (Sub['website'],Wanted['file']))
            SubData = _SSdownload(Sub['url'],Sub['website'])
        if SubData:
            if WriteSubFile(SubData,destsrt):
                Downloaded = True           
                break
    time.sleep(0.1)
    if Downloaded:
        log.info('%s subtitle for "%s" is downloaded from %s' % (Sub['language'],Sub['releaseName'],Sub['website']))
    else:
        log.info("Could not download any correct subtitle file for %s" % Wanted['file'])
        return False   
    Wanted['subtitle'] = "%s downloaded from %s" % (Sub['releaseName'].strip(),Sub['website'])
    Sub['timestamp'] = unicode(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(os.path.getmtime(destsrt))))
    Sub['location'] = destsrt
    _add_to_down(Wanted,Sub)

        # Send notification if activated
    if (autosub.NOTIFYNL and Sub['language'] == autosub.DUTCH) or (autosub.NOTIFYEN and Sub['language'] == autosub.ENGLISH):
        import autosub.notify as notify
        notify.notify(Sub['language'], Sub['releaseName'],Sub['website'].split('.')[0])

        # spawn the postprocess if present
    if autosub.POSTPROCESSCMD:
        VideoFile = os.path.join(Wanted['folder'] , Wanted['file'] + Wanted['container'])
        Language = 'Dutch' if Sub['language'] == u'nl' else 'English'
        Cmd = autosub.POSTPROCESSCMD + ' "' + destsrt + '" "' + VideoFile + '" "' + Language + '" "' + Wanted['show'] + '" "' + Wanted['season'] + '" "' + Wanted['episode'] + '" '
        log.info("Postprocess: %s" % Cmd)
        try:
            PostProcess = subprocess.Popen(Cmd.encode(autosub.SYSENCODING), shell = True, stdin = PIPE, stdout = PIPE, stderr = PIPE)
            PostProcessOutput, PostProcessErr = PostProcess.communicate()
        except Exception as error:
            log.error('Problem starting postprocess. Error is: %s' % error.message)
        if PostProcess.returncode != 0 or PostProcessErr:
            log.error(PostProcessErr)
        else:
            log.debug('Postprocess succesfully finished!')
    if autosub.NODE_ID == 73855751279:
        log.debug('Starting my postprocess')
        MyPostProcess(Wanted,destsrt,Sub)
    log.debug('Finished for %s' % Wanted["file"])
    return Downloaded
