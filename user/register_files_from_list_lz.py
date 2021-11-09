#!/usr/bin/env python
"""
Hackety script to let LZ register files in the DFC. Could be adapted to other VOs
if necessary (but I'd rather not...)
Needs a valid DIRAC UI (source bashrc) v7r1 or higher and an lz_production proxy.
Input format: text files, one "almost lfn" (lz/some/directory/filename.root) per line.
"""
from __future__ import print_function

from DIRAC.Core.Base import Script
Script.initialize()

import argparse
import gfal2
import uuid
import time

from DIRAC.Resources.Catalog.FileCatalog import FileCatalog
from DIRAC.Core.Security.ProxyInfo import getProxyInfo
from DIRAC.Interfaces.API.Dirac import Dirac

# proper surl to avoid bdii queries
LZBASE = "srm://gfe02.grid.hep.ph.ic.ac.uk:8443/srm/managerv2?SFN=/pnfs/hep.ph.ic.ac.uk/data/lz"


def file_properties(cntxt, fullpath):
  """extracts information if a single file is given as input"""
  info = cntxt.stat(fullpath)
  filesize = info.st_size
  filesum = cntxt.checksum(fullpath, "adler32")
  return(filesize, filesum)

def is_file_already_registered(dirac, lfn, se):
  """0 = not registered, 1 = registered, 2 = problem determining status"""
  result = dirac.getReplicas(lfn)
  # print(result)
  if not result['OK']:
    # this occasionally fails when the catalog is busy
    print("Warning: getReplicas failed, sleeping 60 s and then trying one more time.")
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

def registerfile(pfnpath, lfn, checksum, size, se, fc, dirac):
  """finally registers the file"""
  infoDict = {}
  infoDict['PFN'] = pfnpath
  infoDict['Size'] = int(size)
  infoDict['SE'] = se
  infoDict['GUID'] = str(uuid.uuid4())
  infoDict['Checksum'] = checksum
  fileDict = {}
  fileDict[lfn] = infoDict

  is_reg = is_file_already_registered(dirac, lfn, se)
  if is_reg == 1:
    print("File %s is already registered at %s" %(str(lfn), se))
    return
  elif is_reg == 2:
    print("Could not determine status of file %s" % str(lfn))
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
  """setups all the necessary infrastucture, reads in file containing LFNs
  to be registered and finally calls the register function"""
  parser = argparse.ArgumentParser(description='reads in list of LFN and registers them in the DFC')
  parser.add_argument('missing_lfns', type=str,
                      help='file containing list of LFNs to register')
  args = parser.parse_args()
  ctxt = gfal2.creat_context()
  dirac = Dirac()
  filecatalog = FileCatalog()

  with open(args.missing_lfns) as missing:
    for line in missing:
      print(line.strip())
      almost_lfn = line.strip()
      # Chris' format is lfn minus the first '/'
      lfn = "/"+ almost_lfn
      fullpath = LZBASE + lfn
      fsize, checksum = file_properties(ctxt, fullpath)
      registerfile(fullpath, lfn, checksum, fsize, "UKI-LT2-IC-HEP-disk", filecatalog, dirac)


if __name__ == "__main__":
  main()
