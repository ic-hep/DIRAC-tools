#!/usr/bin/env python

from DIRAC.Core.Base import Script
Script.initialize()

import sys
import os
import getopt

from DIRAC.Core.DISET.RPCClient import RPCClient
from DIRAC.DataManagementSystem.Client.DataManager import DataManager



class RecursiveRm(object):
  def __init__(self):
    self.__rpcclient = RPCClient( "DataManagement/FileCatalog" )
    self.__dm = DataManager()
    self.__n_dirs = 0
    self.__n_files = 0
    self.__space_freed = 0L

  def clear_directory(self, directory_path, se_name, dry_run=True):

    print "Clearing directory: %s" % directory_path
    
    dir_content =  self.__rpcclient.listDirectory(directory_path, False)

    if not dir_content["OK"]:
      print "Failed to contact DIRAC server for %s" % directory_path
      return
    
    if directory_path in dir_content['Value']['Failed']:
      print "Could not access %s, maybe it doesn't exist?" % directory_path
      return

    subdirs = dir_content['Value']['Successful'][directory_path]['SubDirs']
    for subdir in subdirs.keys():
      self.clear_directory(subdir, se_name, dry_run)


    # Now do files...
    files = dir_content['Value']['Successful'][directory_path]['Files']
    for filename in files.keys():
      fullpath = os.path.join(directory_path, filename)
      if self.clear_file(fullpath, se_name, dry_run):
        self.__n_files += 1
        self.__space_freed += files[filename]['MetaData']['Size']

    if self.remove_empty_dir(directory_path, dry_run):
      self.__n_dirs += 1
      

  def remove_empty_dir(self, directory_path, dry_run=True):
    # check if directory is now empty and the remove the directory
    dir_content =  self.__rpcclient.listDirectory(directory_path, False)

    if not dir_content["OK"]:
      print  "Could not access %s" % directory_path
      return False


    subdirs = dir_content['Value']['Successful'][directory_path]['SubDirs']
    files = dir_content['Value']['Successful'][directory_path]['Files']
  
    if not subdirs and not files:
      if not dry_run:
        self.__dm.fc.removeDirectory(directory_path, recursive=False)
      return True

    return False


  def clear_file(self, filename, se_name, dry_run=True):
  
    res = self.__rpcclient.getReplicas(filename, False)
    if not res["OK"]:
      print "Could not get replica status for %s" % filename
      return False
  
    ses = res['Value']['Successful'][filename].keys()
    
    # remove file regardless of number of replicas
    if se_name == "Any":
      print "%s" % filename
      if not dry_run:
        self.__dm.removeFile(filename)
      return True

    # file exists only at the chosen SE
    #     -> delete file and remove from file catalogue
    if len(ses) == 1 and se_name in ses:
      print "%s" % filename
      if not dry_run:
        self.__dm.removeFile(filename)
      return True
        
    # file exists at the chosen SE and elswhere -> delete replica at chosen SE
    if len(ses) > 1 and se_name in ses:
      print "%s" % filename
      if not dry_run:
        self.__dm.removeReplica(se_name, filename)
      return True

    return False
     

  def print_stats(self):
    print ""
    print "Number of files deleted: %s" % self.__n_files
    print "NUmber of (sub)directories deleted: %s" % self.__n_dirs
    space = self.__space_freed/(1024.0 * 1024.0 * 1024.0)
    print "Space freed: %0.3f GB" % space

 
def main():


  dry_run = False
  opts, args = getopt.getopt(sys.argv[1:], "n")  

  if len(args) < 2:
    print "Usage: recursiverm.py [-n] <SE> <path> [<path>...]"
    print "       -n: dryRun (list files to be deleted)"
    print "Use 'Any' for <SE> to delete all replicas in a directory"
    sys.exit(1)

  for opt, _ in opts:
    if opt == "-n":
      dry_run = True
      print "dryRun only: list files to be deleted"

  rrm = RecursiveRm()

  se_name = args[0]
  for tpath in args[1:]:
    if tpath.endswith("/"):
      tpath = tpath.rstrip("/")
    rrm.clear_directory(tpath, se_name, dry_run)

  rrm.print_stats()   


if __name__ == "__main__":
  main()


