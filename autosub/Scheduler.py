#
#
# The Autosub Scheduler module
#

from time import time,sleep
import threading
import os
import traceback
import autosub

class Scheduler:
    def __init__(self, command,runnow, name):      
        self.command = command
        self.name = name
        self.thread = threading.Thread(None, self.runcommand, self.name)
        self.stop = False
        if runnow:
            try:
                self.command.run()
                self.lastrun = time()
                self.runnow = False
            except:
                print traceback.format_exc()
                os._exit(1)
            
    def runcommand(self):
        while True:
            ellapsed = time() - self.lastrun
            if (ellapsed > autosub.SEARCHINTERVAL and ellapsed > 21600):
                try:
                    print 'scheduler run:', time()
                    self.command.run()
                    self.lastrun = time() 
                except:
                    print traceback.format_exc()
                    os._exit(1)
            
            if self.runnow:
                try:
                    self.command.run()
                    self.lastrun = time() 
                    self.runnow = False
                except:
                    print traceback.format_exc()
                    os._exit(1)
            if self.stop:
                break
            sleep(1)
