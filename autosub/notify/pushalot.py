import logging
import autosub
from httplib import HTTPSConnection
from urllib import urlencode

log = logging.getLogger('thelogger')

def test_notify(pushalotapi):
    log.debug("Trying to send a notification.")
    message = "Testing Pushalot settings from Auto-Sub."
    return _send_notify(pushalotapi, message)

def send_notify(lang, subtitlefile, videofile, website):
    log.debug("Trying to send a notification.")
    message = "%s downloaded from %s" %(subtitlefile, website)
    pushalotapi = autosub.PUSHALOTAPI
    return _send_notify(pushalotapi, message)

def _send_notify(pushalotapi, message):
    http_handler = HTTPSConnection("pushalot.com")
    
    if not pushalotapi:
        pushalotapi = autosub.PUSHALOTAPI

    data = {'AuthorizationToken': pushalotapi,
            'Title': "Auto-Sub",
            'Body': message.encode('utf-8') }
    
    try:
        http_handler.request("POST",
                                "/api/sendmessage",
                                headers = {'Content-type': "application/x-www-form-urlencoded"},
                                body = urlencode(data))
    except:
        log.error("Notification failed.")
        return False
    
    response = http_handler.getresponse()
    request_status = response.status

    if request_status == 200:
            log.info("Notification sent.")
            return True
    elif request_status == 410: 
            log.error("Auth failed %s" % response.reason)
            return False
    else:
            log.error("Notification failed.")
            return False