#!/usr/bin/env python
"""
Script to (try and) extract all necessary data for a file from a storage element
to be able to register this file in the DIRAC File Catalogue
Takes a full path or a directory as input.
Needs valid grid UI:
source /cvmfs/grid.cern.ch/umd-c7ui-latest/etc/profile.d/setup-c7-ui-example.sh
and a valid proxy:
voms-proxy-init --valid 24:00 --voms [your VO goes here]
If the command is really slow, you can try to force it to use Imperial College's
bdii instead of the default. Before you start the script, do:
export LCG_GFAL_INFOSYS=localbdii.grid.hep.ph.ic.ac.uk:2170
Output:
prints path, checksum (adler32) and size (bytes) to a file
"""
from __future__ import print_function
import os
import stat
import sys
import argparse
import gfal2

def list_dir(cntxt, dir_name, fd, depth=0):
  """lists all the files in a directory and its subdirectories"""
  if depth < 2:
    print("Processing: %s" %dir_name)

  counter = 0
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
          counter = counter+1
          if counter%100 == 0:
            print("Number of processed files: %s" %counter)
          process_file(fullpath, filesize, filesum, fd)
      break
    except Exception as process_except:
      n_of_tries += 1
      print("Failed to process %s (%s), file: %s" %(dir_name, process_except, thing))
  for d in subdirs:
    list_dir(cntxt, d, fd, depth=depth+1)


def single_file(cntxt, fullpath, outputfile):
  """extracts information if a single file is given as input"""
  info = cntxt.stat(fullpath)
  filesize = info.st_size
  filesum = cntxt.checksum(fullpath, "adler32")
  process_file(fullpath, filesize, filesum, outputfile)


def process_file(filename, filesize, filesum, outputfile):
  """format output"""
  outputfile.write("%s %s %u\n" %(filename, filesum, filesize))


def main():
  """Definition of all arguments, help function, etc. Entry point to program."""

  parser = argparse.ArgumentParser(description="List file size and chechksum. Needs a valid grid UI and proxy.",
                                   epilog="Example: ./extract_file_data.py -d srm://gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/gridpp/gridpp/user/daniela.bauer -o myfiles.txt")
  parser.add_argument("-d", "--directory", help="full path (including storage element name) to a directory")
  parser.add_argument("-f", "--filename", help="full path (including storage element name) to a file")
  req_grp = parser.add_argument_group(title='required arguments')
  req_grp.add_argument('-o', "--output", required=True, help="output file name")
  args = parser.parse_args()
  # 1 is the program itself, how could I forget
  if len(sys.argv) != 5:
    print("Please specify [either a directory or a file] and the output file for the results.")
    sys.exit(0)

  file_descriptor = open(args.output, "w")
  ctxt = gfal2.creat_context()

  if args.directory:
    # print(args.directory)
    list_dir(ctxt, args.directory, file_descriptor)
  elif args.filename:
    single_file(ctxt, args.filename, file_descriptor)
  else:
    print("Something went wrong.")

  file_descriptor.close()

if __name__ == "__main__":
  main()
