#
# The Addic7ed method specific module
#
import re
import requests
from time import time, sleep
import autosub
from autosub.Helpers import CleanName
import logging

log = logging.getLogger('thelogger')
    
class Addic7edAPI():
    def __init__(self):
        self.session = requests.Session()
        self.lasttime = time()
        self.server = 'http://www.addic7ed.com'
        self.session.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Trident/7.0; rv:11.0) like Gecko', 'Referer' : self.server}
        self.show_ids = {}

    def A7_Login(self, addic7eduser=None, addic7edpasswd=None):
        try:
            if not self.session.head(self.server,timeout=13).ok:
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
        try:
            Result = self.session.post(self.server + '/dologin.php', data,timeout=22)
        except Exception as error:
            log.error('%s' % error)
            return False        
        if Result.status_code < 400:
            autosub.ADDIC7EDLOGGED_IN = True
            self.geta7ID()
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

    def A7_Logout(self):
        if autosub.ADDIC7EDLOGGED_IN:
            autosub.ADDIC7EDLOGGED_IN = False
            try:
                Result = self.session.get(self.server + '/logout.php', timeout=22)
                log.debug('Addic7ed logged out')
            except Exception as error:
                log.error('%s' % error)
            if Result.status_code >= 400:
                log.error('Addic7ed logout failed with status code %d' % Result.status_code)
        self.session.close()
        autosub.ADDIC7EDAPI = None
        autosub.ADDIC7EDLOGGED_IN = False

    def getpage(self, Page, Delay=True):
        """
        Make a GET request on `url`
        :param string url: part of the URL to reach with the leading slash
        :rtype: text
        """
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
            try:
                Result = self.session.get(SearchUrl,timeout=22)
                self.lasttime = time()
            except Exception as error:
                log.error('%s' % error)
                Count += 1
                continue
            if Result.status_code < 400:
                #Result.encoding = Result.apparent_encoding
                return Result.text
            else:
                log.error('A7 request failed with status code %d' % Result.status_code)
                sleep(2)
                Count += 1
        return None
 
    def A7_download(self, downloadlink):
        try:
            Result = self.getpage(downloadlink)
            if Result:
                autosub.DOWNLOADS_A7 += 1
                log.debug('Successfuly downloaded a sub from Addic7ed.')
                if time() > autosub.DOWNLOADS_A7TIME + 43200:
                    self.getA7Info()
                return Result
            else:
                return None
        except Exception as error:
            log.error('Unexpected error: %s' % error)
        return None
    
    def getA7Info(self):
        try:
            PageBuffer = self.getpage('/panel.php')
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
        return True    
    
    def geta7ID(self, ShowName=None):
 
        # Read the Addic7ed show pages and put the showname's and Addic7ed's in a dict
        if not self.show_ids : 
            Delay = True if ShowName else False
            Result = self.getpage('/shows.php', Delay)
            if not Result:
                return None
            AddicName = u''
            for url in re.findall(r'<a href=[\'"]/show/?([^<]+)', Result, re.I|re.U):
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