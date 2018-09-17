#!/usr/bin/env python

# source /vols/grid/ui/setup_cvmfs_ui.sh
# needs a valid grid UI
# voms-proxy-init --valid 24:00 --voms lz
# e.g. ./listlz.py 20170402
# 
# lists all files in a directory at 
# srm:///gfe02.grid.hep.ph.ic.ac.uk
#      /pnfs/hep.ph.ic.ac.uk/data/lz/[whateveryouspecify]
# prints path, checksum (adler32) and size (bytes) to a file

import gfal2
import os
import stat
import sys

def list_dir(cntxt, dir_name, fd, depth=0):
  if depth < 2:
    print dir_name
 
  subdirs = []
  n_of_tries = 0
  thing = None
  while n_of_tries < 3:  
    try:
      content = cntxt.listdir(dir_name)
      subdirs = []
      for thing in content:
        fullpath = os.path.join(dir_name, thing)
        info = cntxt.stat(fullpath)
        if stat.S_ISDIR(info.st_mode):
          subdirs.append(fullpath)
        else:  
          filesize = info.st_size
          filesum = cntxt.checksum(fullpath, "adler32")
          process_file(fullpath, filesize, filesum, fd)
      break
    except Exception as e:
      n_of_tries += 1
      print "Failed to process %s (%s), file: %s" %(dir_name, e, thing)   
  for d in subdirs:
    list_dir(cntxt, d, fd, depth=depth+1)


def process_file(filename, filesize, filesum, fd):
  fd.write("%s %s %u\n" %(filename, filesum, filesize))


for dir_name in sys.argv[1:]:
  ctxt = gfal2.creat_context()
  outfile = dir_name.replace("/", "_")
  fd = open("%s.txt" %outfile, "w")
  fullpath = os.path.join("srm://gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/lz/lz/data/MDC2/background/LZAP-3.12.0-PHYSICS-3.12.1/", dir_name)
  list_dir(ctxt, fullpath, fd)
  fd.close()



