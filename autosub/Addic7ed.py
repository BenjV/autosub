#
# The Addic7ed method specific module
#
import re,codecs
import library.requests as requests
from time import time, sleep
import autosub
import logging

log = logging.getLogger('thelogger')
    
class Addic7edAPI():
    def __init__(self):
        self.session = requests.Session()
        self.lasttime = time()
        self.server = 'http://www.addic7ed.com'
        self.session.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Trident/7.0; rv:11.0) like Gecko', 'Referer' : self.server}
        self.show_ids = {}
        self.failcount = 0

    def A7_Login(self, addic7eduser=None, addic7edpasswd=None):
        try:
            if not self.session.head(self.server,timeout=4).ok:
                log.error('Addic7ed website is not reachable')
                return False
        except Exception as error:
            log.error('Addic7ed website is not reachable')
            return False

         #Expose to test login
         #When fields are empty it will check the config file
        if addic7eduser or addic7edpasswd:
            Test = True
        else:
            Test = False
            addic7eduser   = autosub.ADDIC7EDUSER
            addic7edpasswd = autosub.ADDIC7EDPASSWD

        data = {'username': addic7eduser, 'password': addic7edpasswd, 'Submit': 'Log in'}
        if not autosub.SEARCHSTOP:
            try:
                Result = self.session.post(self.server + '/dologin.php', data,timeout=10)
            except Exception as error:
                log.error(error.message)
                return False        
            if Result.status_code < 400:
                autosub.ADDIC7EDLOGGED_IN = True
                if self.getA7Info():
                    if Test:
                        log.info('Test Logged in as: %s on Addic7ed' % addic7eduser)
                        self.A7_Logout()
                    else:
                        log.debug('Logged in as: %s on Addic7ed.' % addic7eduser)
                    return True
                else:
                    log.info('Could not login with username: %s' % addic7eduser)
                    autosub.ADDIC7EDLOGGED_IN = False
                    return False
            else:
                log.error('Failed to login on Addic7ed')
                autosub.ADDIC7EDLOGGED_IN = False
                return False

    def A7_Logout(self,Forced=False):
        if autosub.ADDIC7EDLOGGED_IN:
            autosub.ADDIC7EDLOGGED_IN = False
            if not Forced:
                try:
                    Result = self.session.get(self.server + '/logout.php', timeout=13)
                    if Result and Result.status_code >= 400:
                        log.error('Addic7ed logout failed with status code %d' % Result.status_code)
                    else:
                        log.debug('Addic7ed logged out')
                except Exception as error:
                    log.error(error.message)
            else:
                log.info('No response from Addi7ed, so stop trying for now.')
            self.session.close()
            self.show_ids.clear()
            autosub.ADDIC7EDAPI = None

    def getpage(self, Page, Delay=True, Sub=False):
        """
        Make a GET request
        params:
            string url: part of the URL to reach (include leading slash)
            Boolean: do a sleep before
            Boolean: It's  a sub so remove the BOM if applicable
        :rtype: text
        """
            # If we keep getting no response we stop trying
        if self.failcount > 4:
            self.A7_Logout(True)
            return None
        SearchUrl = self.server + Page
            # For old series Addic7ed needs a second try to get the right page.
        Diff = time() - self.lasttime
        if Diff < 10 and Delay:
            sleep(10 - Diff)
        Count = 1
        while Count < 3:
            if Count == 1:
                log.debug('Url= %s'% SearchUrl)
            else:
                log.debug('Retry! Url= %s'% SearchUrl)
            if autosub.SEARCHSTOP:
                return None
            else:
                try:
                    Result = self.session.get(SearchUrl,timeout=15)
                    self.lasttime = time()
                except requests.exceptions.Timeout:
                    Count += 1
                    continue
                except Exception as error:
                    log.error(error.message)
                    self.failcount += 1
                    return None
                if Result.status_code < 400:
                    self.failcount = 0
                    if Sub and Result.apparent_encoding == 'UTF-8-SIG':
                        return Result.text[1:]
                    return Result.text
                else:
                    log.error('A7 request failed with status code %d' % Result.status_code)
                    self.failcount += 1
                    return None
        log.error('Failed to get an Addic7ed page after two retries')
        self.failcount += 1
        return None
 
    def A7_download(self, downloadlink):
        try:
            SubData = self.getpage(downloadlink,True,True)
            if SubData:
                autosub.DOWNLOADS_A7 += 1
                log.debug('Successfuly downloaded a sub from Addic7ed.')
                if time() > autosub.DOWNLOADS_A7TIME + 43200:
                    self.getA7Info()
                return SubData
            else:
                return None
        except Exception as error:
            log.error(error.message)
            return None
    
    def getA7Info(self):
        try:
            sleep(1)
            PageBuffer = self.getpage('/panel.php',False)
            if PageBuffer and re.findall(autosub.ADDIC7EDUSER,PageBuffer, re.I|re.U):
                Temp = re.findall(r'<a href=[\'"]mydownloads.php\'>([^<]+)', PageBuffer)[0].split(" ")
                autosub.DOWNLOADS_A7 = int(Temp[0])
                autosub.DOWNLOADS_A7MAX = int(Temp[2])
                autosub.DOWNLOADS_A7TIME = time()
                log.debug('Current download count for today on addic7ed is: %d' % autosub.DOWNLOADS_A7)
                return True
            else:
                log.error("Couldn't retrieve Addic7ed account info for %s. Maybe not logged in." % autosub.ADDIC7EDUSER)
                return False
        except Exception as error:
            log.error("Couldn't retrieve Addic7ed account info. Error is: %s" % error)
            return False

    def geta7ID(self, ShowName):
        if not self.show_ids:
            # Read the Addic7ed show pages and put the showname's and Addic7ed's in a dict
            if not self.show_ids:
                Result = self.getpage('/shows.php', False)
                if not Result:
                    return 0
                AddicName = u''
                for url in re.findall(r'<a href=[\'"]/show/?([^<]+)', Result.text, re.I|re.U):
                    AddicId = url.split("\">")[0]
                    if AddicId.isdigit():
                        try:
                            AddicName = url.split("\">")[1].replace('&amp;','&').upper()
                            self.show_ids[AddicName] = int(AddicId)
                        except:
                            pass
        if ShowName: 
            return self.show_ids.get(ShowName.upper(),0)
        else:
            return 0