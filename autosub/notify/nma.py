import logging
import library.pynma as pynma
import autosub

log = logging.getLogger('thelogger')

def _send_notify(message, nmaapi, nmapriority):
    if not nmaapi:
        nmaapi = autosub.NMAAPI
    
    if not nmapriority:
        nmapriority = autosub.NMAPRIORITY
    
    nma_instance = pynma.PyNMA(str(nmaapi))
    resp = nma_instance.push('Auto-Sub', 'Downloaded a Subtitle', message, priority=nmapriority)
    try:
        if not resp[str(nmaapi)][u'code'] == u'200':
            log.error("Notification failed.")
            return False
        else:
            log.info("Notification sent")
            return True
    except:
        log.error("Auth failed API-key")

def test_notify(nmaapi, nmapriority):
    log.debug("Trying to send a notification")
    message = "Testing Notify My Android settings from Auto-Sub."
    return _send_notify(message, nmaapi, nmapriority)
        
def send_notify(lang, subtitlefile, videofile, website):
    log.debug("Trying to send a notification.")
    message = "%s downloaded from %s" %(subtitlefile, website)
    nmaapi = autosub.NMAAPI
    nmapriority = autosub.NMAPRIORITY
    return _send_notify(message, nmaapi, nmapriority)