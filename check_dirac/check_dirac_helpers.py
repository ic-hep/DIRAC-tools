#!/usr/bin/python

import os
import sys
import shutil
import string
import random
import getpass
import datetime
import time
import getpass
import pexpect
from subprocess import Popen, PIPE

# dirac-in-a-box puts these in a dictionary, let's go with that
PARAMETERS={ "USERCERT": os.path.expanduser("~/.globus/usercert.pem"),
             "USERKEY": os.path.expanduser("~/.globus/userkey.pem"),
             }


# blatantly stolen from Simon
def simple_run(cmd, warn_run=False, shell=False):
  """ Runs a command and exits on error.
  Command output gets sent to the console.
  """
  proc = Popen(cmd, shell=shell)
  proc.wait()
  if proc.returncode:
    print "ERROR: %s failed. Check output above." % cmd[0]
    if warn_run:
      print "NOTE: Processes may have been left running at this point."
    print "Full Cmd: %s" % str(cmd)
    sys.exit(0)

def complex_run(cmd, warn_run=False, shell=False):
  """ Runs a command and exits on error.
  Command output is returned.
  """
  proc = Popen(cmd, shell=shell, stdout=PIPE, stderr=PIPE)
  allout, _ = proc.communicate() # returns tuple, ignores stderr
  if proc.returncode:
    print "ERROR: %s failed. Check output above." % cmd[0]
    if warn_run:
      print "NOTE: Processes may have been left running at this point."
    print "Full Cmd: %s" % str(cmd)
    sys.exit(0)
  return allout  


def check_prerequisites():
  """ Checks prerequisites for check_dirac script 
  """
  # I'll probably add some more later
  for key_name in ("USERCERT", "USERKEY"):
    key_path = PARAMETERS[key_name]
    if not os.access(key_path, os.R_OK):
      print "ERROR: Can't access the %s at %s." % (key_name, key_path)
      print "This should be accessible by the current user."
      sys.exit(0)


