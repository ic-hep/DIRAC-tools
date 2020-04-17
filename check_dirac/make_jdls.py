#!/usr/bin/python
"""
generates the JDL and .sh files needed for the test
"""
import os
import sys
import re
from check_dirac_helpers import complex_run


JDLTEXT = """[
Executable = "diractest.sh";
StdOutput = "job.log";
StdError = "job.log";
InputSandbox = "diractest.sh";
OutputSandbox = "job.log";
Site = "%s";
JobName = "%s";
Platform = "%s";
%s
]
"""

SHFILETEXT = r"""#!/bin/bash
date
pwd
sleep 2
echo -e "\nChecking the environment \n"
echo $DIRACSITE
ghostname=`hostname --long 2>&1`
gipname=`hostname --ip-address 2>&1`
echo $ghostname "has address" $gipname
uname -a
cat /etc/redhat-release
env | sort

# make a summary later
TESTDOWNLOAD="Failed: Please check log for errors."
TESTUPLOAD="Failed: Please check log for errors."
TESTREMOVE="Failed: Please check log for errors."
TESTLISTLFN="Failed: Please check log for errors."

echo -e " \n ================================== \n"

# **** who am i ***
dirac-proxy-info

echo -e " \n"
ISITVAC=${DIRACSITE:0:3}

if [ "$ISITVAC" == "VAC" ]; then
  echo "This is a VAC site"
  echo "Listing content of \$DIRACROOT/etc/dirac.cfg"
  cat ${DIRACROOT}/etc/dirac.cfg
  echo -e "==========\n"
fi


# use some CPU to prevent job getting killed for sitting idle
perl -e '$z=time()+(2*60); while (time()<$z) { $j++; $j *= 1.1 for (1..9999); }'

echo -e "\n"
echo -e "Any dirac stuff available (dirac-version, dirac-admin-get-site-mask) ?"
dirac-version
dirac-admin-get-site-mask

echo -e "\n"
echo -e "Downloading testfile (/%(VO)s/user/dirac01.test/dirac01.testfile.txt)"
dirac-dms-get-file /%(VO)s/user/dirac01.test/dirac01.testfile.txt
cksum dirac01.testfile.txt
# ideally this should be automated with some exit code (maybe later...)
echo -e "Expected: 2240404671 105 dirac01.testfile.txt \n" 
TESTCHKSUM=`cksum dirac01.testfile.txt | awk {'print $1'}`
if [ ! -z ${TESTCHKSUM} ]; then 
    if [ $TESTCHKSUM == 2240404671 ]; then
        TESTDOWNLOAD="Success"
    else 
        echo "Unexpected checksum found: ${TESTCHKSUM}"
    fi
fi

echo -e "Creating a file, uploading it to gfe02"
MYDATE=`date +%%s`
# for running within a UI
if [ -z "${DIRACSITE}" ]; then
  DIRACSITE=`hostname` 
fi
env > testfile.${MYDATE}.${DIRACSITE}.txt
echo "File to be uploaded: " testfile.${MYDATE}.${DIRACSITE}.txt
dirac-dms-add-file -ddd /%(VO)s/user/%(DIRACUSERNAME)s/testfile.${MYDATE}.${DIRACSITE}.txt testfile.${MYDATE}.${DIRACSITE}.txt UKI-LT2-IC-HEP-disk 2>&1 | tee dmsaddlog.${MYDATE}.txt
# prepare summary
if [ $? == 0 ];then 
    ISITGOOD=`grep "Successfully uploaded file to" dmsaddlog.${MYDATE}.txt | wc -l`
    echo $ISITGOOD
    if [ $ISITGOOD == 1 ];then
	TESTUPLOAD="Success"
    fi
fi

sleep 3
echo -e "\n"
echo "Testing dirac-dms-lfn-replicas command"
dirac-dms-lfn-replicas -ddd /%(VO)s/user/%(DIRACUSERNAME)s/testfile.${MYDATE}.${DIRACSITE}.txt 2>&1 | tee dmslfnrep.${MYDATE}.txt 

if [ $? == 0 ];then 
    ISITGOOD=`grep "'Failed': {}}}" dmslfnrep.${MYDATE}.txt | wc -l`
    if [ $ISITGOOD == 1 ];then
	TESTLISTLFN="Success"
    fi
fi

sleep 3
echo -e "\n" 
echo "Removing file"
dirac-dms-remove-files /%(VO)s/user/%(DIRACUSERNAME)s/testfile.${MYDATE}.${DIRACSITE}.txt 2>&1 | tee dmsremove.${MYDATE}.txt
if [ $? == 0 ];then 
    ISITGOOD=`grep "Successfully removed" dmsremove.${MYDATE}.txt | wc -l`
    if [ $ISITGOOD == 1 ];then
	TESTREMOVE="Success"
    fi
fi

sleep 3

echo -e "\nSummary:\n"
echo ${DIRACSITE}
if [ "${DIRACSITE}" == "LCG.UKI-LT2-IC-HEP.uk" ] || [ "${DIRACSITE}" == "LCG.UKI-SOUTHGRID-RALPP.uk" ];then
     echo "NSLOTS=${NSLOTS}"
     echo "OMP_NUM_THREADS=${OMP_NUM_THREADS}"
fi
echo "File download: ${TESTDOWNLOAD}"
echo "File upload: ${TESTUPLOAD}"
echo "List LFN: ${TESTLISTLFN}"
echo "File remove: ${TESTREMOVE}"

echo -e "\nI am done here."

"""

REPANDREGTEXT = r"""#!/bin/bash
echo -e "\nTesting the dirac-dms-replicate-and-register-request command"
MYDATE=`date +%%s`
env > repregtest.${MYDATE}.txt
echo "File to be uploaded: " repregtest.${MYDATE}.txt
dirac-dms-add-file /%(VO)s/user/%(DIRACUSERNAME)s/repregtest.${MYDATE}.txt repregtest.${MYDATE}.txt UKI-LT2-IC-HEP-disk
dirac-dms-replicate-and-register-request ddrarr_${MYDATE}  /%(VO)s/user/%(DIRACUSERNAME)s/repregtest.${MYDATE}.txt %(TARGETSE)s
echo "Sleeping 120 s to give replicate request a chance to finish."
sleep 120
echo -e "\n" 
echo "For reference the request name can be found in rep_and_reg_requests.txt"
echo "ddrarr_${MYDATE} /%(VO)s/user/%(DIRACUSERNAME)s/repregtest.${MYDATE}.txt" >> rep_and_reg_requests.txt
%(SHOWCMD)s ddrarr_${MYDATE}

echo -e "\nPlease remeber to delete the file if transfer was sucess full or cancel the request if it wasn't:"
echo -e "dirac-dms-remove-files /%(VO)s/user/%(DIRACUSERNAME)s/repregtest.${MYDATE}.txt" 
echo -e "dirac-rms-request --Cancel ddrarr_${MYDATE}"

echo -e "\nThe dirac-dms-replicate-and-register-request test script ends here."

"""


def make_jdls(user_VO, sites_to_check):
  """
  generates the JDL and .sh files needed for the test
  """

  for site in sites_to_check:
    # jdl file name = sitename.jdl
    filename = site + ".jdl"
    jdlfile = open(filename, 'w')
    jobname = "DiracTest" # default
    platform = "AnyPlatform" # default
    special_requirement = '' #default
    jdlfile.write(JDLTEXT % (site, jobname, platform, special_requirement))
    jdlfile.close()

    if site == "LCG.UKI-LT2-IC-HEP.uk":
      # there are three extra test cases for Imperial:
      # 1) standard test, plus InputData requirement
      filename = site + ".inputdata.jdl"
      jdlfile_special = open(filename, 'w')
      jobname = "DiracTestInputData"
      special_requirement = "InputData = {\"/%s/user/dirac01.test/dirac01.testfile.txt\"};\n" % user_VO
      jdlfile_special.write(JDLTEXT % (site, jobname, platform, special_requirement))
      jdlfile_special.close()
      # 2) standard test, plus multiprocessor (to be merged with 3 once we only have htcondor CEs)
      filename = site + ".multi.jdl"
      jdlfile_special = open(filename, 'w')
      jobname = "DiracTestMulti"
      special_requirement = "Tags = {\"8Processors\"};\n"
      jdlfile_special.write(JDLTEXT % (site, jobname, platform, special_requirement))
      jdlfile_special.close()
      # 3) standard test, plus multiprocessor on htcondor CEs
      filename = site + ".multi.htcondor.jdl"
      jdlfile_special = open(filename, 'w')
      jobname = "DiracTestMulti"
      special_requirement = "Tags = {\"8Processors\"};\nGridCE = {\"ceprod00.grid.hep.ph.ic.ac.uk\"};\n"
      jdlfile_special.write(JDLTEXT % (site, jobname, platform, special_requirement))
      jdlfile_special.close()
      # 4) check that setting the Platform does not break job submission/matching
      filename = site + ".el7.jdl"
      jdlfile_special = open(filename, 'w')
      jobname = "DiracTestPlatform"
      platform = "EL7"
      special_requirement = ""
      jdlfile_special.write(JDLTEXT % (site, jobname, platform, special_requirement))
      jdlfile_special.close()

    if site == "LCG.UKI-SOUTHGRID-RALPP.uk":
      platform = "AnyPlatform"
      # there are two extra test cases for RALPP
      # 1) test the tagging mechanism: HighMem queue at RALPP (should run at heplnx207)
      filename = site + ".tag.jdl"
      jdlfile_special = open(filename, 'w')
      jobname = "DiracTestTag"
      special_requirement = "Tags = {\"HighMem\"};\n"
      jdlfile_special.write(JDLTEXT % (site, jobname, platform, special_requirement))
      jdlfile_special.close()
      # 2) test multi-core on ARC
      filename = site + ".multi.jdl"
      jdlfile_special = open(filename, 'w')
      jobname = "DiracTestMulti"
      special_requirement = "Tags = {\"8Processors\"};\n"
      jdlfile_special.write(JDLTEXT % (site, jobname, platform, special_requirement))
      jdlfile_special.close()

  proxycrap = complex_run(["dirac-proxy-info"])
  # at this point, the proxy has already been verified
  # so proxycrap should always be OK, but still do basic check
  match = re.search(r'username\s+:\s+(.+)', proxycrap)
  if not match:
    print 'It should have never come that far.'
    sys.exit(0)
  dirac_username = match.group(1)

  # files for solidexperiment.org can only be replicated to and from Belgium
  targetse = "UKI-LT2-QMUL2-disk"
  if user_VO == "solidexperiment.org":
    targetse = "BEgrid-ULB-VUB-disk"
  diracinfo = {}

  # there used to be an if here...
  diracinfo = {"DIRACUSERNAME":dirac_username, "VO":user_VO, "TARGETSE":targetse, "SHOWCMD":"dirac-rms-request"}


  # while I am at it, also make the .sh file
  diractestshfile = open("diractest.sh", 'w')
  diractestshfile.write(SHFILETEXT %diracinfo)
  os.chmod("diractest.sh", 0744)
  

  # file to test replicate and register command 
  diracrepandregfile = open("repandreg.sh", "w")
  diracrepandregfile.write(REPANDREGTEXT %diracinfo)
  os.chmod("repandreg.sh", 0744)


# for testing, where's travis when you need it
# make_jdls("lsst", ["LCG.UKI-LT2-IC-HEP.uk", "LCG.UKI-LT2-QMUL.uk"])

