#################################################################################################################
# History:                                                                                                      #
# First developed by zyronix to work with the website "Bierdopje"                                               #
# After the ending of Bierdopje collincab took over and change it to use subtitleseeker instead of Bierdopje.   #
# Donny stepped in a added the bootstrap user interface an the support for mobil devices and notifications.     #
# Later collincab added support for the website Addic7ed                                                        #
# First collingcab and later Donny abbanded the project and Benj took over the support.                         #
# He added support for the Opensubtitles API, the TVDB API v2 and numerous other options                        #
#################################################################################################################
import sys,os
# Root path
base_path = os.path.dirname(os.path.abspath(__file__))

# Insert local directories into path
sys.path.insert(0, os.path.join(base_path, 'library'))

from getopt import getopt
from time import sleep
import locale,json
import platform
import autosub
from autosub.AutoSub import start
import cherrypy



help_message = '''
Usage:
    -h (--help)     Prints this message
    -c (--config=)  Forces AutoSub.py to use a configfile other than ./config.properties, the database will be put in the same folder
    -d (--daemon)   Run AutoSub in the background
    -l (--nolaunch) Stop AutoSub from launching a webbrowser
    
Example:
    python AutoSub.py
    python AutoSub.py -d
    python AutoSub.py -d -l
    python AutoSub.py -c/home/user/config.properties
    python AutoSub.py -c/home/user
    python AutoSub.py --config=/home/user/config.properties
    python AutoSub.py --config=/home/user/config.properties --daemon
    
'''
class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg

def main(argv=None):
    Update = False
    if argv is None:
        argv = sys.argv
    try:
        opts, args= getopt(argv[1:], "hc:dlu", ["help","config=","daemon","nolaunch","updated="])
    except Exception as error:
        print error
        os._exit(1)
    # option processing
    for option, value in opts:
        if option in ("-h", "--help"):
            raise Usage(help_message)
        if option in ("-c", "--config"):
            autosub.CONFIGFILE = value
        if option in ("-l", "--nolaunch"):
            autosub.LAUNCHBROWSER = False
        if option in ("-d", "--daemon"):
            if sys.platform == "win32":
                print "ERROR: No support for daemon mode in Windows"
                # TODO: Service support for Windows
            else:
                autosub.DAEMON = True
        if option in ("-u"):
            autosub.UPDATED = True
    autosub.AutoSub.start()

if __name__ == "__main__":
    sys.exit(main())