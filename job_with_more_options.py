#!/usr/bin/env python

# requires a DIRAC UI to be set up (source bashrc)
# and a valid proxy: dirac-proxy-init -g [your vo here]_user -M
# TODO: Error handling

# DIRAC does not work otherwise
from DIRAC.Core.Base import Script
Script.initialize()
# end of DIRAC setup

from DIRAC.Interfaces.API.Job import Job
from DIRAC.Interfaces.API.Dirac import Dirac

import pprint


def configure_and_submit(dirac, job, logfile): 

  job.setCPUTime(500)
  # testapi takes 'magic' as an argument
  job.setExecutable('testapi.sh', arguments='magic')
  job.setName('API_test')
  # any site you don't want your jobs to go to:
  job.setBannedSites(['LCG.UKI-SOUTHGRID-BRIS-HEP.uk', 'LCG.pic.es'])
  # test Manchester GPU queue
  # job.setTag(['GPU', 'skatelescope.eu.gpu'])
  # This is GridPP DIRAC specific
  job.setPlatform("AnyPlatform") 

  result = dirac.submitJob(job)
  logfile.write('Submission Result: ')
  pprint.pprint(result, logfile)
  jobid = result['JobID']

  # print job id to file for future reference
  joblog = open("jobid.log", "a")
  joblog.write(str(jobid)+'\n')
  joblog.close()

  return jobid

def check_job(dirac, jobid, logfile):
  # to interactively check on job status do:
  # dirac-wms-job-status -f jobid.log
  logfile.write("\nThe current status of this job is:")
  pprint.pprint(dirac.getJobStatus(jobid), logfile)

def check_all_jobs(dirac, logfile):

  joblog = open("jobid.log", "r")
  # list comprehension :-D
  all_jobids = [jobid.strip() for jobid in joblog.readlines()]

  logfile.write("\nThe current status of all jobs is:")
  all_status = dirac.getJobStatus(all_jobids)
  pprint.pprint(all_status, logfile)


def main():
  logfile = open("api.log", "w")
  dirac = Dirac()
  job = Job()

  jobid = configure_and_submit(dirac, job, logfile)
  check_job(dirac, jobid, logfile)
  check_all_jobs(dirac, logfile)
  logfile.close()
  print "Logs can be found in api.log and jobid.log."

if __name__ == "__main__":
    main()
