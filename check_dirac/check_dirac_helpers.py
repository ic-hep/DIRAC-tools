#!/usr/bin/env python3
"""
Helper functions for the dirac test module.
Nothing to see here.
"""
import os
import sys
# import shutil
# import string
import re
from subprocess import Popen, PIPE

# dirac-in-a-box puts these in a dictionary, let's go with that
PARAMETERS = {"USERCERT": os.path.expanduser("~/.globus/usercert.pem"),
              "USERKEY": os.path.expanduser("~/.globus/userkey.pem"),}


# blatantly stolen from Simon
def simple_run(cmd, warn_run=False, shell=False):
  """ Runs a command and exits on error.
  Command output gets sent to the console.
  """
  proc = Popen(cmd, shell=shell)
  proc.wait()
  if proc.returncode:
    print("ERROR: %s failed. Check output above." % cmd[0])
    if warn_run:
      print("NOTE: Processes may have been left running at this point.")
    print("Full Cmd: %s" % str(cmd))
    sys.exit(0)

def complex_run(cmd, warn_run=False, shell=False):
  """ Runs a command and exits on error.
  Command output is returned.
  """
  proc = Popen(cmd, shell=shell, stdout=PIPE, stderr=PIPE)
  allout, _ = proc.communicate() # returns tuple, ignores stderr
  if proc.returncode:
    print("ERROR: %s failed. Check output above." % cmd[0])
    if warn_run:
      print("NOTE: Processes may have been left running at this point.")
    print("Full Cmd: %s" % str(cmd))
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
      print(f"ERROR: Can't access the {key_name} at {key_path}.")
      print("This should be accessible by the current user.")
      sys.exit(0)

  # Check 2: Is this SL7, 8 or 9 (other distibutions may work)
  if not os.path.isfile("/etc/redhat-release"):
    print("Cannot find /etc/redhat-release.")
    print("Script EL7, please.")
    sys.exit(0)
  else:
    os_ver = os.uname()[2]
    supported_os = [".el7", ".el8", ".el9"]
    if not any(x in os_ver for x in supported_os):
      print("This doesn't look like an EL7/8/9 node. This will probably NOT WORK.")
      print("Press <ENTER> if you're sure.")
      input()

  # Check 3: Cannot setup a new DIRAC UI on top of an old one
  if "DIRAC" in os.environ:
    print(os.environ["DIRAC"])
    print("You seem to have already have setup a DIRAC UI.")
    print("Please run this script in a clean shell.")
    print("Otherwise bad things(TM) might happen.")
    sys.exit(0)

  # Check 4: Cannot setup a DIRAC UI on top of a grid UI either
  if "GLITE_LOCATION" in os.environ:
    print(os.environ["GLITE_LOCATION"])
    print("You seem to have already have setup a Grid UI.")
    print("Please run this script in a clean shell.")
    print("Otherwise bad things(TM) might happen.")
    sys.exit(0)


def extract_externals_version(logfile):
  """for old releases that use dirac externals"""
  externals_version = "Unknown"
  with open(logfile, encoding='utf-8') as uilogfile:
    for line in uilogfile:
      res = re.search(r"Externals", line)
      if res:
        words = line.split(' ')
        externals_version = words[10]
  return externals_version


def extract_diracos_version(logfile):
  """PY2 ONLY: keep record of which diracos version was installed"""
  diracos_version = "Unknown"
  with open(logfile, encoding='utf-8') as uilogfile:
    for line in uilogfile:
      # res = re.search(r"diracos.web.cern.ch/diracos/releases", line)
      res = re.search(r"Using CVMFS copy of diracos", line)
      if res:
        print(line)
        diracos_version = line[-13:-8]
  return diracos_version


def jobid_to_file(command_log, outfile):
  """extract jobid and write to file"""
  jobid_start = command_log.decode().find("JobID =")
  if jobid_start != -1:
    outfile.write(command_log[jobid_start:].decode())
  else:
    outfile.write("No job submitted!")
    outfile.write("\n")
