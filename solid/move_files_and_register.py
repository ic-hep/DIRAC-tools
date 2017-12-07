#!/usr/bin/env python
"""Uploads local files/directories to an SE and registers them in 
the DIRAC file catalogue. Uses gfal for the uploading to enable 
checksum verification.
Valid choices for the SEs are: UKI-LT2-IC-HEP-disk or BEgrid-ULB-VUB-disk
"""
# gfal2 source:
# https://gitlab.cern.ch/dmc/gfal2-bindings/blob/master/example/python/gfal2_copy.py

import sys
import os
import uuid
# DIRAC does not work otherwise
from DIRAC.Core.Base import Script
Script.parseCommandLine( ignoreErrors = True )
# end of DIRAC setup

from DIRAC.Resources.Storage.StorageFactory import StorageFactory
from DIRAC.Resources.Catalog.FileCatalog import FileCatalog

import gfal2

def usage():
  """explains usage"""
  print "move_files_and_register.py <source> <lfn_directory> <storage element>"
  print "example: move_files_and_register.py testfile.txt /solidexperiment.org/test/ UKI-LT2-IC-HEP-disk"
  print "         (uploads testfile.txt to /solidexperiment.org/test/testfile.txt on the chosen SE)"
  print "example: move_files_and_register.py testdir /solidexperiment.org/user UKI-LT2-IC-HEP-disk"
  print "         (uploads the contents of the directory testdir to /solidexperiment.org/user/testdir"
  print "example:  move_files_and_register.py /my/absolute/path/testdir /solidexperiment.org/user UKI-LT2-IC-HEP-disk"

  sys.exit(0)


class FileUploader(object):

  def __init__(self):
    # set up gfal
    self.__gfalctxt = gfal2.creat_context()

    # setup DIRAC file catalogue
    self.__fc = FileCatalog()


  def safe_upload(self, source_file, base_pfn):
    """uploads a file using gfal2"""
    # TODO: This function needs a retry loop, catching any of the gfal exceptions
    full_source = "file://%s" % os.path.abspath(source_file)
    gfalparams = self.__gfalctxt.transfer_parameters()
    # this hopefully enables checksum verification (hard to test ...)
    gfalparams.checksum_check = True
    fileinfo = self.__gfalctxt.stat(full_source)
    filesize = fileinfo.st_size
    filesum = self.__gfalctxt.checksum(full_source, "adler32")
    gfalparams.set_user_defined_checksum("adler32", filesum)
    full_pfn = "%s/%s" % (base_pfn, source_file)
    self.__gfalctxt.filecopy(gfalparams, full_source, full_pfn) 

    return (filesize, filesum)


  def upload_files(self, source, base_pfn, base_lfn, target_se):
    """for directories: recursively searches the source directory for files and uploads them to SE
    otherwise, just uploads file"""
    if os.path.isfile(source):
      # TODO: this and the same block below should be a function
      filesize, filesum = self.safe_upload(source, base_pfn)
      full_lfn = "%s/%s" %(base_lfn, source)
      full_pfn = "%s/%s" %(base_pfn, source)
      self.registerfile(full_pfn, full_lfn, target_se, filesum, filesize)
      return 
    for dirpath, subdirs, files in os.walk(source):
      for filename in files:
        source_file = os.path.join(dirpath, filename)
        print "Trying %s" % filename
        filesize, filesum = self.safe_upload(source_file, base_pfn)
        print "Uploaded: %s (%s %s)" % (filename, filesize, filesum)
        full_lfn = "%s/%s" %(base_lfn, source_file)
        full_pfn = "%s/%s" %(base_pfn, source_file)
        self.registerfile(full_pfn, full_lfn, target_se, filesum, filesize)
        # TODO: if the registering fails, the file should be deleted to avoid 'dark data' that is on disk, but not in the catalogue

  def registerfile(self, full_pfn, full_lfn, target_se, checksum, size):
    infoDict = {}
    infoDict['PFN'] = full_pfn
    infoDict['Size'] = int(size)
    infoDict['SE'] = target_se
    infoDict['GUID'] = str(uuid.uuid4())
    infoDict['Checksum'] = checksum   
    fileDict = {}
    fileDict[full_lfn] = infoDict
    result = self.__fc.addFile(fileDict) 
    # TODO: handle the return code as an exception 
    if not result["OK"]:
      print result
      return
    if result["Value"]["Failed"]:
      print result["Value"]
    return

def get_base_pfn(base_lfn, target_se):
  """constructs a pfn from an lfn and a target se"""
  storage_factory = StorageFactory()
  result = storage_factory.getStorages(target_se)
  if not result['OK']:
    raise Exception("Failed to look up storage element details: %s" % result)
  # look for srm (don't use anything else)
  storage_info = result['Value']
  for proto_info in storage_info['ProtocolOptions']:
    if proto_info['Protocol'] != 'srm':
      continue
    se_host = proto_info['Host']
    se_port = proto_info['Port']
    se_wsurl = proto_info['WSUrl']
    se_vopath = proto_info['Path']
    base_pfn = "srm://%s:%s%s%s%s" %(se_host, se_port, se_wsurl, se_vopath, base_lfn)
    return base_pfn
  raise Exception("No srm protocol found for storage element: %s" %target_se)

def check_lfn(lfn):
  """LFN must start with /solidexperiment.org"""
  if not lfn.startswith("/solidexperiment.org"):
    raise Exception("LFN does not start with /solidexperiment.org as required by DIRAC")

def main():
  """does the work"""
  # TODO: needs a try and except wrapper
  if len(sys.argv) != 4:
    usage()
  source = sys.argv[1]
  base_lfn = sys.argv[2]
  check_lfn(base_lfn)
  target_se = sys.argv[3]
  # does the input exist (beware of the typos)
  if not os.path.exists(source):
    raise Exception("Input does not exist, please check path.")
  # Input can be relative or absolute path: Here get the absolute path of the source
  full_path = os.path.abspath(source)
  input_source = os.path.basename(full_path) # file(s) to be uploaded are here
  dir_name = os.path.dirname(full_path)
  # that way, we know where we are
  os.chdir(dir_name)
  print dir_name, input_source, full_path

  file_uploader = FileUploader()
  base_pfn = get_base_pfn(base_lfn, target_se)
  file_uploader.upload_files(input_source, base_pfn, base_lfn, target_se)

if __name__ == "__main__":
  main()
