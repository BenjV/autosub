# coding=utf-8


from __future__ import unicode_literals

import urllib
import urllib2
import logging
import autosub
#import library.requests as requests
log = logging.getLogger('thelogger')

#    Use Telegram to send notifications

#    https://telegram.org/



def test_notify( api_key=None,id=None):
    """
    Send a test notification
    :param id: The Telegram user/group id to send the message to
    :param api_key: Your Telegram bot API token
    :returns: the notification
    """
    return _send_notify('This is a test notification from Autosub', api_key,id)

def send_notify(lang, subtitlefile, videofile, website):
    log.debug("Telegram: Trying to send a notification")
    message = "%s downloaded from %s" %(subtitlefile, website)
    return _send_notify(message)


def _send_notify(msg, api_key=None,id=None) :
    """
    Sends a Telegram notification
    :param msg: The message string to send
    :param id: The Telegram user/group id to send the message to
    :param api_key: Your Telegram bot API token

    :returns: True if the message succeeded, False otherwise
    """
    id = autosub.TELEGRAMID if id is None else id
    api_key = autosub.TELEGRAMAPI if api_key is None else api_key

    log.debug('telegram: Notification send to ID: %s' % id)

    message = '{0} : {1}'.format('Auto-Sub', msg)
    payload = urllib.urlencode({'chat_id': id, 'text': message})
    telegram_api = 'https://api.telegram.org/bot%s/%s'

    req = urllib2.Request(telegram_api % (api_key, 'sendMessage'), payload)

    try:
        urllib2.urlopen(req)
        log.debug('telegram : message sent successfully.')
    except Exception as error:
        log.error('telegram: %s' % error)
        return False
    return True


