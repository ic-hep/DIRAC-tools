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

#JOBFILTER =  { 'OwnerGroup': 'dune_user',   
#               'Status': 'Failed',
#               'Site': 'LCG.UKI-LT2-IC-HEP.uk'}

import sys
import os
import getopt


import DIRAC
from DIRAC.Core.Base import Script
Script.parseCommandLine( ignoreErrors = False )
from DIRAC.Core.DISET.RPCClient import RPCClient
from DIRAC.WorkloadManagementSystem.Client.WMSClient import WMSClient


def main():

    if len(sys.argv) < 2:
      print "At least one parameter (user group, e.g. dune_user) expected, got %s !" \
          % (len(sys.argv)-1)
      print "Usage: resetjobs.py <user group> -or- resetjobs.py <user group> <site>"
      print "Example: ./resetjobs.py dune_user LCG.UKI-LT2-IC-HEP.uk"
      print "Only available to dirac_admin."
      sys.exit(1)



    # dictionary  
    JOBFILTER = {}
    JOBFILTER['OwnerGroup'] = str(sys.argv[1])
    JOBFILTER['Status'] = 'Failed'
    if len(sys.argv) == 3:
      JOBFILTER['Site'] = str(sys.argv[2])

    print JOBFILTER  

    rpcClient = RPCClient( "WorkloadManagement/JobMonitoring" )

    jobs = rpcClient.getJobs(JOBFILTER)
    if not jobs["OK"]:
        print "Could not retrieve jobs."
        sys.exit(1)
   
    job_ids = jobs["Value"]
    print "%s matching jobs found." % len(job_ids)
    if len(job_ids) > 500:
      print "Will reset the first 500 jobs, please rerun script to delete more."


    wmsClient = WMSClient()

    for jobid in job_ids[0:500]:
      # print jobid
      res = wmsClient.resetJob(int(jobid))
      if not res['OK']:
        print "Could not reset job %s" % jobid
    

if __name__ == "__main__":
  main()
