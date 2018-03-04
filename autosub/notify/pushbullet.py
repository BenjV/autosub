import logging
import autosub
import json
from library.requests.auth import HTTPBasicAuth
from httplib import HTTPSConnection
from urllib import urlencode

log = logging.getLogger('thelogger')

def test_notify(pushbulletapi):
    log.debug("Trying to send a notification.")
    message = "Testing Pushbullet settings from Auto-Sub."
    return _send_notify(pushbulletapi, message)

def send_notify(lang, releasename, website):
    log.debug("Trying to send a notification.")
    message = "%s: %s downloaded from %s" %(lang, releasename, website)
    pushbulletapi = autosub.PUSHBULLETAPI
    return _send_notify(pushbulletapi, message)

def _send_notify(pushbulletapi, message):
    http_handler = HTTPSConnection("api.pushbullet.com")
    
    if not pushbulletapi:
        pushbulletapi = autosub.PUSHBULLETAPI

    mydata = {'type': u'note'.encode('utf-8'),
            'title': u'Auto-Sub'.encode('utf-8'),
            'body': message.encode('utf-8') }

    try:
        http_handler.request('POST', '/v2/pushes', body=json.dumps(mydata),
                            headers={'Content-Type': u'application/json', 'Authorization': u'Bearer %s' % pushbulletapi})  
    except:
        log.error("Notification failed.")
        return False  

    response = http_handler.getresponse()
    request_status = response.status

    if request_status == 200:
            log.info("Notification sent.")
            return True
    elif request_status == 401: 
            log.error("No valid access token provided")
            return False
    elif request_status == 403:
            log.error("The access token is not valid for that request")
            return False
    else:
            log.error("Notification failed with error")
            return False