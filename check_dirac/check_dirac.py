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
import sys


# according to pylint this has to be in SHOUTING
SITES_TO_CHECK = ["LCG.UKI-LT2-IC-HEP.uk",
                  "LCG.UKI-LT2-QMUL.uk",
                  "LCG.UKI-NORTHGRID-MAN-HEP.uk",
                  "LCG.UKI-NORTHGRID-LIV-HEP.uk",
                  "LCG.UKI-SCOTGRID-GLASGOW.uk",
                  "LCG.UKI-SOUTHGRID-RALPP.uk",
                  "LCG.RAL-LCG2.uk",
                  "VAC.UKI-NORTHGRID-MAN-HEP.uk",
                  "VAC.UKI-NORTHGRID-LIV-HEP.uk",
                  "LCG.UKI-LT2-Brunel.uk"
                 ]

# solidexperiment.org is currently hardcoded to be
# ["LCG.UKI-LT2-IC-HEP.uk", "LCG.BEgrid.ULB-VUB.be"]
# otherwise we are aiming for a good UK coverage

print "Welcome to the basic dirac test script."
print "Please make sure you are using an SL6/SL7 compatible machine."
print "You will also need a valid user certificate in $HOME/.globus \n"

check_dirac_helpers.check_prerequisites()

# I refuse to have this in SHOUTING pylint be dammed
user_VO = install_ui.install_ui()

if user_VO == "solidexperiment.org":
  SITES_TO_CHECK = ["LCG.UKI-LT2-IC-HEP.uk", "LCG.BEgrid.ULB-VUB.be"]

if user_VO == "skatelescope.eu":
  SITES_TO_CHECK = ["LCG.UKI-LT2-IC-HEP.uk", "LCG.UKI-NORTHGRID-MAN-HEP.uk",
                    "LCG.RAL-LCG2.uk", "LCG.SARA-MATRIX.nl"]

make_jdls.make_jdls(user_VO, SITES_TO_CHECK)

print os.getcwd()

working_dir = os.getcwd()
check_dirac_helpers.simple_run([os.path.join(working_dir, "diractest.sh")])
check_dirac_helpers.simple_run([os.path.join(working_dir, "repandreg.sh")])

# write job numbers corresponding to sites to a log file
outfile_name = "%s/sites.log" %working_dir

outfile = open(outfile_name, "wa")

for site in SITES_TO_CHECK:

  jdlfile = site + ".jdl"
  print site
  
  sub_cmd = ["dirac-wms-job-submit", "-f", "jobs.log", jdlfile]
  command_log = install_ui.complex_run(sub_cmd)
  if site != "LCG.UKI-SOUTHGRID-RALPP.uk":
    outfile.write("Submitting standard job to %s\n" %site)
  else: 
    outfile.write("Submitting HighMem tag job to %s\n" %site)
  check_dirac_helpers.jobid_to_file(command_log, outfile)


  if site == "LCG.UKI-LT2-IC-HEP.uk" and user_VO in ["gridpp", "skatelescope.eu"]:
    print "Submitting multicore job for %s VO to %s" %(user_VO, site)
    outfile.write("Submitting multicore job for %s VO to %s\n" %(user_VO, site))

    sub_cmd = ["dirac-wms-job-submit", "-f",
               "jobs.log", "LCG.UKI-LT2-IC-HEP.multi.uk.jdl"]
    command_log = install_ui.complex_run(sub_cmd)
    check_dirac_helpers.jobid_to_file(command_log, outfile)

  if site == "LCG.UKI-LT2-IC-HEP.uk" and user_VO in ["gridpp", "lz"]:
    print "Submitting EL7 job for %s VO to %s" %(user_VO, site)
    outfile.write("Submitting EL7 job for %s VO to %s\n" %(user_VO, site))
    sub_cmd = ["dirac-wms-job-submit", "-f",
               "jobs.log", "LCG.UKI-LT2-IC-HEP.el7.uk.jdl"]
    command_log = install_ui.complex_run(sub_cmd)
    check_dirac_helpers.jobid_to_file(command_log, outfile)


outfile.close()

# test API submission (currently basic implemetation only)
wget_cmd_api = ["wget", "-np", "-O", "testapi.py",
                "https://raw.githubusercontent.com/ic-hep/DIRAC-tools/master/job_with_more_options.py"]
install_ui.simple_run(wget_cmd_api)
os.chmod("testapi.py", 0744)
wget_cmd_aux = ["wget", "-np", "https://raw.githubusercontent.com/ic-hep/DIRAC-tools/master/testapi.sh"]
install_ui.simple_run(wget_cmd_aux)
sub_cmd_api = "./testapi.py"
install_ui.simple_run(sub_cmd_api)


print '\nTo check on the status of the test jobs, please do:'
print 'cd '+ working_dir
print 'source bashrc'
print 'dirac-wms-job-status -f jobs.log'
