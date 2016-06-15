#!/usr/bin/python

import os
import sys
import check_dirac_helpers
import install_ui
import make_jdls

# on the naughty step

# UKI-LT2-Brunel --never runs
# UKI-SCOTGRID-DURHAM
# UKI-SOUTHGRID-RALPP
# UKI-SOUTHGRID-BRI-HEP

# This should work
# "EFDA-JET"
# "UKI-LT2-IC-HEP"
# "UKI-LT2-QMUL"
# "UKI-NORTHGRID-LANCS-HEP"
# "UKI-NORTHGRID-LIV-HEP"
# "UKI-SOUTHGRID-CAM-HEP"
# "UKI-SCOTGRID-ECDF" (priority too low)
# "UKI-SCOTGRID-GLASGOW"
# sites_to_check = ["UKI-LT2-IC-HEP", "UKI-NORTHGRID-MAN-HEP", "UKI-SOUTHGRID-OX-HEP"]
sites_to_check = ["UKI-LT2-IC-HEP", 
                  "UKI-LT2-QMUL", 
                  "UKI-NORTHGRID-MAN-HEP", 
                  "UKI-NORTHGRID-LIV-HEP",
                  "UKI-SOUTHGRID-OX-HEP",
                  "UKI-SCOTGRID-GLASGOW",
                  "UKI-SOUTHGRID-RALPP",
                  "RAL-LCG2"
]

# sites_to_check = ["UKI-LT2-IC-HEP"]

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
check_dirac_helpers.simple_run([os.path.join(working_dir, "repandreg.sh")])


for site in sites_to_check:
  # jdl file name = sitename.jdl
  jdlfile = site + ".jdl"

  sub_cmd = ["dirac-wms-job-submit", "-f", "jobs.log", jdlfile]
  install_ui.simple_run(sub_cmd)


print '\nTo check on the status of the test jobs, please do:'
print 'cd '+ working_dir
print 'source bashrc'
print 'dirac-wms-job-status -f jobs.log'

