#!/usr/bin/env python

# registers LZ files located at UKI-LT2-IC-HEP-disk
# in the dirac file catalogue
# takes output from listlz.py as input
# requires DIRAC UI to be setup and valid proxy

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
  # print lfnpath
  # return
  # to do: check if file is there
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
  
