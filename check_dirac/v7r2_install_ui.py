#!/usr/bin/env python
"""
installs and configures a fresh DIRAC UI
"""
from __future__ import print_function

import os
import sys
import getpass
import datetime
import time
import re
# apparently obsolete, haven't found a replacement yet
import platform
import pexpect
from check_dirac_helpers import simple_run, complex_run
from check_dirac_helpers import extract_externals_version
from check_dirac_helpers import extract_diracos_version
from subprocess import Popen, PIPE


UI_PYTHON_VERSION = "27"

UI_VERSION = "v7r2p28"
# note that a v7r1 UI does not work against a v6r22 server
# LCG_BINDINGS is ignored for any v7 version of DIRAC
LCG_BINDINGS = "v14r1"

# dirac-in-a-box puts these in a dictionary, let's go with that
PARAMETERS = {"USERCERT": os.path.expanduser("~/.globus/usercert.pem"),
              "USERKEY": os.path.expanduser("~/.globus/userkey.pem"),}


def install_ui():
  """installs UI locally, as opposed to using the cvmfs UI"""

  wget_cmd = ["wget", "-np", "-O", "dirac-install",
              "https://raw.githubusercontent.com/DIRACGrid/management/master/dirac-install.py"]
  simple_run(wget_cmd)

  os.chmod("dirac-install", 0744)

  pwd = os.getcwd()
  install_command_string = pwd + "/dirac-install" # needs full path
  # install UI
  # inst_cmd = [install_command_string, "-r", UI_VERSION,
  #            "-i", UI_PYTHON_VERSION, "-g", LCG_BINDINGS]
  if UI_VERSION[0:2] == "v6":
    inst_cmd = "%s -r %s -i %s -g %s | tee install.log" %(install_command_string, UI_VERSION, UI_PYTHON_VERSION, LCG_BINDINGS)
  else:
    inst_cmd = "%s -r %s | tee install.log" %(install_command_string, UI_VERSION)
  simple_run(inst_cmd, shell=True) # to capture output
  # log ui and related versions in a convenient place
  uiverfile = open('ui_versions.txt', 'w')
  uiverfile.write('UI_VERSION: '+UI_VERSION+'\n')
  uiverfile.write('UI_PYTHON_VERSION: '+UI_PYTHON_VERSION+'\n')
  if UI_VERSION[0:2] == "v6":
    uiverfile.write('LCG_BINDINGS: '+LCG_BINDINGS+'\n')
    ext_version = extract_externals_version("install.log")
    uiverfile = open('ui_versions.txt', 'a')
    uiverfile.write(ext_version)
  else:
    diracos_version = extract_diracos_version("install.log")
    uiverfile = open('ui_versions.txt', 'a')
    uiverfile.write('DIRACOS: '+diracos_version+'\n')
    uiverfile.close()
  # that's currently a dummy return
  return 0

def setup_ui():
  """
  installs and configures a fresh DIRAC UI (VO specific)
  """
  # pick which VO I want to test, default gridpp
  print("Which VO do you want to test (default: gridpp) ?")
  user_VO = raw_input("Your choices are: gridpp, lz, lsst, solidexperiment.org, skatelescope.eu: ") \
      or "gridpp"
  if user_VO not in ["gridpp", "lz", "lsst", "solidexperiment.org", "skatelescope.eu"]:
    print("Testing for %s VO is not supported." % user_VO)
    sys.exit(0)

  install_type = raw_input("Install new local UI or use cvmfs (default: local)? Please enter: 'local'/'cvmfs'. ") or "local"
  if install_type not in ["local", "cvmfs"]:
    print("WARNING: install_type %s not known, proceeding with local install." % install_type)

  # I'll need the proxy password later
  proxypasswd = getpass.getpass("Please enter your proxy password: ")
  if proxypasswd == "":
    print("Password seems to be empty, that won't work.")
    sys.exit(0)
  else:
    print("Read password of length %d" % (len(proxypasswd)))

  # make a new directory using date and time
  # I refuse to use seconds here ....
  dirac_test_dir = datetime.datetime.now().strftime("%Y_%b_%d_%H%M")
  dirac_test_dir = dirac_test_dir + '_' + str(user_VO)
  el = platform.linux_distribution()[1].split('.')[0]
  if (int(el) not in [6, 7]):
    print("This does not look lile EL7, here be dragons (HBD ;-)")
    dirac_test_dir = dirac_test_dir+'_HBD'
  else:
    dirac_test_dir = dirac_test_dir+'_EL'+ str(el)

  # this should only happen if program was quit in anger
  # the main purpose of this function is to annoy Simon :-)
  if os.path.exists(dirac_test_dir):
    print('Trying to make dir %s, but it exists already.' % dirac_test_dir)
    print('Did you quit in anger previously ?')
    print('Please be patient ....')
    time.sleep(30)
    print('Your call is important to us. Please hold ....')
    time.sleep(31)
    dirac_test_dir = datetime.datetime.now().strftime("%Y_%b_%d_%H%M")


  print('\nCreating test dir: %s' % dirac_test_dir)
  os.mkdir(dirac_test_dir)
  os.chdir(dirac_test_dir)

  # retrieve and install executable
  if install_type == "local":
    ui = install_ui()
  else:
    print("Using cvmfs UI, nothing to install.")

  # from Simon
  # We have to "source" the bashrc now.
  # This is a bit of a hassle to do as we're in python not bash.
  # There are some pickle tricks to do this,
  # but python changes on source bashrc.
  source_cmd = ["/bin/bash", "-c", "source bashrc && env -0"]
  if install_type == "cvmfs":
    source_cmd = ["/bin/bash", "-c", "source /cvmfs/dirac.egi.eu/dirac/bashrc_gridpp && env -0"]

  proc = Popen(source_cmd, stdout=PIPE)
  vars_out, _ = proc.communicate()
  if proc.returncode:
    print("ERROR: Failed to source bashrc. Check output above.")
    sys.exit(0)
  # Get the vars from the output
  for var in vars_out.split("\0"):
    var_name, _, var_value = var.partition("=")
    os.environ[var_name] = var_value

  # Make a generic proxy to be able to download the config files
  proxy_child = pexpect.spawn('dirac-proxy-init -r -x')
  proxy_child.expect('password:')
  proxy_child.sendline(proxypasswd)
  print(proxy_child.before)

  # configure UI
  # sorry pylint, no shortcuts
  if install_type == "local":
    configure_ui_cmd = ["dirac-configure", "-F", "-S", "GridPP",
                        "-C", "dips://dirac01.grid.hep.ph.ic.ac.uk:9135/Configuration/Server", "-I"]
    simple_run(configure_ui_cmd)

  # now all should be well, so make a %s VO proxy
  make_proxy_string = 'dirac-proxy-init -r -g %s_user -M' % user_VO
  # print  make_proxy_string
  proxy_child = pexpect.spawn(make_proxy_string)
  # proxy_child = pexpect.spawn('dirac-proxy-init -g gridpp_user -M')
  proxy_child.expect('password:')
  proxy_child.sendline(proxypasswd)
  # try to give a hint of what is going on
  print(proxy_child.read())

  # check if it's a voms-proxy and if it's not, try again. Once.
  proxycheck = complex_run(["dirac-proxy-info"])

  match = re.search(r'username\s+:\s+(.+)', proxycheck)
  if not match:
    print('Cannot determine dirac user name. Something has gone terribly wrong.')
    sys.exit(0)

  if proxycheck.find("VOMS fqan") < 0:
    print('This proxy does not seem to contain a VOMS fqan, try again. Once')
    time.sleep(3)
    proxy_child = pexpect.spawn(make_proxy_string)
    proxy_child.expect('password:')
    proxy_child.sendline(proxypasswd)

  proxycheck2 = complex_run(["dirac-proxy-info"])
  if proxycheck2.find("VOMS fqan") < 0:
    print('This proxy still does not seem to contain a VOMS fqan. Giving up.')
    sys.exit(0)

  # send a status message - I should probably check for errors along the way
  print("UI installed and configured.")
  print("Current proxy is: ")

  simple_run(["dirac-proxy-info"])

  # needed elsewhere
  return user_VO
