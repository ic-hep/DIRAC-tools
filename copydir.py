#!/usr/bin/env python
"""
Copies a directory from one SE to another and registers the copied files
in the dirac file catalogue
"""
from DIRAC.Core.Base import Script
Script.initialize()

import sys
import os
import getopt

from DIRAC.Core.DISET.RPCClient import RPCClient
from DIRAC.DataManagementSystem.Client.DataManager import DataManager
from DIRAC.Core.Security.ProxyInfo import getProxyInfo


class RecursiveCp(object):
  def __init__(self):
    self.__rpcclient = RPCClient( "DataManagement/FileCatalog" )
    self.__dm = DataManager()
    self.__n_files = 0
    self.__space_copied = 0L

  def search_directory(self, directory_path, source_se, dest_se, dry_run=True):
    """
    finds all files and subdirectories in a directory
    """
    print "Searching directory: %s" % directory_path
    
    dir_content =  self.__rpcclient.listDirectory(directory_path, False)

    if not dir_content["OK"]:
      print "Failed to contact DIRAC server for %s" % directory_path
      return
    
    if directory_path in dir_content['Value']['Failed']:
      print "Could not access %s, maybe it doesn't exist?" % directory_path
      return

    subdirs = dir_content['Value']['Successful'][directory_path]['SubDirs']
    for subdir in subdirs.keys():
      self.search_directory(subdir, source_se, dest_se, dry_run)


    # Now do files...
    files = dir_content['Value']['Successful'][directory_path]['Files']
    for filename in files.keys():
      fullpath = os.path.join(directory_path, filename)
      if self.copy_file(fullpath, source_se, dest_se, dry_run):
        self.__n_files += 1
        self.__space_copied += files[filename]['MetaData']['Size']

  def copy_file(self, filename, source_se, dest_se, dry_run=True):
    """
    copies a file from on SE to another and registers it in 
    the dirac file catalogue
    """
    res = self.__rpcclient.getReplicas(filename, False)
    if not res["OK"]:
      print "Could not get replica status for %s" % filename
      return False
  
    ses = res['Value']['Successful'][filename].keys()
    
    if not source_se in ses:
      # print "File %s not at source SE" % filename
      return False
    
    if (source_se in ses) and (not dest_se in ses):
      print "%s" % filename
      if not dry_run:
        res = self.__dm. replicateAndRegister(filename, dest_se, source_se)
        if not res['OK']:
          print "Replicate and register failed for: %s" % filename
          print res
          return False
      return True

    # file already exists on destination SE
    return False
     

  def print_stats(self):
    """Prints summary"""
    print ""
    print "Number of files copied: %s" % self.__n_files
    space = self.__space_copied/(1024.0 * 1024.0 * 1024.0)
    print "Data copied: %0.3f GB" % space

 
def main():
  """ put it all together """

  dry_run = False
  opts, args = getopt.getopt(sys.argv[1:], "n")  

  if len(args) < 3:
    print "Usage: copydir.py [-n] <source SE> <destination SE> <LFN> [<LFN>...]"
    print "       -n: dryRun (list files to be deleted)"
    print "Example: copydir.py -n UKI-SCOTGRID-ECDF1-disk UKI-LT2-IC-HEP-disk /lsst/test2"
    sys.exit(1)

  proxy_info = getProxyInfo()   
  if not "VOMS" in proxy_info["Value"] or not proxy_info["Value"]["VOMS"]:
    print "Error: Your proxy does not contain a VOMS signature."
    print "(Try using dirac-proxy-init -g [voname]_user -M)"
    sys.exit(2)


  for opt, _ in opts:
    if opt == "-n":
      dry_run = True
      print "dryRun only: list files to be deleted"

  copyme = RecursiveCp()

  paths = []
  for tpath in args[2:]:
    tpath = os.path.normpath(tpath)
    if len(tpath.split("/")) < 2:
      print "Sorry, I can't let you do that Dave: Path %s is too broad." \
                                                                    % tpath
      sys.exit(3)
    paths.append(tpath)

  source_se = args[0]
  dest_se = args[1]
  for tpath in paths:
    copyme.search_directory(tpath, source_se, dest_se, dry_run)

  copyme.print_stats()   


if __name__ == "__main__":
  main()


