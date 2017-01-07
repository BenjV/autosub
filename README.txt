README 

+--- AutoSub
     |
     +--- Uses SubtitleSeeker API, supporting the following website:
     |    +--- Podnapisi
     |    +--- Subscene
     |
     +--- Opensubtitles support.
     |    +--- Requires account.
     |    \--- Limited downloads per 24 hours. (Regular: 30 - VIP: 55)
     |
     +--- Addic7ed support.
     |    +--- Requires account.
     |    \--- Limited downloads per 24 hours. (Regular: 20 - VIP: 40)
     |
     +--- Notifications
     |    +--- Windows & Windows Phone
     |    |    +--- Pushalot
     |    |    \--- Growl
     |    +--- Android
     |    |    +--- Notify My Android
     |    |    \--- Pushover
     |    +--- OSX & iDevices
     |    |    +--- Pushover
     |    |    +--- Growl
     |    |    +--- Prowl
     |    |    \--- Boxcar
     |    \--- Other
     |         +--- Email
     |         +--- Twitter
     |         +--- Telegram
     |         \--- Plex Media Server
     |
     \--- Features
          +--- Mobile template, automatically detected.
          +--- Multiple folder support, separate folders with a comma. Example: D:\Series1,D:\Series2
          +--- Select which languages you want to allow(Dutch and/or English).
          +--- Select if you want a notification for a sub.
          +--- Select the suffix you want to use for the language (only one suffix can be empty)
          +--- Choose if you want to search for an other language if the dutch sub is not available
          +--- Remove English subtitle when the Dutch subtitle has been downloaded.
          +--- Configure a custom post-process script.
          +--- 
          \--- Home tables.
               +--- Both
               |    +--- Select 10, 25, 50, 100, All items to display. Options are stored using localStorage.
               |    \--- Search field, which allows you to search on show name.
               +--- Wanted
               |    +--- Option to skip show when clicking on the wrench symbol.
               |    +--- Red Color shows which match criteria is used (e.g. Source, Quality, Codec , Release Group)
               |    +--- Option to skip season when clicking on the season.
               |    +--- Show ImdbId and AddiceID which are also hyperlink tot those websites.
               +    \--- Display videofilename by hovering over the show name
               +--- Downloaded
                    +--- Display original subtitle and website by hovering over the show name
                    \--- Preview of the sub file

To use:

Ubuntu
Make sure you have python installed. Also you need the python-cheetah package:
 * sudo apt-get install python-cheetah
 * Download the zip file from our download section
 * Unzip the file, change to the directory where AutoSub.py is located
 * Start the script: "python AutoSub.py"
 * A webbrowser should now open
 * Go to the config page, check the settings, make sure you set atleast: path 
(Should point to the location where AutoSub.py is located. Seriespath (Should point to the root of your series folder)
 * Shutdown AutoSub and start it again
Enjoy your subtitles!

Requirements for running AutoSub:
- Install Cheetah : https://pypi.python.org/pypi/Cheetah/2.4.4
- Python2.7

For Synology users use python from the SynoCommunity this has cheetah already included

You can use a version lower than python2.7 but as an additional dependency, you have to install
the python html5lib module: https://pypi.python.org/pypi/html5lib/1.0b3




