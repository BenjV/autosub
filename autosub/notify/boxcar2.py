import logging
import autosub
import urllib, urllib2
import time

log = logging.getLogger('thelogger')

API_URL = "https://new.boxcar.io/api/notifications"

def test_notify(boxcar2token):
    if not boxcar2token:
        boxcar2token = autosub.BOXCAR2TOKEN
    
    log.debug("Trying to send a notification.")
    title = 'Auto-Sub'
    message = 'Testing Boxcar2 settings from Auto-Sub.'
    return _send_notify(message, title, boxcar2token)

def send_notify(lang, releasename, website):
    log.debug("Trying to send a notification.")
    title = 'AutoSub'
    message = "%s: %s downloaded from %s" %(lang, releasename, website)
    boxcar2token = autosub.BOXCAR2TOKEN
    return _send_notify(message, title, boxcar2token)

def _send_notify(message, title, boxcar2token):
    """
    Sends a boxcar2 notification to the address provided
    msg: The message to send (unicode)
    title: The title of the message
    boxcaruser: The access token to send notification to
    returns: True if the message succeeded, False otherwise
    """
    
    # build up the URL and parameters
    msg = message.strip().encode('utf-8')

    data = urllib.urlencode({
        'user_credentials': boxcar2token,
        'notification[title]': title + " - " + msg,
        'notification[long_message]': msg,
        'notification[source_name]': "AutoSub"
    })
    
    # send the request to boxcar2
    try:
        req = urllib2.Request(API_URL)
        handle = urllib2.urlopen(req, data)
        handle.close()
    except urllib2.URLError, e:
        # FIXME: Python 2.5 hack, it wrongly reports 201 as an error
        if hasattr(e, 'code') and e.code == 201:
            log.info("Notification successful.")
            return True
        
        # if we get an error back that doesn't have an error code then who knows what's really happening
        if not hasattr(e, 'code'):
            log.error("Notification failed." + e)
        else:
            log.error("Notification failed. Error code: " + str(e.code))
        if e.code == 404:
            log.error("Access token is wrong/not associated to a device.")
        elif e.code == 401:
            log.error("Access token not recognized.")
        elif e.code == 400:
            log.error("Wrong data sent to boxcar.")
        elif e.code == 503:
            log.warning("Boxcar server to busy to handle the request at this time.")
        return False

    log.info("Notification successful.")
    return True