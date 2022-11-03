#!/usr/bin/env python3
"""
installs and configures a fresh DIRAC UI
"""
import os
import sys
import getpass
import datetime
import time
import re
import pexpect
# apparently obsolete, haven't found a replacement yet
# import platform
from subprocess import Popen, PIPE
from check_dirac_helpers import simple_run, complex_run
from check_dirac_helpers import extract_diracos_version

# version format for PY2 is "v7r3p24", for PY3 use "7.3.24"
# (including for choosing cvmfs UI)
UI_VERSION = "7.3.26"
# UI_VERSION = "v7r3p26"

PARAMETERS = {"USERCERT": os.path.expanduser("~/.globus/usercert.pem"),
              "USERKEY": os.path.expanduser("~/.globus/userkey.pem"),}

def setup_test_dir(user_VO, install_type):
  """
  make a new directory (using date and time) for the tests to run in
  """
  dirac_test_dir = datetime.datetime.now().strftime("%Y_%b_%d_%H%M")
  dirac_test_dir = dirac_test_dir+'_'+str(user_VO)
  # currently only SL7... replace with PY2/PY3 distinction
  # el = platform.linux_distribution()[1].split('.')[0]
  # dirac_test_dir = dirac_test_dir+'_EL'+ str(el)

  py_ver = "py3"
  if UI_VERSION.startswith('v'):
    py_ver = "py2"
  # ignore python versions if using cvmfs install
  if install_type == "cvmfs":
    py_ver = "cvmfs"
  dirac_test_dir = dirac_test_dir + '_' + py_ver


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


def install_local_ui(user_VO, proxypasswd):
  """
  installs local UI
  """
  # at this point we are in the newly created directory
  pwd = os.getcwd()
  # PY2
  if UI_VERSION.startswith('v'):
    # retrieve install executable
    wget_cmd = ["wget", "-np", "-O", "dirac-install",
                "http://raw.githubusercontent.com/DIRACGrid/management/master/dirac-install.py"]
    simple_run(wget_cmd)

    os.chmod("dirac-install", 0o744)
    install_command_string = pwd + "/dirac-install" # needs full path

    # install UI
    inst_cmd = "%s -r %s | tee install.log" %(install_command_string, UI_VERSION)
    simple_run(inst_cmd, shell=True) # to capture output

    # log ui and related versions in a convenient place
    uiverfile = open('ui_versions.txt', 'w')
    uiverfile.write('UI_VERSION: '+UI_VERSION+'\n')
    diracos_version = extract_diracos_version("install.log")
    uiverfile.write('DIRACOS: '+diracos_version+'\n')
    uiverfile.close()

    # We have to "source" the bashrc now.
    # This is a bit of a hassle to do as we're in python not bash.
    source_cmd = ["/bin/bash", "-c", "source bashrc && env -0"]
    proc = Popen(source_cmd, stdout=PIPE)
    vars_out, _ = proc.communicate()
    if proc.returncode:
      print("ERROR: Failed to source bashrc. Check output above.")
      sys.exit(0)
    # Get the vars from the output
    for var in vars_out.decode().split("\0"):
      var_name, _, var_value = var.partition("=")
      # var_name can be empty
      if var_name:
        os.environ[var_name] = var_value

  else:
    curl_cmd = ["curl", "-LO", "https://github.com/DIRACGrid/DIRACOS2/releases/latest/download/DIRACOS-Linux-x86_64.sh"]
    simple_run(curl_cmd)
    os.chmod("DIRACOS-Linux-x86_64.sh", 0o744)

    # install UI
    inst_cmd = "bash DIRACOS-Linux-x86_64.sh | tee install.log"
    simple_run(inst_cmd, shell=True) # to capture output

    diracos_version = "UNKNOWN"
    diracos_ver_filename = pwd + "/diracos/.diracos_version"
    try:
      diracos_ver_file = open(diracos_ver_filename, "r")
    except OSError as stupiderror:
      print('Problem opening file: ', stupiderror)
    diracos_version = diracos_ver_file.read().strip()

    os.remove(pwd+"/DIRACOS-Linux-x86_64.sh")
    # log ui and related versions in a convenient place
    uiverfile = open('ui_versions.txt', 'w')
    uiverfile.write('UI_VERSION: '+UI_VERSION+'\n')
    uiverfile.write('DIRACOS: '+diracos_version+'\n')
    uiverfile.close()

    # now 'activate' the env
    print("Trying to activate the env")
    source_cmd = ["/bin/bash", "-c", "source diracos/diracosrc && env -0"]
    proc = Popen(source_cmd, stdout=PIPE)
    vars_out, _ = proc.communicate()
    if proc.returncode:
      print("ERROR: Failed to source diracos/diracosrc. Check output above.")
      sys.exit(0)
    for var in vars_out.decode().split("\0"):
      var_name, _, var_value = var.partition("=")
      if var_name:
        os.environ[var_name] = var_value

    # pip install
    pipversion = "DIRAC == %s" %UI_VERSION
    print("Attempting pip install %s" %pipversion)
    pip_cmd = ["pip", "install", pipversion]
    simple_run(pip_cmd)


  # Make a generic proxy to be able to download the config files
  proxy_child = pexpect.spawn('dirac-proxy-init -x -N')
  proxy_child.expect('password:')
  proxy_child.sendline(proxypasswd)

  # configure UI
  configure_ui_cmd = ["dirac-configure", "-F", "-S", "GridPP",
                      "-C", "dips://dirac01.grid.hep.ph.ic.ac.uk:9135/Configuration/Server", "-I"]

  simple_run(configure_ui_cmd)


  # now all should be well, so make a %s VO proxy
  make_proxy_string = 'dirac-proxy-init -g %s_user' % user_VO
  # print  make_proxy_string
  proxy_child = pexpect.spawn(make_proxy_string)
  # proxy_child = pexpect.spawn('dirac-proxy-init -g gridpp_user -M')
  proxy_child.expect('password:')
  proxy_child.sendline(proxypasswd)
  # the next line is magic, I used to know what it is doing.
  proxy_child.read()

  # check if it's a voms-proxy and if it's not, try again. Once.
  proxycheck = complex_run(["dirac-proxy-info"])

  match = re.search(r'username\s+:\s+(.+)', proxycheck.decode())
  if not match:
    print('Cannot determine dirac user name. Something has gone terribly wrong.')
    sys.exit(0)

  if proxycheck.decode().find("VOMS fqan") < 0:
    print('This proxy does not seem to contain a VOMS fqan, try again. Once')
    time.sleep(3)
    proxy_child = pexpect.spawn(make_proxy_string)
    proxy_child.expect('password:')
    proxy_child.sendline(proxypasswd)

  proxycheck2 = complex_run(["dirac-proxy-info"])
  if proxycheck2.decode().find("VOMS fqan") < 0:
    print('This proxy still does not seem to contain a VOMS fqan. Giving up.')
    sys.exit(0)

  # send a status message - I should probably check for errors along the way
  print('UI installed and configured.')
  print('Current proxy is: ')
  simple_run(["dirac-proxy-info"])


def setup_voms_proxy(user_VO, proxypasswd):
  """
  This is the last step. At this point the UI is installed and the env activated.
  """

  make_proxy_string = 'dirac-proxy-init -r -g %s_user -U' % user_VO
  proxy_child = pexpect.spawn(make_proxy_string)
  proxy_child.expect('password:')
  proxy_child.sendline(proxypasswd)
  # debugging: try to give a hint of what is going on
  print(proxy_child.read().decode())
  # check if it's a voms-proxy and if it's not, try again. Once.
  proxycheck = complex_run(["dirac-proxy-info"])

  match = re.search(r'username\s+:\s+(.+)', proxycheck.decode())
  if not match:
    print('Cannot determine dirac user name. Something has gone terribly wrong.')
    sys.exit(0)

  if proxycheck.decode().find("VOMS fqan") < 0:
    print('This proxy does not seem to contain a VOMS fqan, try again. Once')
    time.sleep(3)
    proxy_child = pexpect.spawn(make_proxy_string)
    proxy_child.expect('password:')
    proxy_child.sendline(proxypasswd)

  proxycheck2 = complex_run(["dirac-proxy-info"])
  if proxycheck2.decode().find("VOMS fqan") < 0:
    print('This proxy still does not seem to contain a VOMS fqan. Giving up.')
    sys.exit(0)


def setup_ui(user_VO, install_type):
  """
  Main function to setup a UI.
  Result should be a working UI and a voms proxy
  """
  proxypasswd = getpass.getpass("Please enter your proxy password: ")
  if proxypasswd == "":
    print("Password seems to be empty, that won't work.")
    sys.exit(0)
  else:
    print("Read password of length %d" % (len(proxypasswd)))

  setup_test_dir(user_VO, install_type)

  source_cmd = []
  if install_type == "local":
    install_local_ui(user_VO, proxypasswd)
    # this is python2
    if os.path.isfile('bashrc'):
      source_cmd = ["/bin/bash", "-c", "source bashrc && env -0"]
    else:
      # python3
      source_cmd = ["/bin/bash", "-c", "source diracos/diracosrc && env -0"]
  else:
    # python2 tests would have to be done by hand
    print("Activating python3 DIRAC env from cvmfs")
    source_cmd = ["/bin/bash", "-c", "source /cvmfs/dirac.egi.eu/dirac/bashrc_gridpp && env -0"]

  # source the environment prior to invoking any DIRAC commands
  proc = Popen(source_cmd, stdout=PIPE)
  vars_out, _ = proc.communicate()
  if proc.returncode:
    print("ERROR: Failed to source diracos/diracosrc and/or bashrc. Check output above.")
    sys.exit(0)
  for var in vars_out.decode().split("\0"):
    var_name, _, var_value = var.partition("=")
    if var_name:
      os.environ[var_name] = var_value

  # setting up a VO proxy
  setup_voms_proxy(user_VO, proxypasswd)

  print('UI installed and configured.')
  print('Current proxy is: ')
  simple_run(["dirac-proxy-info"])
