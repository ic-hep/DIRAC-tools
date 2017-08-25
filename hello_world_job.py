#!/usr/bin/env python

# submits a 'hello world' style job via the dirac api
# requires a DIRAC UI to be set up (source bashrc)
# and a valid proxy: dirac-proxy-init -g [your vo here]_user -M

# DIRAC does not work otherwise
from DIRAC.Core.Base import Script
Script.parseCommandLine( ignoreErrors = True )
# end of DIRAC setup

from DIRAC.Interfaces.API.Job import Job
from DIRAC.Interfaces.API.Dirac import Dirac

import pprint

dirac = Dirac()
j = Job()

j.setCPUTime(500)
j.setExecutable('/bin/echo hello')
j.setExecutable('/bin/hostname')
j.setExecutable('/bin/echo hello again')
j.setName('API')

result = dirac.submit(j)
print 'Submission Result: '
pprint.pprint(result)

jobid = result['JobID']

# print job id to file for future reference
joblog = open("jobid.log", "a")
joblog.write(str(jobid)+'\n')
joblog.close()

# to interactively check on job status do:
# dirac-wms-job-status -f jobid.log
print "\nThe current status of this job is:"
pprint.pprint(dirac.status(jobid))

joblog = open("jobid.log", "r")
# list comprehension :-D
all_jobids = [jobid.strip() for jobid in joblog.readlines()]

print "\nThe current status of all jobs is:"
all_status = dirac.status(all_jobids)
pprint.pprint(all_status)
