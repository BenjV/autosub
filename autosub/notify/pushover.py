import logging
import autosub
import library.requests as requests
log = logging.getLogger('thelogger')

API_URL = "https://api.pushover.net/1/messages.json"

def test_notify(pushoverappkey, pushoveruserkey, priority):
    message = "Testing Pushover settings from AutoSub"
    return _send_notify(pushoverappkey, pushoveruserkey,message,priority)

def send_notify(lang, subtitlefile, videofile, website):
    log.debug("Trying to send a notification")
    message = "%s downloaded from %s" %(subtitlefile, website)
    return _send_notify(autosub.PUSHOVERAPPKEY,autosub.PUSHOVERUSERKEY ,message,autosub.PUSHOVERPRIORITY)

def _send_notify(appkey,userkey,message,priority):
    """
    Sends a pushover notification to the address provided
    userKey: The pushover user key to send the message to (or to subscribe with)   
    msg: The message to send (unicode)
    returns: True if the message succeeded, False otherwise
    """
    params = {
                'token': appkey,
                'user': userkey,
                'title': 'Auto-Sub',
                'message': message,
                'retry': 30, 
                'expire': 180,
                'priority': priority,
            }
    try:
        msg = requests.post('https://api.pushover.net/1/messages.json', data=params).json()
    except:
        log.error('Problem sending Pushover message.')
        return False
    if msg['status'] == 0 :
        log.error('Pushover error is: %s' % msg['errors'][0])
        return False
    return True
