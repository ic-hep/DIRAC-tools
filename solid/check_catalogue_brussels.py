#!/usr/bin/env python

# requires DIRAC UI to be setup and valid proxy
# takes output from listsolid.py as input
# returns a list of files that are on the SE, 
# but not in the catalogue 
# optional: registers any files that are present on the SE
# but missing from the catalogue

import sys
import uuid
import getopt
# DIRAC does not work otherwise
from DIRAC.Core.Base import Script
# Script.parseCommandLine( ignoreErrors = True )
Script.initialize() # this lets me use getopt
# end of DIRAC setup

DIRAC_SE_NAME="BEgrid-ULB-VUB-disk"
# DIRAC_SE_NAME="UKI-LT2-IC-HEP-disk"

from DIRAC.Resources.Catalog.FileCatalog import FileCatalog


def add_catalog_entry(fc, fileDict, logfile):
    result = fc.addFile(fileDict) 
    # TODO: handle the return code as an exception 
    if not result["OK"]:
      logfile.write(result)
      print result
      return
    if result["Value"]["Failed"]:
      logfile.write(result)
      print result["Value"]
    return

def checkfile(pfnpath, checksum, size, fc, logfile, register_missing):
 
  infoDict = {}
  infoDict['PFN'] = pfnpath
  infoDict['Size'] = int(size)
  infoDict['SE'] = DIRAC_SE_NAME
  infoDict['GUID'] = str(uuid.uuid4())
  infoDict['Checksum'] = checksum   
  fileDict = {}
  # this is for BEgrid-ULB-VUB-disk
  lfnpath = pfnpath[38:]
  # this is for UKI-LT2-IC-HEP-disk
  # lfnpath = pfnpath[64:]
  fileDict[lfnpath] = infoDict
  # print lfnpath
  result = fc.getFileSize(fileDict)  # from FileCatalogClient.py
  # print result
  # {'OK': True, 'Value': {'Successful': {'/solidexperiment.org/Data/phase1_BR2/DAQ/days/2017_11_12/RO-data/rundetector_1000138_12Nov17_1544.sbf': 1496472512L}, 'Failed': {}}}

  if not result["OK"]:
    print result
    logfile.write(str(result)+"\n")
    if register_missing:
      add_catalog_entry(fc, fileDict, logfile)
    return
  if result["Value"]["Failed"]:
    print result["Value"]
    logfile.write(str(result["Value"])+"\n")
    if register_missing:
      add_catalog_entry(fc, fileDict, logfile)
    return
  # for bonus points, compare the file sizes
  file_size_from_catalog = result["Value"]["Successful"][str(lfnpath)]
  if int(file_size_from_catalog) != int(size):
    print "SIZE ERROR for %s" %str(lfnpath)
    logfile.write("SIZE ERROR for %s" %str(lfnpath)+"\n")
  return


def usage():
  """Tells you how to use this script. Obvs."""
  print "Usage: ./inputparameters.py -i <inputfile> [-r]"
  print "Options: -h: This help."
  print "Options: -r: Register missing files in the catalogue."

def main():
  """This is where it all starts. And ends."""

  # get all the input parameters
  try:
    opts, args = getopt.getopt(sys.argv[1:], "i:hr", ["inputfile:", "help", "register"]) 
  except getopt.GetoptError as err:
    print str(err)
    sys.exit()

  inputfile = ""
  register_missing = False

  for opt, content in opts:
    # print opt
    if opt in ("-i", "--inputfile"):
      inputfile = str(content)
    elif opt in ("-r", "--register"):
      register_missing = True
      print "Will try to register missing files."
    elif opt in ("-h", "--help"):
      usage()
      sys.exit()
    else:
      print "Unknown Option \"%s\", exiting" % opt
      sys.exit()
  if inputfile == "":
    print "You must specify an input file (-i <inputfile>)"
    sys.exit()
 

 
  fd = open(inputfile, "r")
  fc = FileCatalog()
  # make an output file to log errors (catalogue entries not found, 
  # wrong file size etc)
  errorlog = str(inputfile  + "_failed")
  logfile = open(errorlog, 'w')

  i = 0

  for line in fd:
    line = line.strip()
    pfnpath, checksum, size = line.split(' ')
    if (i%500 == 0):
      print i, pfnpath, checksum, size
    checkfile(pfnpath, checksum, size, fc, logfile, register_missing)
    i += 1
    
  logfile.close()

if __name__ == "__main__":
  main()
  
