#!/usr/bin/python
"""
Main program for checking the status of dirac01.
Installs a fresh UI and submits jobs to a variety of sites
(CREAM, ARC) using the selected VO. Also tried to replicate
and register a file.
"""

import os
import check_dirac_helpers
import install_ui
import make_jdls

# according to pylint this has to be in SHOUTING
SITES_TO_CHECK = ["LCG.UKI-LT2-IC-HEP.uk", 
                  "LCG.UKI-LT2-QMUL.uk", 
                  "LCG.UKI-NORTHGRID-MAN-HEP.uk", 
                  "LCG.UKI-NORTHGRID-LIV-HEP.uk",
                  "LCG.UKI-SCOTGRID-GLASGOW.uk",
                  "LCG.UKI-SOUTHGRID-RALPP.uk",
                  "LCG.RAL-LCG2.uk",
                  "VAC.UKI-NORTHGRID-MAN-HEP.uk",
                  "VAC.UKI-NORTHGRID-LIV-HEP.uk"
]

# solidexperiment.org is currently hardcoded to be 
# ["LCG.UKI-LT2-IC-HEP.uk", "LCG.BEgrid.ULB-VUB.be"]
# otherwise we are aiming for a good UK coverage

print "Welcome to the basic dirac test script."
print "Please make sure you are using an SL6 compatible machine."
print "You will also need a valid user certificate in $HOME/.globus \n"

check_dirac_helpers.check_prerequisites()

# I refuse to have this in SHOUTING pylint be dammed
user_VO = install_ui.install_ui()

if user_VO == "solidexperiment.org":
  SITES_TO_CHECK = ["LCG.UKI-LT2-IC-HEP.uk", "LCG.BEgrid.ULB-VUB.be"]

make_jdls.make_jdls(user_VO, SITES_TO_CHECK)

print os.getcwd()

working_dir = os.getcwd()
check_dirac_helpers.simple_run([os.path.join(working_dir, "diractest.sh")])
check_dirac_helpers.simple_run([os.path.join(working_dir, "repandreg.sh")])


for site in SITES_TO_CHECK:

  jdlfile = site + ".jdl"
  print site
  sub_cmd = ["dirac-wms-job-submit", "-f", "jobs.log", jdlfile]
  install_ui.simple_run(sub_cmd)


print '\nTo check on the status of the test jobs, please do:'
print 'cd '+ working_dir
print 'source bashrc'
print 'dirac-wms-job-status -f jobs.log'

