import logging
import autosub

from library.growl import gntp
import socket

log = logging.getLogger('thelogger')

def _send_notify(message, growlhost, growlport):
    if not growlhost:
        host = autosub.GROWLHOST
            
    if growlhost:
        host = growlhost
    
    if not growlport:
        port = int(autosub.GROWLPORT)
            
    if growlport:
        port = int(growlport)
    
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
        s.send(message)
        gntp.parse_gntp(s.recv(1024)) 
        s.close()
        
        log.info("Growl: notification sent.")
        
        return True
    except socket.error:
        log.error("Growl: notification failed.")
        return False
    
def test_notify(growlhost, growlport, growlpass):
    if not growlpass:
        password = autosub.GROWLPASS
    
    if growlpass:
        password = growlpass
        
    register = gntp.GNTPRegister()
    register.add_header('Application-Name', "Auto-Sub")
    register.add_notification('Test', True)
    register.add_notification('Subtitle Download', True)
    register.add_notification('Registration', True)
    register.add_header('Application-Icon', 'http://img826.imageshack.us/img826/1281/autosub.png')
    if password != "":
        register.set_password(password)
    if not _send_notify(register.encode(), growlhost, growlport):
        return False

    notice = gntp.GNTPNotice()
    notice.add_header('Application-Name', "Auto-Sub")
    notice.add_header('Notification-Name', "Test")
    notice.add_header('Notification-Title', "Testing notification")
    notice.add_header('Notification-Text', "Testing Growl settings from Auto-Sub.")
    notice.add_header('Notification-Icon', 'http://img826.imageshack.us/img826/1281/autosub.png')
    if password != "":
        notice.set_password(password)
    return _send_notify(notice.encode(), growlhost, growlport)
    
def send_notify(lang, subtitlefile, videofile, website):
    growlhost = autosub.GROWLHOST
    growlport = autosub.GROWLPORT
    password = autosub.GROWLPASS 
    message = "%s downloaded from %s" %(subtitlefile, website)
    
    notice = gntp.GNTPNotice()
    notice.add_header('Application-Name', "Auto-Sub")
    notice.add_header('Notification-Name', "Subtitle Download")
    notice.add_header('Notification-Title', "AutoSub: Subtitle Download")
    notice.add_header('Notification-Text', message)
    notice.add_header('Notification-Icon', 'http://img826.imageshack.us/img826/1281/autosub.png')
    if password != "":
        notice.set_password(password)
    return _send_notify(notice.encode(), growlhost, growlport)
    