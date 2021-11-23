#!/usr/bin/env python
"""
needs valid grid UI and lz production proxy:
source /cvmfs/grid.cern.ch/umd-c7ui-latest/etc/profile.d/setup-c7-ui-example.sh
voms-proxy-init --valid 24:00 --voms lz:/lz/Role=production
broken semaphore file paths have this format:
/pnfs/hep.ph.ic.ac.uk/data/lz/spade/sending/usdc/lzap/LZAP-5.3.8/202110/006011/lz_006011_000042_dqm.sem
runs after cleanup_semaphores[..].py
"""
from __future__ import print_function

import argparse
import os
import gfal2


# proper surl to avoid bdii queries
LZBASE = "srm://gfe02.grid.hep.ph.ic.ac.uk:8443/srm/managerv2?SFN="

def main():
  """setups all the necessary infrastucture, reads in file containing LFNs
  to be registered and finally calls the register function"""
  parser = argparse.ArgumentParser(description='quietly replaces broken semaphores with newly generated ones')
  parser.add_argument('broken_sem', type=str,
                      help='file containing filepaths of the broken semaphores')
  args = parser.parse_args()
  ctxt = gfal2.creat_context()
  params = ctxt.transfer_parameters()
  params.timeout = 3600
  params.overwrite = True

  with open(args.broken_sem) as broken_sem:
    for line in broken_sem:
      print(line.strip())
      pfn = line.strip()
      if not pfn.startswith('/'):
        continue
      # the file name is the last bit in the string
      semfile_name = pfn.split('/')[-1]
      print(semfile_name)
      # check if I have a new file to replace the old one
      if os.path.exists(semfile_name):
        sourcefile = "file:///home/hep/dbauer/" + semfile_name
        destination = LZBASE + pfn
        print(destination)
        ret = ctxt.filecopy(params, str(sourcefile), str(destination))
        if ret == 0:
          print("%s copied successfully" %semfile_name)
        else:
          print(ret)
          print("ERROR copying %s" %semfile_name)
      else:
        print("Oh dear, no mathcing fixed file exists: %s" %pfn)
if __name__ == "__main__":
  main()
