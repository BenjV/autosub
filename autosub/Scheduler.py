#
#
# The Autosub Scheduler module
#

import time
import threading
import os
import traceback
import autosub

class Scheduler:
    def __init__(self, command,runnow, name):      
        self.command = command
        self.name = name
        #self.interval = interval*3600
        self.thread = threading.Thread(None, self.runcommand, self.name)
        self.stop = False
        if runnow:
            try:
                self.command.run()
                self.lastrun = time.time()
                self.runnow = False
            except:
                print traceback.format_exc()
                os._exit(1)
            
    def runcommand(self):
        while True:
            if time.time() - self.lastrun > autosub.SEARCHINTERVAL:
                try:
                    print 'scheduler run'
                    self.command.run()
                    self.lastrun = time.time() 
                except:
                    print traceback.format_exc()
                    os._exit(1)
            
            if self.runnow:
                try:
                    self.command.run()
                    self.lastrun = time.time() 
                    self.runnow = False
                except:
                    print traceback.format_exc()
                    os._exit(1)
            if self.stop:
                break
            time.sleep(1)
