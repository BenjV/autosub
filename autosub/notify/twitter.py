import library.pythontwitter as twitter
import autosub
import logging

log = logging.getLogger('thelogger')

try:
    from urlparse import parse_qsl
except:
    from cgi import parse_qsl

CONSUMER_KEY = 'CRMvUogoJ5kMErtU9fiw'
CONSUMER_SECRET = 'JqS5jJIWdokl5iijZmoBHNwRsknw7xmCxPggEsmo8'

REQUEST_TOKEN_URL = 'https://api.twitter.com/oauth/request_token'
ACCESS_TOKEN_URL = 'https://api.twitter.com/oauth/access_token'
AUTHORIZATION_URL = 'https://api.twitter.com/oauth/authorize'
SIGNIN_URL = 'https://api.twitter.com/oauth/authenticate'

def _send_notify(message, twitterkey, twittersecret):
    if not twitterkey:
        twitterkey = autosub.TWITTERKEY
            
    if not twittersecret:
        twittersecret = autosub.TWITTERSECRET      
    try:
        api = twitter.Api(CONSUMER_KEY, CONSUMER_SECRET, twitterkey, twittersecret)
        api.PostUpdate(message[:140])
        log.info("Twitter: notification sent.")
        return True
    except:
        log.error("Twitter: notification failed.")
        return False

def test_notify(twitterkey, twittersecret):
    log.debug("Twitter: Testing notification.")
    message = 'Testing Twitter settings from Auto-Sub.'
    return _send_notify(message, twitterkey, twittersecret)

def send_notify(lang, subtitlefile, videofile, website):
    log.debug("Twitter: Trying to send a notification.")
    NonUrlName = subtitlefile.replace('.',u".\u200B")
    message = "%s downloaded from %s" %(NonUrlName, website)
    twitterkey = autosub.TWITTERKEY
    twittersecret = autosub.TWITTERSECRET
    return _send_notify(message, twitterkey, twittersecret)
   
