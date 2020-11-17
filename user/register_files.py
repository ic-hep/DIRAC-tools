#!/usr/bin/env python
"""
USE WITH CARE.
Registers files that are already on a storage element in DIRAC.
The user needs to provide an input file of the following format:
PFN checksum size (as e.g. produced by extract_file_data.py)
example:
srm://gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/gridpp/gridpp/user/d/daniela.bauer/small.text.file.txt e5d214d7 3445
*and*
the DIRAC name of the SE (e.g. UKI-LT2-IC-HEP-disk)
*and*
the VO the files are meant to be registered under.
The PFN must be DIRAC File catalogue compliant:
protocol (here: srm://)
storage element name (here: gfe02.grid.hep.ph.ic.ac.uk)
VO path as registered in the DIRAC Configuration (please double check)
(here: /pnfs/hep.ph.ic.ac.uk/data/gridpp/)
and LFN that starts with the VO name (here /gridpp) and only contains that VO name once.
(note that in the above PFN the first 'gridpp' is part of the  VOPath, not the LFN).
Requires a DIRAC UI and a valid proxy of the VO the files are meant to be registered under.
"""

from __future__ import print_function
import sys
import uuid
from DIRAC import gLogger, S_OK
from DIRAC.Core.Base import Script
from DIRAC.Interfaces.API.Dirac import Dirac


from DIRAC.Resources.Catalog.FileCatalog import FileCatalog


class Params(object):
  """
  handles all parameters for the register_existing_files script
  """

  def __init__(self):
    """
    creates an (empty) default set of parameters
    """
    self.vo = ''
    self.se = []
    self.sanity_check = True

  def addVO(self, voname):
    """
    VO to be used for registering the files
    """
    self.vo = voname
    return S_OK()

  def addSE(self, sename):
    """
    DIRAC name of the storage element where files are located
    """
    self.se.append(sename)
    return S_OK()

  # args is a dummy argument, but needed
  def turn_off_sanity_check(self, args):
    """ use at your own risk """
    self.sanity_check = False

  def registerCLISwitches(self):
    """
    add options to dirac option parser
    """
    Script.setUsageMessage('Script to register existing files in the DIRAC File Catalogue.  \n \
    Usage: ./register_existing_files.py -v [voname] -e [sename] inputfile')

    # note the magic : and =
    # apparently short switch 'c' and 's' already defined, maybe just not use short switches at all ?
    # ':' means only one parameter allowed
    Script.registerSwitch("v:", "vo=", "VO name of VO that owns the files", self.addVO)
    Script.registerSwitch("e:", "se=", "Storage element the files reside on", self.addSE)
    Script.registerSwitch("n", "nosanitycheck", "disable sanity check", self.turn_off_sanity_check)

# options class stops here

def is_file_already_registered(dirac, lfn, se):
  """0 = not registered, 1 = registered, 2 = problem determining status"""
  result = dirac.getReplicas(lfn)
  # print(result)
  if not result['OK']:
    # this occasionally fails when the catalog is busy
    print("Warning: getReplicas failed, sleeping 60 s and then trying one more time.")
    from time import sleep
    time.sleep(60)
    result = dirac.getReplicas(lfn)
    if not result['OK']:
      print('ERROR determining status of %s: %s' %(lfn, result['Message']))
      return 2
  # Possible outputs
  # {'OK': True, 'Value': {'Successful': {'/gridpp/user/daniela.bauer/repregtest.dirac00.1496070514.txt':
  #      {'UKI-LT2-IC-HEP-disk': '/gridpp/user/daniela.bauer/repregtest.dirac00.1496070514.txt',
  #        'UKI-LT2-QMUL-disk': '/gridpp/user/daniela.bauer/repregtest.dirac00.1496070514.txt'}}, 'Failed': {}}}
  # {'OK': True, 'Value': {'Successful': {}, 'Failed': {'/gridpp/user/daniela.bauer/epregtest.dirac00.1496070514.txt':
  #                                                     'No such file or directory'}}}
  if lfn not in result['Value']['Successful']:
    return 0
  if se not in result['Value']['Successful'][lfn]:
    return 0
  return 1


def determine_lfn(pfn, vo):
  """determines the LFN from a PFN by looking for the first instance of /vo/ starting
  at the end of the PFN"""
  search_string = '/'+vo+'/'
  lfn = 'ERROR: No LFN found'
  isOK = False
  start_index = pfn.rfind(search_string)
  if start_index != -1:
    start_index = pfn.rfind(search_string)
    lfn = pfn[start_index:]
    isOK = True
  return (isOK, lfn)


def sanity_check(testpfn, vo):
  """Asks the user to double check the first LFN to avoid everything going terribly wrong from the start"""
  result = determine_lfn(testpfn, vo)
  if not result[0]:
    print("Could not determine LFN from PFN %s" %testpfn)
    print("Sanity check failed, cannot proceed.")
    return False

  print("Input PFN: %s" %testpfn)
  print("Please confirm that this LFN looks sensible to you: %s" %result[1])
  # now I need input from the user, to absolve myself of all responsibility
  decision = raw_input("Please choose: y/n ? ")
  if decision != 'y':
    print("You decided to exit at this point.")
    return False

  return True


def registerfile(pfnpath, checksum, size, vo, se, fc, dirac):
  """finally registers the file"""
  infoDict = {}
  infoDict['PFN'] = pfnpath
  infoDict['Size'] = int(size)
  infoDict['SE'] = se
  infoDict['GUID'] = str(uuid.uuid4())
  infoDict['Checksum'] = checksum
  fileDict = {}
  lfnpath = determine_lfn(pfnpath, vo)

  # this is what I am trying to process
  # a debug flag mit be helpful
  # print(lfnpath[1])
  # print(infoDict)

  if lfnpath[0]:
    fileDict[lfnpath[1]] = infoDict
  else:
    print("Could not determine LFN path: %s" %pfnpath)
    print("Can not register file.")
    return

  # check if file is already registered
  is_reg = is_file_already_registered(dirac, lfnpath[1], se)
  if is_reg == 1:
    # print("File %s is already registered at %s" %(str(lfnpath), se))
    return
  elif is_reg == 2:
    print("Could not determine status of file %s" % str(lfnpath))
  else:
    result = fc.addFile(fileDict)
    if not result["OK"]:
      print("File registration failed (reason below): ")
      print(result)
      return
    if result["Value"]["Failed"]:
      print("File registration failed (reason below): ")
      print(result["Value"])
      return
  return

def main():
  """
  please see notes in the header of this program
  """
  options = Params()
  options.registerCLISwitches()
  Script.parseCommandLine(ignoreErrors=True)
  args = Script.getPositionalArgs()
  if len(args) < 1:
    Script.showHelp()

  if not (options.vo and options.se):
    print("You must set both the VO and the SE for this to work.")
    sys.exit(0)

  # check if the first entry looks OK, hope for the best for the rest
  if options.sanity_check:
    with open(args[0]) as inputFile:
      first_line = (inputFile.readline()).strip()
      testpfn = first_line.split(' ')[0]
      passed = sanity_check(testpfn, options.vo)
      if not passed:
        sys.exit(0)
  else:
    print("Sanity check turned off.\n")


  dirac = Dirac()
  # check if SE is accessible
  if not dirac.checkSEAccess(options.se[0]):
    print("Chosen SE  %s not accessible, please check SE name" %str(options.se[0]))
    sys.exit(0)


  # this is the heavy lifting
  # dirac = Dirac()
  fc = FileCatalog()
  i = 0
  inputFile = open(args[0], "r")
  for line in inputFile:
    line = line.strip()
    # print("Looking at: %s\n" %line)
    pfnpath, checksum, size = line.split(' ')
    if i%100 == 0:
      print(i, pfnpath, checksum, size)
    registerfile(pfnpath, checksum, size, options.vo, options.se[0], fc, dirac)
    i += 1

  inputFile.close()

if __name__ == "__main__":
  main()
