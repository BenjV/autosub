import autosub
import logging
import errno, json,urllib2, base64


log = logging.getLogger('thelogger')

def _send_to_kodi_json(host=None, username=None, password=None):
    """Handles communication to KODI servers via JSONRPC

    Args:
        command: Dictionary of field/data pairs, encoded via urllib and passed to the KODI JSON-RPC via HTTP
        host: KODI webserver host:port
        username: KODI webserver username
        password: KODI webserver password

    Returns:
        Returns response.result for successful commands or False if there was an error

    """
    command = '{"jsonrpc":"2.0","method":"VideoLibrary.Scan","id":1}'
    url = 'http://{0}/jsonrpc'.format(host)
    try:
        req = urllib2.Request(url, command)
        req.add_header("Content-type", "application/json")
        # if we have a password, use authentication
        if password:
            base64string = base64.encodestring('%s:%s' % (username, password)).replace('\n', '')
            req.add_header("Authorization", "Basic %s" % base64string)
        try:
            fd = urllib2.urlopen(req)
        except Exception as error:
            log.debug("notifyKodi: %s" %error )
            return False

        # parse the json result
        try:
            response = json.JSONDecoder().decode(fd)
            fd.close()
            log.debug("NotifyKodi: Result from Kodi is: %s" % result)
        except Exception as error:
            log.debug("notifyKodi: %s" %error )
            return False
        log.debug("NotifyKodi: Kodi response is: %s" % result)
        try:
            if response[0]['result']:
                return True
            else:
                return False
        except:
            return False
    except:
        return False

def test_update_library(kodiserverhost, kodiserverport, kodiserverusername, kodiserverpassword):
    kodihost = kodiserverhost + ':' + kodiserverport.strip()
    log.info("Kodi: Trying to update the Kodi library.")
    return _send_to_kodi_json(kodihost, kodiserverusername, kodiserverpassword)

def send_update_library():
    log.info("Kodi Scan: Trying to update the Kodi library.")
    kodihost = autosub.KODISERVERHOST +':' + autosub.KODISERVERPORT.strip()
    return _send_to_kodi_json(kodihost, autosub.KODISERVERUSERNAME, autosub.KODISERVERPASSWORD)