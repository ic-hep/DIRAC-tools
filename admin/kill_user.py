#!/usr/bin/env python
"""
Kill all of the jobs for a given user.
"""

import sys

from DIRAC.Core.Base import Script
Script.parseCommandLine(ignoreErrors = False)
from DIRAC.Interfaces.API.Dirac import Dirac
from DIRAC.Core.DISET.RPCClient import RPCClient

BATCH_SIZE = 100

def find_jobs(uname, site=None):
  """ Find all active jobs for a given user.
      i.e. Jobs in a non-terminal state.
  """
  jfilter = { 'Owner': uname,
              'Status': ['Received', 'Scheduled', 'Submitted', 'Running'],
            }
  if site:
    jfilter['Site'] = site
  rpc = RPCClient( "WorkloadManagement/JobMonitoring" )
  res = rpc.getJobs(jfilter)
  if not res['OK']:
    print "ERROR: Failed to fetch job list (%s)." % res
    return []
  return res['Value']

def usage():
  """ Print usage information and exit. """
  print ""
  print "Usage: kill-user.py <username> [<site>]"
  print ""
  sys.exit(1)

def main():
  """ Main program entry point. """
  if len(sys.argv) < 2 or len(sys.argv) > 3:
    usage()
  uname = sys.argv[1]
  site = None
  if len(sys.argv) >= 3:
    site = sys.argv[2]
  print "Fetching job list for user '%s'..." % uname
  jlist = find_jobs(uname, site)
  jlist.append('1')
  print "Found %u jobs, killing..." % len(jlist)
  dirac = Dirac()
  for loc in xrange(0, len(jlist), BATCH_SIZE):
    print "%u/%u complete." % (loc, len(jlist))
    dirac.killJob(jlist[loc:loc+BATCH_SIZE])
  print "%u/%u complete." % (len(jlist), len(jlist))
  print "Exiting."

if __name__ == "__main__":
  main()

