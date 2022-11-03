#!/usr/bin/env python
"""
Main program for checking the status of dirac01.
Installs a fresh UI and submits jobs to a variety of sites
(CREAM, ARC) using the selected VO. Also tried to replicate
and register a file.
"""
from __future__ import print_function
import os
import sys
import install_ui
import make_jdls
import check_dirac_helpers


def main():
  """This is where all the action is. """
  print("Welcome to the basic dirac test script.")
  print("Please make sure you are using an SL7 compatible machine.")
  print("You will also need a valid user certificate in $HOME/.globus \n")

  # 0. Sanity checks
  check_dirac_helpers.check_prerequisites()

  # 1. Setup a UI
  # pick which VO to test, default: gridpp
  print("Which VO do you want to test (default: gridpp) ?")
  user_VO = raw_input("Your choices are: gridpp, lz, lsst, solidexperiment.org, skatelescope.eu: ") \
            or "gridpp"
  if user_VO not in ["gridpp", "lz", "lsst", "solidexperiment.org", "skatelescope.eu"]:
    print("Testing for %s VO is not supported." % user_VO)
    sys.exit(0)

  # use cvmfs ui or install local one, default: local
  install_type = raw_input("Install new local UI or use cvmfs (default: local)? Please enter: 'local'/'cvmfs': ") \
                 or "local"
  if install_type not in ["local", "cvmfs"]:
    print("WARNING: install_type %s not known, proceeding with local install." % install_type)
    install_type = "local"

  install_ui.setup_ui(user_VO, install_type)

  # 2. Select Sites and make JDLs
  # aiming for good UK coverage, ARC and HTCondor
  sites_to_check = ["LCG.UKI-LT2-IC-HEP.uk",
                    "LCG.UKI-LT2-QMUL.uk",
                    "LCG.UKI-LT2-Brunel.uk",
                    "LCG.UKI-NORTHGRID-LANCS-HEP.uk",
                    "LCG.UKI-NORTHGRID-LIV-HEP.uk",
                    "LCG.UKI-SOUTHGRID-RALPP.uk"]

  if user_VO == "solidexperiment.org":
    sites_to_check = ["LCG.UKI-LT2-IC-HEP.uk", "LCG.BEgrid.ULB-VUB.be"]

  if user_VO == "skatelescope.eu":
    sites_to_check = ["LCG.UKI-LT2-IC-HEP.uk", "LCG.UKI-NORTHGRID-MAN-HEP.uk",
                      "LCG.RAL-LCG2.uk", "LCG.SARA-MATRIX.nl"]
  if user_VO == "lz":
    sites_to_check.append("CLOUD.UKI-LT2-IC-HEP-lz.uk")

  make_jdls.make_jdls(user_VO, sites_to_check)

  # 3. Check that dirac test script works locally
  print('Running local test of script to submit: diractest.sh')
  working_dir = os.getcwd()
  testscript = os.path.join(working_dir, "diractest.sh")
  test_submitted_script_cmd = [testscript, "testarg1", "testarg2"]
  check_dirac_helpers.complex_run(test_submitted_script_cmd)

  # write job numbers corresponding to sites to a log file
  outfile_name = "%s/sites.log" %working_dir

# 6. Job Submission
  outfile = open(outfile_name, "a")

  for site in sites_to_check:

    jdlfile = site + ".jdl"
    print(site)

    sub_cmd = ["dirac-wms-job-submit", "-f", "jobs.log", jdlfile]
    outfile.write("Submitting standard job to %s\n" %site)
    command_log = install_ui.complex_run(sub_cmd)
    check_dirac_helpers.jobid_to_file(command_log, outfile)

    # now all the special cases (all these sites also receive a standard test job)
    # all special cases run either at RALPP or Imperial

    if site == "LCG.UKI-SOUTHGRID-RALPP.uk":
      print("Submitting multicore job for %s VO to %s" % (user_VO, site))
      outfile.write("Submitting multicore job for %s VO to %s\n" % (user_VO, site))
      sub_cmd = ["dirac-wms-job-submit", "-f",
                 "jobs.log", "LCG.UKI-SOUTHGRID-RALPP.uk.multi.jdl"]
      command_log = install_ui.complex_run(sub_cmd)
      check_dirac_helpers.jobid_to_file(command_log, outfile)

      print("Submitting tag job for %s VO to %s" % (user_VO, site))
      outfile.write("Submitting tag job for %s VO to %s\n" % (user_VO, site))
      sub_cmd = ["dirac-wms-job-submit", "-f",
                 "jobs.log", "LCG.UKI-SOUTHGRID-RALPP.uk.tag.jdl"]
      command_log = install_ui.complex_run(sub_cmd)
      check_dirac_helpers.jobid_to_file(command_log, outfile)

    if site == "LCG.UKI-LT2-IC-HEP.uk":
      print("Submitting multicore job for %s VO to %s" % (user_VO, site))
      outfile.write("Submitting multicore job for %s VO to %s\n" % (user_VO, site))
      sub_cmd = ["dirac-wms-job-submit", "-f",
                 "jobs.log", "LCG.UKI-LT2-IC-HEP.uk.multi.jdl"]
      command_log = install_ui.complex_run(sub_cmd)
      check_dirac_helpers.jobid_to_file(command_log, outfile)

      print("Submitting EL7 job for %s VO to %s" % (user_VO, site))
      outfile.write("Submitting EL7 job for %s VO to %s\n" % (user_VO, site))
      sub_cmd = ["dirac-wms-job-submit", "-f",
                 "jobs.log", "LCG.UKI-LT2-IC-HEP.uk.el7.jdl"]
      command_log = install_ui.complex_run(sub_cmd)
      check_dirac_helpers.jobid_to_file(command_log, outfile)

      print("Submitting job requiring InputData for %s VO to %s\n" % (user_VO, site))
      outfile.write("Submitting job requiring InputData for %s VO to %s\n" % (user_VO, site))
      sub_cmd = ["dirac-wms-job-submit", "-f",
                 "jobs.log", "LCG.UKI-LT2-IC-HEP.uk.inputdata.jdl"]
      command_log = install_ui.complex_run(sub_cmd)
      check_dirac_helpers.jobid_to_file(command_log, outfile)

  outfile.close()

  # test API submission (currently basic implemetation only)
  wget_cmd_api = ["wget", "-np", "-O", "testapi.py",
                  "https://raw.githubusercontent.com/ic-hep/DIRAC-tools/master/check_dirac/grid_and_cloud_api_test.py"]
  install_ui.simple_run(wget_cmd_api)
  os.chmod("testapi.py", 0744)
  wget_cmd_aux = ["wget", "-np", "https://raw.githubusercontent.com/ic-hep/DIRAC-tools/master/user/testapi.sh"]
  install_ui.simple_run(wget_cmd_aux)
  sub_cmd_api = ["./testapi.py", user_VO]
  install_ui.simple_run(sub_cmd_api)

  # 7. Datamanagement: Test replicate and register (using FTS) function
  check_dirac_helpers.simple_run([os.path.join(working_dir, "repandreg.sh")])

  # 8. Closing statement
  print('\nTo check on the status of the test jobs, please do:')
  print('cd '+ working_dir)

  if os.path.isfile('bashrc'):
    print('source bashrc')
  elif install_type == "cvmfs":
    print('source /cvmfs/dirac.egi.eu/dirac/bashrc_gridpp_py3')
  else:
    print('source diracos/diracosrc')
  print('dirac-wms-job-status -f jobs.log')


if __name__ == "__main__":
  main()
