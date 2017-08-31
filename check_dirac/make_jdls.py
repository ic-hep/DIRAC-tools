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
JobName = "DiracTest";
]
"""

SHFILETEXT = r"""#!/bin/bash 
date 
pwd 
sleep 2
echo -e "\n Checking the environment \n"
ghostname=`hostname --long 2>&1` 
gipname=`hostname --ip-address 2>&1` 
echo $ghostname "has address" $gipname
uname -a
cat /etc/redhat-release
env | sort

echo -e " \n ================================== \n"

# **** who am i ***
dirac-proxy-info

echo -e " \n"
ISITVAC=${DIRACSITE:0:3}

if [ "$ISITVAC" == "VAC" ]; then
  echo "This is a VAC site"
  echo "Listing content of \$DIRACROOT/etc/dirac.cfg"
  cat ${DIRACROOT}/etc/dirac.cfg
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

echo -e "Creating a file, uploading it to gfe02"
MYDATE=`date +%%s`
# for running within a UI
if [ -z "${DIRACSITE}" ]; then
  DIRACSITE=`hostname` 
fi
env > testfile.${MYDATE}.${DIRACSITE}.txt
echo "File to be uploaded: " testfile.${MYDATE}.${DIRACSITE}.txt
dirac-dms-add-file -ddd /%(VO)s/user/%(DIRACUSERNAME)s/testfile.${MYDATE}.${DIRACSITE}.txt testfile.${MYDATE}.${DIRACSITE}.txt UKI-LT2-IC-HEP-disk
sleep 3
echo -e "\n"
echo "Testing dirac-dms-lfn-replicas command"
dirac-dms-lfn-replicas -ddd /%(VO)s/user/%(DIRACUSERNAME)s/testfile.${MYDATE}.${DIRACSITE}.txt
sleep 3
echo -e "\n" 
echo "Removing file"
dirac-dms-remove-files /%(VO)s/user/%(DIRACUSERNAME)s/testfile.${MYDATE}.${DIRACSITE}.txt
sleep 3

echo -e "\nI am done here."

"""

REPANDREGTEXT = r"""#!/bin/bash
echo "Testing the dirac-dms-replicate-and-register-request command"
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
echo -e "dirac-rms-cancel-request ddrarr_${MYDATE}"

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
    jdlfile.write(JDLTEXT % (site))
    jdlfile.close() # needed ?
    # after previous problems, make sure the InputData 
    # syntax still works (use Imperial only)
    if site == "LCG.UKI-LT2-IC-HEP.uk":
      ic_jdl = open("LCG.UKI-LT2-IC-HEP.uk.jdl", "r")
      contents = ic_jdl.readlines()
      ic_jdl.close()
      # VO specific input data
      inputdatastring = "InputData = {\"/%s/user/dirac01.test/dirac01.testfile.txt\"};\n" % user_VO
      # print inputdatastring
      contents.insert(6, inputdatastring)
      

      ic_jdl = open("LCG.UKI-LT2-IC-HEP.uk.jdl", "w")
      contents = "".join(contents)
      ic_jdl.write(contents)
      ic_jdl.close()


  # this has moved to install_ui.install_ui()    
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

