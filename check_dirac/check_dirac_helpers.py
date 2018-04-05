#!/usr/bin/python
"""
Helper functions for the dirac test module.
Nothing to see here.
"""
import os
import sys
import shutil
import string
from subprocess import Popen, PIPE

# dirac-in-a-box puts these in a dictionary, let's go with that
PARAMETERS = { "USERCERT": os.path.expanduser("~/.globus/usercert.pem"),
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
  (e.g. usercert and release version)
  """
  # Check 1: Is there a usercert ?
  for key_name in ("USERCERT", "USERKEY"):
    key_path = PARAMETERS[key_name]
    if not os.access(key_path, os.R_OK):
      print "ERROR: Can't access the %s at %s." % (key_name, key_path)
      print "This should be accessible by the current user."
      sys.exit(0)

 # Check 2: Is this SL6 or SL7 similar ?
  if not os.path.isfile("/etc/redhat-release"):
    print "Cannot find /etc/redhat-release."
    print "Script needs EL6 or EL7, please."
    sys.exit(0)
  else:
    # But of course Simon's is better
    if not ".el6." in os.uname()[2] and not  ".el7." in os.uname()[2]:
      print "This doesn't look like an EL6 or EL7 node. This will probably NOT WORK."
      print "Press <ENTER> if you're sure."
      raw_input()
    #I liked my version, pah
    #relfile = open("/etc/redhat-release", "r")
    #content = relfile.read()
    #relstring = "release "
    #start_loc = content.find(relstring)
    #releaseversion = content[(start_loc + 8):(start_loc + 9)]
    #try:
    #  releaseversion =  int(releaseversion)
    #except ValueError:
    #  print "Cannot determine release version."
    #if releaseversion != 6 :
    #  print "This does not seem to be an EL6 machine."
    #  print "Proceed at your own risk, but it will probably NOT WORK."


  # Check 3: Cannot setup a new DIRAC UI on top of an old one
  if "DIRAC" in os.environ:
    print os.environ["DIRAC"]
    print "You seem to have already have setup a DIRAC UI."
    print "Please run this script in a clean shell."
    print "Otherwise bad things(TM) might happen."
    sys.exit(0)

  # Check 4: Cannot setup a DIRAC UI on top of a grid UI either
  if "GLITE_LOCATION" in os.environ:
    print os.environ["GLITE_LOCATION"]
    print "You seem to have already have setup a Grid UI."
    print "Please run this script in a clean shell."
    print "Otherwise bad things(TM) might happen."
    sys.exit(0)


