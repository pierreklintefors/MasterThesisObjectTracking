from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from datetime import datetime
import sys

import threading
import time


# make this work with Python2 or Python3
if sys.version_info[0] < 3:
    input = raw_input


class SecondCounter(object):
    def __init__(self):
        self.start_time = None

    def start(self):
        self.start_time = datetime.now()

    @property
    def value(self):
        return (datetime.now() - self.start_time).total_seconds()

    def peek(self):
        return self.value

    def finish(self):
        return self.value

    def reset(self):
        self.start_time = datetime.now()

class Counter_tread(threading.Thread):
    '''
    create a thread object that will do the counting in the background
    default interval is 1/1000 of a second
    '''
    def __init__(self, interval=0.001):
        # init the thread
        threading.Thread.__init__(self)
        self.interval = interval  # seconds
        # initial value
        self.value = 0
        # controls the while loop in method run
        self.alive = False

    def run(self):
        '''
        this will run in its own thread via self.start()
        '''
        self.alive = True
        while self.alive:
            time.sleep(self.interval)
            # update count value
            self.value += self.interval

    def peek(self):
        '''
        return the current value
        '''
        return self.value

    def finish(self):
        '''
        close the thread, return final value
        '''
        # stop the while loop in method run
        self.alive = False
        return self.value
