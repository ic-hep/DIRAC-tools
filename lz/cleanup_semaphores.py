#!/usr/bin/env python
"""
example usage: ./cleanup_semaphores.py usdc-missing-sr1-20210906.txt
input format: file containing LFNs, e.g.
/lz/sim/fast/background/bgSR1/BACCARAT-6.2.10_PROD-0/Co60_ForwardFieldResistors/lz_Co60_ForwardFieldResistors_root_31400010.v0.root
needs valid grid UI and lz proxy:
source /cvmfs/grid.cern.ch/umd-c7ui-latest/etc/profile.d/setup-c7-ui-example.sh
voms-proxy-init --valid 24:00 --voms lz (--voms lz:/lz/Role=production to upload the semaphores)
"""

import argparse
import os
import re
import gfal2

# proper surl to avoid bdii queries
LZBASE = "srm://gfe02.grid.hep.ph.ic.ac.uk:8443/srm/managerv2?SFN=/pnfs/hep.ph.ic.ac.uk/data/lz"


def file_properties(cntxt, fullpath):
  """extracts information if a single file is given as input"""
  info = cntxt.stat(fullpath)
  filesize = info.st_size
  filesum = cntxt.checksum(fullpath, "adler32")
  return(filesize, filesum)


def write_semaphore(almost_lfn, checksum, fsize, fullpath):
  """write the actual semphore"""
  # replace .root with .sem
  sem_name = os.path.basename(almost_lfn)[:-5]+".sem"
  sem_file = open(sem_name, 'w')
  # extracts BACCART version, assumes format BACCARAT-n.n.n[_/-]
  baccversion = re.search(r"BACCARAT-([^_/-]*)", almost_lfn).group(1)

  SEMTEXT = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<lz_metadata>
  <canonical_path>%s</canonical_path>
  <checksum algorithm="Adler32">%s</checksum>
  <equipment>simulations</equipment>
  <file_size>%s</file_size>
  <original_path>%s</original_path>
  <baccarat_vers>%s</baccarat_vers>
  <source>BACCARAT</source>
  <type>bacc-root</type>
</lz_metadata>
"""
  sem_file.write(SEMTEXT % (almost_lfn, checksum, fsize, fullpath[56:], baccversion))


def main():
  """setups all the necessary infrastucture, reads in file containing LFNs
  to be registered and finally calls the register function"""
  parser = argparse.ArgumentParser(description='generates a semaphore for a given LZAP lfn')
  parser.add_argument('missing_lfns', type=str,
                      help='file containing list of LFNs to register')
  args = parser.parse_args()
  ctxt = gfal2.creat_context()

  with open(args.missing_lfns) as missing:
    for line in missing:
      print(line.strip())
      lfn = line.strip()
      fullpath = LZBASE + lfn
      fsize, checksum = file_properties(ctxt, fullpath)
#      print(lfn, fsize, checksum)
#      print(os.path.basename(lfn))
      write_semaphore(lfn[1:], checksum, fsize, fullpath)

if __name__ == "__main__":
  main()
