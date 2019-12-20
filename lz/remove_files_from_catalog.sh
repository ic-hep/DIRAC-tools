#!/usr/bin/env python

# remove entries for LZ files from the dirac file catalogue
# this is an emergency measure to reconcile the file catalog
# with the files on disk if files are lost due to faulty
# hardware
# this script assumes that the files were only present at
# UKI-LT2-IC-HEP-disk
# you have been warned
# take a list of lfns as input

import sys
import uuid
# DIRAC does not work otherwise
from DIRAC.Core.Base import Script
Script.parseCommandLine( ignoreErrors = True )
# end of DIRAC setup

DIRAC_SE_NAME="UKI-LT2-IC-HEP-disk"

from DIRAC.Resources.Catalog.FileCatalog import FileCatalog

def remove_catalog_entry(lfnpath, fc):
 
  dbentry_result = fc.exists(lfnpath)
  if dbentry_result["OK"]:
    # print dbentry_result
    # this is dodgy
    if dbentry_result["Value"]["Successful"][lfnpath] != False:
      # print "DB entry already exists"
      # print dbentry_result["Value"]["Successful"]
      fc.removeFile(lfnpath)
  else:
    # don't know what happened, just print to screen for now
    print result
  return  

def main():
  fd = open(sys.argv[1], "r")

  fc = FileCatalog()


  i = 0

  for line in fd:
    line = line.strip()
    remove_catalog_entry(line,fc)
    i += 1
    if (i%100 == 0):
      print i, line

if __name__ == "__main__":
  main()
  
