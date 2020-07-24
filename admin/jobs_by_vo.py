#!/usr/bin/env python
"""
Resets (as opposed to reschedules) all jobs for a  
given user group.
Needs an admin proxy.
"""

# for available options check:
# DIRAC/Interfaces/API/Dirac.py (selectJobs)
# options = {'Status':status, 'MinorStatus':minorStatus, 'ApplicationStatus':applicationStatus, 
#             'Owner':owner, 'Site':site, 'JobGroup':jobGroup, 'OwnerGroup':ownerGroup }

import sys
import os
import getopt


import DIRAC
from DIRAC.Core.Base import Script
Script.parseCommandLine( ignoreErrors = False )
from DIRAC.Core.DISET.RPCClient import RPCClient
from DIRAC.WorkloadManagementSystem.Client.WMSClient import WMSClient


JOB_STATES = ['Received', 'Checking', 'Staging', 'Matched', 'Waiting',
              'Running', 'Stalled', 'Done', 'Completed', 'Failed', 'Killed', 'Deleted']

def main():

    if len(sys.argv) < 2:
      print "At least one parameter (user group, e.g. dune_user) expected, got %s !" \
          % (len(sys.argv)-1)
      print "Usage: jobs_by_vo.py <user group> -or- jobs_by_vo.py <user group> <site>"
      print "Example: ./jobs_by_vo.py dune_user LCG.UKI-LT2-IC-HEP.uk"
      print "Only available to dirac_admin."
      sys.exit(1)

    print '*** %s ***' %  str(sys.argv[1])
    if len(sys.argv) == 3:
      print '(at %s)' %  str(sys.argv[2])
    rpcClient = RPCClient( "WorkloadManagement/JobMonitoring" )

    for jobstate in JOB_STATES:  
      
      JOBFILTER = {}
      JOBFILTER['OwnerGroup'] = str(sys.argv[1])
      JOBFILTER['Status'] = str(jobstate)
      if len(sys.argv) == 3:
        JOBFILTER['Site'] = str(sys.argv[2])

      # print JOBFILTER  
      jobs = rpcClient.getJobs(JOBFILTER)
      if not jobs["OK"]:
        print "Could not retrieve jobs."
        sys.exit(1)
   
      job_ids = jobs["Value"]
      
      print '{0:<10} {1:>6}'.format(str(jobstate)+':', len(job_ids))
      

if __name__ == "__main__":
  main()
