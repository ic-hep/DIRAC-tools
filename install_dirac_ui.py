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

UI_PYTHON_VERSION = "27"

UI_VERSION = "v6r15p6"
LCG_BINDINGS = "2015-09-03"


# note: There might be newer/better (though not necessarily both)
# versions of the LCG_BINDINGS available here:
# http://lhcbproject.web.cern.ch/lhcbproject/dist/Dirac_project/lcgBundles/

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


def prerequisites():
  print 'To install this UI please ensure that: '
  print 'a) This is an SL6 compatible machine.'
  print 'b) Your user cert and key are located in $HOME/.globus' 
  print 'c) You are a member of a VO supported by the dirac.gridpp.ac.uk instance of dirac.'
  print 'In case of problems, please email daniela.bauer@imperial.ac.uk'



def install_ui():

  # second thoughts ?
  do_i_want_to_try = ''
  while True:
    userinput = raw_input('Would you like to go ahead and install the UI (y/n) ? : ')
    # for people who just hit 'Enter'
    if len(userinput) > 0:
      first_char_only = userinput[0] # for people who type 'yes' instead of 'y'....
      do_i_want_to_try = first_char_only.lower()
   
    if do_i_want_to_try == 'y':
       break
    elif do_i_want_to_try == 'n':
      print 'Goodbye, maybe next time.'
      sys.exit(1)
    else:  
      print "You must specify y/n, please !"
   

  # I'll need the proxy password later
  proxypasswd = getpass.getpass("Please enter your (grid) proxy password: ") 
  
  # Get VO of user
  user_VO = raw_input('Please state your VO (fully qualified VO name) : ')

  # make a new directory using date and time
  # I refuse to use seconds here ....
  dirac_test_dir = "dirac_ui_"+datetime.datetime.now().strftime("%Y_%b_%d")
  
  # this should only happen if program was quit in anger
  # the main purpose of this function is to annoy Simon :-)
  if os.path.exists(dirac_test_dir):
    print 'Trying to make dir %s, but it exists already.' % dirac_test_dir
    print 'Did you quit in anger previously ?'
    print 'Please delete the directory and try again.'
    sys.exit(0)


  print 'Creating test dir: %s' % dirac_test_dir 
  os.mkdir(dirac_test_dir)
  os.chdir(dirac_test_dir)
  # log the ui versions used in a convenient place
  uiverfile = open('ui_versions.txt', 'w')
  uiverfile.write('UI_VERSION: '+UI_VERSION+'\n')
  uiverfile.write('UI_PYTHON_VERSION: '+UI_PYTHON_VERSION+'\n')
  uiverfile.write('LCG_BINDINGS: '+LCG_BINDINGS+'\n')
  uiverfile.close()
  

  # retrieve install executable
  wget_cmd = ["wget", "-np", "-O", "dirac-install", "http://lhcbproject.web.cern.ch/lhcbproject/dist/Dirac_project/dirac-install"]
  simple_run(wget_cmd)
  os.chmod("dirac-install", 0744)

  pwd = os.getcwd()
  install_command_string = pwd + "/dirac-install" # needs full path

  # install UI
  inst_cmd =  [install_command_string, "-r", UI_VERSION , "-i", UI_PYTHON_VERSION, "-g", LCG_BINDINGS]
  simple_run(inst_cmd) 


  # from Simon
  # We have to "source" the bashrc now.
  # This is a bit of a hassle to do as we're in python not bash.
  # There are some pickle tricks to do this, but python changes on source bashrc.
  # We'll do it the slightly more tedious way:
  source_cmd = [ "/bin/bash", "-c", "source bashrc && env -0" ]
  proc = Popen(source_cmd, stdout=PIPE)
  vars_out, _ = proc.communicate()
  if proc.returncode:
    print "ERROR: Failed to source bashrc. Check output above."
    sys.exit(0)
  # Get the vars from the output
  for var in vars_out.split("\0"):
    var_name, _, var_value = var.partition("=")
    os.environ[var_name] = var_value

  # Make a generic proxy to be able to download the config files  
  proxy_child = pexpect.spawn('dirac-proxy-init -x')
  proxy_child.expect ('password:')
  proxy_child.sendline (proxypasswd)

  # configure UI
  configure_ui_cmd = ["dirac-configure", "-F", "-S", "GridPP", "-C", "dips://dirac01.grid.hep.ph.ic.ac.uk:9135/Configuration/Server", "-I"]

  simple_run(configure_ui_cmd)

  # now all should be well, so make a VO specific proxy
  vo_user_string = 'dirac-proxy-init -g ' + user_VO + '_user' + ' -M'
  # proxy_child = pexpect.spawn('dirac-proxy-init -g comet.j-parc.jp_user -M')
  proxy_child = pexpect.spawn(vo_user_string)
  proxy_child.expect ('password:')
  proxy_child.sendline (proxypasswd)

  # send a status message - I should probably check for errors along the way
  print "UI installed and configured."
  print "Current proxy is: " 
  
  simple_run(["dirac-proxy-info"])
  print "\nTo use this UI, please do:"
  print "cd "+ dirac_test_dir
  print "source bashrc"
  print "If you need a proxy:"
  # print "dirac-proxy-init -g comet.j-parc.jp_user -M"
  print vo_user_string

# now actually do something
prerequisites()
install_ui()

