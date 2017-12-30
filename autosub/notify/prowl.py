import logging
import autosub

from httplib import HTTPSConnection
from urllib import urlencode

log = logging.getLogger('thelogger')

def _send_notify(data):
    try:
        http_handler = HTTPSConnection("api.prowlapp.com")
        http_handler.request("POST", "/publicapi/add", headers = {'Content-type': "application/x-www-form-urlencoded"}, body = urlencode(data))
        response = http_handler.getresponse()
        request_status = response.status
    except:
        log.error("Failed to connect to Prowl")
        return False
       
    if request_status == 200:
        log.info('notification sent.')
        return True
    elif request_status == 401:
        log.error("Authentication failed, check your API key")
        return False
    else:
        log.error("Notification failed.")
        return False

def test_notify(prowlapi, prowlpriority):
    message = 'Testing Prowl settings from Auto-Sub.'
    
    data = {'apikey': prowlapi,
            'application': 'Auto-Sub',
            'event': 'Test Message',
            'description': message.encode("utf-8"),
            'priority': prowlpriority}
    return _send_notify(data)
    
def send_notify(lang, releasename, website):
    message = "%s: %s downloaded from %s" %(lang, releasename, website)
    
    data = {'apikey': autosub.PROWLAPI,
            'application': 'Auto-Sub',
            'event': 'Subtitle Downloaded',
            'description': message.encode("utf-8"),
            'priority': autosub.PROWLPRIORITY}
    return _send_notify(data)
