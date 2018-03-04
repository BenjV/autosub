import autosub
import logging
from time import time

log = logging.getLogger('thelogger')


def OS_Login(opensubtitlesusername=None,opensubtitlespasswd=None):
        # Expose to test login if all fields are filled
        # Test Login are only possible if not Logged in already (uer interface does not allow it)
    if opensubtitlesusername or opensubtitlespasswd:
        if opensubtitlesusername and opensubtitlespasswd:
            Test = True
        else:
            log.info('Test login attempt without enough credentials.')
            return False
    else:
        opensubtitlesusername = autosub.OPENSUBTITLESUSER
        opensubtitlespasswd   = autosub.OPENSUBTITLESPASSWD
        Test = False

    try:
        Result = autosub.OPENSUBTITLESSERVER.LogIn(opensubtitlesusername, opensubtitlespasswd, 'dut', autosub.OPENSUBTITLESUSERAGENT)
    except Exception as error:
        log.error('Login with user %s failed. %s'  % (opensubtitlesusername,error.message))
        autosub.OPENSUBTITLESTOKEN = None
        return False
    if Result['status'] == '200 OK':
        if Test:
            log.info('OS Test Login with User %s. Result is: %s' %  (opensubtitlesusername,Result['status']))
            OS_logout(Result['token'])
            return True
        else:
            autosub.OPENSUBTITLESTIME = time()
            autosub.OPENSUBTITLESTOKEN = Result['token']
            log.debug('OS Login with User %s. Result is: %s' %  (opensubtitlesusername,Result['status']))
            return True
    else:
        autosub.OPENSUBTITLESTOKEN = None
        return False


def OS_Logout(Token=None):
    if not Token:
        Token = autosub.OPENSUBTITLESTOKEN
    autosub.OPENSUBTITLESTOKEN = None
    if Token:  
        try:
            Result = autosub.OPENSUBTITLESSERVER.LogOut(Token)
        except:
            log.error('OS logout failed. Probably a lost connection')
            return False
        if Result['status'] == '200 OK':
            log.debug('OpenSubtitles logged out.')
            return True
        else:
            log.error('Os logout failed. Message is: %s' %  (autosub.OPENSUBTITLESUSER, Result['status']))
            return False
    else:
        return True


def OS_NoOp():
    if time() - autosub.OPENSUBTITLESTIME > 840:
        try:
            Result = autosub.OPENSUBTITLESSERVER.NoOperation(autosub.OPENSUBTITLESTOKEN)
            log.debug('Max connection time exceeded, refreshing it.')
            if Result['status'] != '200 OK':
                log.debug('Error or token expired. Message: %s' % Result['status'] )
                autosub.OPENSUBTITLESTOKEN = None
                if OS_Login():
                    log.debug('Re-established connection')
                    return True
                else:
                    log.error('Could not Re-established connection. ')
                    autosub.OPENSUBTITLESTOKEN = None
                    return False
            else:
                autosub.OPENSUBTITLESTIME = time()
        except:
            log.debug('Error from Opensubtitles NoOp API. Maybe a lost connection. Trying to login again')
            if OS_Login():
                log.debug('Re-established connection')
            else:
                log.error('Could not Re-established connection. ')
                autosub.OPENSUBTITLESTOKEN = None
                return False
    return True