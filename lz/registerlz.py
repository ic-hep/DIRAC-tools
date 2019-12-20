#!/usr/bin/env python

# registers LZ files located at UKI-LT2-IC-HEP-disk
# in the dirac file catalogue
# takes output from listlz.py as input
# input format:
# srm://gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/lz/lz/data/MDC3/background/BACCARAT-4.11.0_DER-8.5.13/20180401/lz_201804010002_000172_035741_raw.root 85e30c08 164712434
# requires DIRAC UI to be setup and valid proxy
# if there is an existing entry for an LFN in the catalogue, 
# it removes this entry and readds it
# This script operates under the assumption that the files are stored at
# UKI-LT2-IC-HEP-disk and *only* at UKI-LT2-IC-HEP-disk
# You have been warned.

import sys
import uuid
# DIRAC does not work otherwise
from DIRAC.Core.Base import Script
Script.parseCommandLine( ignoreErrors = True )
# end of DIRAC setup

DIRAC_SE_NAME="UKI-LT2-IC-HEP-disk"

from DIRAC.Resources.Catalog.FileCatalog import FileCatalog

def registerfile(pfnpath, checksum, size, fc):
 
  infoDict = {}
  infoDict['PFN'] = pfnpath
  infoDict['Size'] = int(size)
  infoDict['SE'] = DIRAC_SE_NAME
  infoDict['GUID'] = str(uuid.uuid4())
  infoDict['Checksum'] = checksum   
  fileDict = {}
  lfnpath = pfnpath[61:]
  fileDict[lfnpath] = infoDict
  # if there is an old entry in the database, remove it
  override=True
  dbentry_result = fc.exists(lfnpath)
  print dbentry_result
  if dbentry_result["OK"]:
    # this is dodgy
    if dbentry_result["Value"]["Successful"][lfnpath] != False:
      print "DB entry already exists"
      print dbentry_result["Value"]["Successful"]
      if (override == True):
        fc.removeFile(lfnpath)
  else:
    # don't know what happened, just print to screen for now
    print result

  result = fc.addFile(fileDict) 
  if not result["OK"]:
    print result
    return
  if result["Value"]["Failed"]:
    print result["Value"]
    return

def main():
  fd = open(sys.argv[1], "r")

  fc = FileCatalog()

  print "WARNING: Override of old entries enabled."

  i = 0

  for line in fd:
    line = line.strip()
    pfnpath, checksum, size = line.split(' ')
    if (i%100 == 0):
      print i, pfnpath, checksum, size
    registerfile(pfnpath, checksum, size, fc)
    i += 1
    

if __name__ == "__main__":
  main()
  
