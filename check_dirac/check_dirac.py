#!/usr/bin/python

import os
import sys
import check_dirac_helpers
import install_ui
import make_jdls


sites_to_check = ["UKI-LT2-IC-HEP", "UKI-LT2-Brunel", "UKI-SCOTGRID-GLASGOW", "UKI-SOUTHGRID-RALPP"]


print "Welcome to the basic dirac test script."
print "Please make sure you are using an SL6 compatible machine."
print "You will also need a valid user certificate in $HOME/.globus \n"

check_dirac_helpers.check_prerequisites()

install_ui.install_ui()

make_jdls.make_jdls(sites_to_check)

# the resulting shell script should also work within the UI
# to check dirac-dms
# this does not work
print os.getcwd()

working_dir = os.getcwd()
check_dirac_helpers.simple_run([os.path.join(working_dir, "gridpp.sh")])

# can I use the simple_run here ?
# does it still have the bashrc ?

for site in sites_to_check:
  # jdl file name = sitename.jdl
  jdlfile = site + ".jdl"

  sub_cmd = ["dirac-wms-job-submit", "-f", "jobs.log", jdlfile]
  install_ui.simple_run(sub_cmd)


print '\nTo check on the status of the test jobs, please do:'
print 'cd '+ working_dir
print 'source bashrc'
print 'dirac-wms-job-status -f jobs.log'

