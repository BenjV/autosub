import autosub
import xmlrpclib
import logging
import time

log = logging.getLogger('thelogger')


def OpenSubtitlesLogin(opensubtitlesusername=None,opensubtitlespasswd=None):

    autosub.OPENSUBTITLESSERVER = xmlrpclib.Server(autosub.OPENSUBTITLESURL)
        # Expose to test login
        # When fields are empty it will check the config file
    if opensubtitlesusername and opensubtitlespasswd:
        try:
            Result = autosub.OPENSUBTITLESSERVER.LogIn(opensubtitlesusername, opensubtitlespasswd, 'dut', autosub.OPENSUBTITLESUSERAGENT)
        except:
            log.debug('OpenSubtitlesLogin: Login with user %s failed.'  % opensubtitlesusername)
            return False
        if opensubtitlesusername or opensubtitlespasswd:
            log.info('OpenSubtitlesLogin: Test Login with User %s. Result is: %s' %  (opensubtitlesusername,Result['status']))
        else:
            log.debug('OpenSubtitlesLogin: Login with User %s. Result is: %s' %  (opensubtitlesusername,Result['status']))
        if Result['status'] == '200 OK':
            autosub.OPENSUBTITLESTIME = time.time()
            autosub.OPENSUBTITLESTOKEN = Result['token']
            return True
        else:
            autosub.OPENSUBTITLESTOKEN = None
            return False
        return True
    else:
        if not autosub.OPENSUBTITLESUSER or not autosub.OPENSUBTITLESPASSWD:
            return False
        if not autosub.OPENSUBTITLESTOKEN:
            try:
                Result = autosub.OPENSUBTITLESSERVER.LogIn(autosub.OPENSUBTITLESUSER, autosub.OPENSUBTITLESPASSWD, 'dut', autosub.OPENSUBTITLESUSERAGENT)
            except:
                log.debug('OpenSubtitlesLogin: Login with user %s failed.'  % autosub.OPENSUBTITLESUSER)
                return False
            log.info('OpenSubtitlesLogin: Logged in as %s.' % autosub.OPENSUBTITLESUSER)
            if Result['status'] == '200 OK':
                autosub.OPENSUBTITLESTIME = time.time()
                autosub.OPENSUBTITLESTOKEN = Result['token']
            else:
                log.debug('OpenSubtitlesLogin: Could not establish a Session with the opensubtitle API server.')        
                autosub.OPENSUBTITLESTOKEN = None
                return False
        else:
            log.debug('OpenSubtitlesLogin: Already Logged in with user %s'  % autosub.OPENSUBTITLESUSER)
            return True

def OpenSubtitlesLogout():
    if autosub.OPENSUBTITLESTOKEN:  
        try:
            Result = autosub.OPENSUBTITLESSERVER.LogOut(autosub.OPENSUBTITLESTOKEN)
        except:
            autosub.OPENSUBTITLESTOKEN = None
            log.error('OpenSubtitles: Logout with User %s failed. Probably a lost connection' % autosub.OPENSUBTITLESUSER)
            return False
        if Result['status'] == '200 OK':
            autosub.OPENSUBTITLESTOKEN = None
            log.debug('OpenSubtitlesLogout: Logged out.')
            return True
        else:
            autosub.OPENSUBTITLESTOKEN = None
            log.debug('OpenSubtitles: Logout with User %s failed. Message is: %s' %  (autosub.OPENSUBTITLESUSER, Result['status']))
            return False
    else:
        return True


def OpenSubtitlesNoOp():
    if time.time() - autosub.OPENSUBTITLESTIME > 840:
        try:
            Result = autosub.OPENSUBTITLESSERVER.NoOperation(autosub.OPENSUBTITLESTOKEN)
            log.debug('OpenSubtitlesNoOp: Max connection time exceeded, refreshing it.')
            if Result['status'] != '200 OK':
                log.debug('Opensubtitles: Error or token expired. Message: %s' % Result['status'] )
                autosub.OPENSUBTITLESTOKEN = None
                if OpenSubtitlesLogin():
                    log.debug('Opensubtitles: Re-established connection')
                    return True
                else:
                    log.error('Opensubtitles: Could not Re-established connection. ')
                    autosub.OPENSUBTITLESTOKEN = None
                    return False
            else:
                autosub.OPENSUBTITLESTIME = time.time()
        except:
            log.debug('Opensubtitles: Error from Opensubtitles NoOp API. Maybe a lost connection. Trying to login again')
            if OpenSubtitlesLogin():
                log.debug('Opensubtitles: Re-established connection')
            else:
                log.error('Opensubtitles: Could not Re-established connection. ')
                autosub.OPENSUBTITLESTOKEN = None
                return False
    return True