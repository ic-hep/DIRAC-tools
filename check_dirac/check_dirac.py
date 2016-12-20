#!/usr/bin/python

import os
import sys
import check_dirac_helpers
import install_ui
import make_jdls

sites_to_check = ["LCG.UKI-LT2-IC-HEP.uk", 
                  "LCG.UKI-LT2-QMUL.uk", 
                  "LCG.UKI-NORTHGRID-MAN-HEP.uk", 
                  "LCG.UKI-NORTHGRID-LIV-HEP.uk",
                  "LCG.UKI-SOUTHGRID-OX-HEP.uk",
                  "LCG.UKI-SCOTGRID-GLASGOW.uk",
                  "LCG.UKI-SOUTHGRID-RALPP.uk",
                  "LCG.RAL-LCG2.uk",
                  "VAC.UKI-NORTHGRID-MAN-HEP.uk",
                  "VAC.UKI-NORTHGRID-LIV-HEP.uk"
]



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

  jdlfile = site + ".jdl"
  print site
  sub_cmd = ["dirac-wms-job-submit", "-f", "jobs.log", jdlfile]
  install_ui.simple_run(sub_cmd)


print '\nTo check on the status of the test jobs, please do:'
print 'cd '+ working_dir
print 'source bashrc'
print 'dirac-wms-job-status -f jobs.log'

