#!/usr/bin/env python3
"""
Main program for checking the status of dirac01.
Installs a fresh UI and submits jobs to a variety of sites
(HTCondorCE, ARC) using the selected VO. Also tried to replicate
and register a file.
"""
import os
import sys
import install_ui
import make_jdls
import check_dirac_helpers


def main():
  """This is where all the action is. """
  print("Welcome to the basic dirac test script.")
  print("Please make sure you are using an EL7,8 or 9 compatible machine.")
  print("You will also need a valid user certificate in $HOME/.globus \n")

  # 0. Sanity checks
  check_dirac_helpers.check_prerequisites()

  # 1. Setup a UI
  # pick which VO to test, default: gridpp
  print("Which VO do you want to test (default: gridpp) ?")
  user_VO = input("Your choices are: gridpp, lz, lsst, solidexperiment.org, skatelescope.eu: ") \
            or "gridpp"
  if user_VO not in ["gridpp", "lz", "lsst", "solidexperiment.org", "skatelescope.eu"]:
    print(f"Testing for {user_VO} VO is not supported.")
    sys.exit(0)

  # use cvmfs ui or install local one, default: local
  install_type = input("Install new local UI or use cvmfs (default: local)? Please enter: 'local'/'cvmfs': ") \
                 or "local"
  if install_type not in ["local", "cvmfs"]:
    print(f"WARNING: install_type {install_type} not known, proceeding with local install.")
    install_type = "local"

  install_ui.setup_ui(user_VO, install_type)

  # 2. Select Sites and make JDLs
  # aiming for good UK coverage, ARC and HTCondor
  sites_to_check = ["LCG.UKI-LT2-IC-HEP.uk",
                    "LCG.UKI-LT2-QMUL.uk",
                    "LCG.UKI-LT2-Brunel.uk",
                    "LCG.UKI-NORTHGRID-LANCS-HEP.uk"
                    "LCG.UKI-NORTHGRID-LIV-HEP.uk",
                    "LCG.UKI-SCOTGRID-GLASGOW.uk",
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
  outfile_name = os.path.join(working_dir, "sites.log")

# 6. Job Submission
  outfile = open(outfile_name, "a", encoding="utf-8")

  for site in sites_to_check:

    jdlfile = site + ".jdl"
    print(site)

    sub_cmd = ["dirac-wms-job-submit", "-f", "jobs.log", jdlfile]
    outfile.write(f"Submitting standard job to {site}\n")
    command_log = install_ui.complex_run(sub_cmd)
    check_dirac_helpers.jobid_to_file(command_log, outfile)

    # now all the special cases (all these sites also receive a standard test job)
    # all special cases run either at RALPP or Imperial

    if site == "LCG.UKI-SOUTHGRID-RALPP.uk":
      print(f"Submitting multicore job for {user_VO} VO to {site}")
      outfile.write(f"Submitting multicore job for {user_VO} VO to {site}\n")
      sub_cmd = ["dirac-wms-job-submit", "-f",
                 "jobs.log", "LCG.UKI-SOUTHGRID-RALPP.uk.multi.jdl"]
      command_log = install_ui.complex_run(sub_cmd)
      check_dirac_helpers.jobid_to_file(command_log, outfile)

    if site == "LCG.UKI-LT2-IC-HEP.uk":
      print(f"Submitting multicore job for {user_VO} VO to {site}")
      outfile.write(f"Submitting multicore job for {user_VO} VO to {site}\n")
      sub_cmd = ["dirac-wms-job-submit", "-f",
                 "jobs.log", "LCG.UKI-LT2-IC-HEP.uk.multi.jdl"]
      command_log = install_ui.complex_run(sub_cmd)
      check_dirac_helpers.jobid_to_file(command_log, outfile)

      print(f"Submitting EL7 job for {user_VO} VO to {site}")
      outfile.write(f"Submitting EL7 job for {user_VO} VO to {site}\n")
      sub_cmd = ["dirac-wms-job-submit", "-f",
                 "jobs.log", "LCG.UKI-LT2-IC-HEP.uk.el7.jdl"]
      command_log = install_ui.complex_run(sub_cmd)
      check_dirac_helpers.jobid_to_file(command_log, outfile)

      print(f"Submitting job requiring InputData for {user_VO} VO to {site}\n")
      outfile.write(f"Submitting job requiring InputData for {user_VO} VO to {site}\n")
      sub_cmd = ["dirac-wms-job-submit", "-f",
                 "jobs.log", "LCG.UKI-LT2-IC-HEP.uk.inputdata.jdl"]
      command_log = install_ui.complex_run(sub_cmd)
      check_dirac_helpers.jobid_to_file(command_log, outfile)

      print(f"Submitting tag (GPU) job for {user_VO} VO to {site}")
      outfile.write(f"Submitting tag (GPU) job for {user_VO} VO to {site}\n")
      sub_cmd = ["dirac-wms-job-submit", "-f",
                 "jobs.log", "LCG.UKI-LT2-IC-HEP.uk.tag.jdl"]
      command_log = install_ui.complex_run(sub_cmd)
      check_dirac_helpers.jobid_to_file(command_log, outfile)


  outfile.close()

  # test API submission (currently basic implemetation only)
  wget_cmd_api = ["wget", "-np", "-O", "testapi.py",
                  "https://raw.githubusercontent.com/ic-hep/DIRAC-tools/master/check_dirac/grid_and_cloud_api_test.py"]
  install_ui.simple_run(wget_cmd_api)
  os.chmod("testapi.py", 0o744)
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
    print('source /cvmfs/dirac.egi.eu/dirac/bashrc_gridpp')
  else:
    print('source diracos/diracosrc')
  print('dirac-wms-job-status -f jobs.log')


if __name__ == "__main__":
  main()
