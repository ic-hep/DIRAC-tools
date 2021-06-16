#!/usr/bin/env python
"""
requires a DIRAC UI to be set up (source bashrc)
and a valid proxy: dirac-proxy-init -g [your vo here]_user -M
"""
from __future__ import print_function

# DIRAC does not work otherwise
from DIRAC.Core.Base import Script
Script.initialize()
# end of DIRAC setup

from DIRAC.Interfaces.API.Job import Job
from DIRAC.Interfaces.API.Dirac import Dirac


def main():
  """selects job based on user defined criteria and does basic processing as chosen"""
  dirac = Dirac()
  # def selectJobs(self, status=None, minorStatus=None, applicationStatus=None, site=None,
  #                owner=None, ownerGroup=None, jobGroup=None, date=None, printErrors=True)
  # status: Done, Failed, Killed, Matched, Received, Running, Stalled, Waiting
  failedjobs = dirac.selectJobs(status='Failed', site='LCG.UKI-SOUTHGRID-BRIS-HEP.uk')
  print(failedjobs)
  if not failedjobs['OK']:
    print("Ooops, this didn't work")
  else:
    print(failedjobs['Value'])
    for j in failedjobs['Value']:
      print(dirac.getJobStatus(j))
      # dirac.deleteJob(j)
      dirac.rescheduleJob(j)
if __name__ == "__main__":
  main()
