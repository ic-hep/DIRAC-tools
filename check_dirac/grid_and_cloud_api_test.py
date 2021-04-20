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

import pprint
import argparse

def configure_and_submit(dirac, job, logfile, testvo):
  """configure and send two jobs, one to grid and one to cloud"""
  job.setCPUTime(500)
  # testapi takes 'magic' as an argument
  job.setExecutable('testapi.sh', arguments='magic')
  job.setName('APIGridtest')
  job.setDestination('LCG.UKI-LT2-IC-HEP.uk')
  # This is GridPP DIRAC specific
  job.setPlatform("AnyPlatform")

  result = dirac.submitJob(job)
  logfile.write('Submission Result: ')
  pprint.pprint(result, logfile)
  jobid = result['JobID']

  # print job id to file for future reference
  joblog = open("api_jobid.log", "a")
  joblog.write(str(jobid)+'\n')
  joblog.close()

  # can I reuse 'job' ?
  if testvo == "lz":
    job.setName('APICloudtest')
    job.setDestination('CLOUD.UKI-LT2-IC-HEP-lz.uk')
    # This is GridPP DIRAC specific
    job.setPlatform("AnyPlatform")
    result = dirac.submitJob(job)
    logfile.write('Submission Result: ')
    pprint.pprint(result, logfile)
    jobid = result['JobID']
    # print job id to file for future reference
    joblog = open("api_jobid.log", "a")
    joblog.write(str(jobid)+'\n')
    joblog.close()



  return jobid

def check_job(dirac, jobid, logfile):
  """print status after submission to catch immediate errors"""
  # to interactively check on job status do:
  # dirac-wms-job-status -f api_jobid.log
  logfile.write("\nThe current status of this job is:")
  pprint.pprint(dirac.getJobStatus(jobid), logfile)

def check_all_jobs(dirac, logfile):
  """end programme by printing job status"""
  joblog = open("api_jobid.log", "r")
  # list comprehension :-D
  all_jobids = [jobid.strip() for jobid in joblog.readlines()]

  logfile.write("\nThe current status of all jobs is:")
  all_status = dirac.getJobStatus(all_jobids)
  pprint.pprint(all_status, logfile)


def main():
  """reads in VO so it knows which sites to submit to and then submits job"""
  parser = argparse.ArgumentParser()
  parser.add_argument("vo")
  args = parser.parse_args()
  testvo = str(args.vo)

  logfile = open("api.log", "w")
  dirac = Dirac()
  job = Job()

  jobid = configure_and_submit(dirac, job, logfile, testvo)
  check_job(dirac, jobid, logfile)
  check_all_jobs(dirac, logfile)
  logfile.close()
  print("API logs can be found in api.log and api_jobid.log.")

if __name__ == "__main__":
  main()
