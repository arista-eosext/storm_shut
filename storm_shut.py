#!/usr/bin/env python

import re, time, os, sys, Logging
from os import stat
from jsonrpclib import Server
from os.path import abspath
from stat import ST_SIZE
from threading import Timer
import argparse

# Accept argument to define time in munutes before interface re-acvtivates (0 - default, 24hr max)
parser = argparse.ArgumentParser()
parser.add_argument("hold_down_timer", type=int, help="Hold-down timer to re-enable interface. \
        Value = 0 - 1440 minutes. Default = 0 (Never enable)", default=0, nargs='?')
args = parser.parse_args()
if args.hold_down_timer > 1440:
        parser.error("Out of range, 0 - 1440 minutes (24hrs)")
hold_down = args.hold_down_timer

#print "Hold-down timer = ", hold_down, "minutes"

switch = Server( "http://admin:@127.0.0.1:8080/command-api" )

# What log file to watch 
file = "/var/log/messages"

# What line in the log to match on 
expression = ".*STORMCONTROL_DISCARDS.*"

# Define Log
Logging.logD( id="STORMCONTROL_INT_SHUT",
              severity=Logging.logInfo,
              format="%s",
              explanation="Message to indicate that the script has caught an event",
              recommendedAction=Logging.NO_ACTION_REQUIRED
)

class LogTail:
    def __init__(self, logfile, expression):
        self.expression = expression
        self.logfile = abspath(logfile)
        self.f = open(self.logfile,"r")
        file_len = stat(self.logfile)[ST_SIZE]
        self.f.seek(file_len)
        self.pos = self.f.tell()
    def _reset(self):
        self.f.close()
        self.f = open(self.logfile, "r")
        self.pos = self.f.tell()

# Method to reactivate interface after hold-down timer expiry
    def Hold_down_act(self, sc_int):
        commands = 'configure', 'interface ' + sc_int, 'no shutdown'
        self.resp = switch.runCmds(1, commands)
        print sc_int + " enabled due to storm control timer expiry"
        Logging.log(STORMCONTROL_INT_SHUT, "Hold-down timer expiry, interface " + sc_int + " reactivated")


# Look for new entries in the log file

    def tail(self):        

        while 1:
            self.pos = self.f.tell()
            line = self.f.readline()
            if not line:
                if stat(self.logfile)[ST_SIZE] < self.pos:
                    self._reset()
                else:
                    time.sleep(1)
                    self.f.seek(self.pos)
            else:

# Look for a matching line

                if re.match(self.expression, line, re.M|re.I):
# Split out each word in the line
                        words = line.split()

# Slice list for Ethernet interface that has active Storm Control Policer
                        sc_int = words[12]              
                        sc_int = sc_int[:-1]
                        Logging.log(STORMCONTROL_INT_SHUT, "Storm control triggered interface " + sc_int + " shutdown")

# Shutdown interface and start timer to re-enable if non-zero value
                        commands = 'configure', 'interface ' + sc_int, 'shutdown'                       
                        resp = switch.runCmds(1, commands)
                        print sc_int + " disabled due to storm control violation"
                        if hold_down >= 1:
                                t = Timer(60.0*hold_down, self.Hold_down_act, [sc_int])
                                t.start()

# Run 
tail = LogTail(file, expression)
tail.tail()
