import autosub
from xmlrpclib import Server as xmlRpcServer 
import logging
from time import time

log = logging.getLogger('thelogger')


def OS_Login(opensubtitlesusername=None,opensubtitlespasswd=None):
    autosub.OPENSUBTITLESSERVER = xmlRpcServer(autosub.OPENSUBTITLESURL)
        # Expose to test login
        # When fields are empty it will check the config file
    if opensubtitlesusername and opensubtitlespasswd:
        try:
            Result = autosub.OPENSUBTITLESSERVER.LogIn(opensubtitlesusername, opensubtitlespasswd, 'dut', autosub.OPENSUBTITLESUSERAGENT)
        except:
            log.debug('Login with user %s failed.'  % opensubtitlesusername)
            return False
        if opensubtitlesusername or opensubtitlespasswd:
            log.info('Test Login with User %s. Result is: %s' %  (opensubtitlesusername,Result['status']))
        else:
            log.debug('Login with User %s. Result is: %s' %  (opensubtitlesusername,Result['status']))
        if Result['status'] == '200 OK':
            autosub.OPENSUBTITLESTIME = time()
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
                log.debug('Login with user %s failed.'  % autosub.OPENSUBTITLESUSER)
                return False
            log.info('Logged in as %s.' % autosub.OPENSUBTITLESUSER)
            if Result['status'] == '200 OK':
                autosub.OPENSUBTITLESTIME = time()
                autosub.OPENSUBTITLESTOKEN = Result['token']
            else:
                log.debug('Could not establish a Session with the opensubtitle API server.')        
                autosub.OPENSUBTITLESTOKEN = None
                return False
        else:
            log.debug('Already Logged in with user %s'  % autosub.OPENSUBTITLESUSER)
            return True

def OS_Logout():
    if autosub.OPENSUBTITLESTOKEN:  
        try:
            Result = autosub.OPENSUBTITLESSERVER.LogOut(autosub.OPENSUBTITLESTOKEN)
        except:
            autosub.OPENSUBTITLESTOKEN = None
            log.error('Logout with User %s failed. Probably a lost connection' % autosub.OPENSUBTITLESUSER)
            return False
        if Result['status'] == '200 OK':
            autosub.OPENSUBTITLESTOKEN = None
            log.debug('Logged out.')
            return True
        else:
            autosub.OPENSUBTITLESTOKEN = None
            log.debug('Logout with User %s failed. Message is: %s' %  (autosub.OPENSUBTITLESUSER, Result['status']))
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