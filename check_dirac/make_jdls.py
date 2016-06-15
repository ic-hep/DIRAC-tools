#!/usr/bin/python

import os
import sys
import string
import re
from check_dirac_helpers import simple_run
from check_dirac_helpers import complex_run


JDLTEXT="""[
Executable = "gridpp.sh";
StdOutput = "job.log";
StdError = "job.log";
InputSandbox = "gridpp.sh";
OutputSandbox = "job.log";
ShallowRetryCount = 2;
Site = "%s";
JobName = "DiracTest";
]
"""

SHFILETEXT=r"""#!/bin/bash 
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

# use some CPU to prevent job getting killed for sitting idle
perl -e '$z=time()+(2*60); while (time()<$z) { $j++; $j *= 1.1 for (1..9999); }'

echo -e "\n"
echo -e "Any dirac stuff available ?"
dirac-dms-show-se-status

dirac-admin-get-site-mask

echo -e "\n"
echo -e "Downloading testfile (gridpptestfile.txt)"
dirac-dms-get-file /gridpp/user/dbauer/gridpptestfile.txt
cksum gridpptestfile.txt
# ideally this should be automated with some exit code (maybe later...)
echo -e "Expected: 2240404671 105 gridpptestfile.txt \n" 

echo -e "Creating a file, uploading it to gfe02"
MYDATE=`date +%%s`
env > testfile.${MYDATE}.txt
echo "File to be uploaded: " testfile.${MYDATE}.txt
dirac-dms-add-file -ddd /gridpp/user/%(DIRACUSERNAME)s/testfile.${MYDATE}.txt testfile.${MYDATE}.txt UKI-LT2-IC-HEP-disk
sleep 3
echo -e "\n"
echo "Testing dirac-dms-lfn-replicas command"
dirac-dms-lfn-replicas -ddd /gridpp/user/%(DIRACUSERNAME)s/testfile.${MYDATE}.txt
sleep 3
echo -e "\n" 
echo "Removing file"
dirac-dms-remove-files /gridpp/user/%(DIRACUSERNAME)s/testfile.${MYDATE}.txt
sleep 3

echo -e "\nI am done here."

"""

REPANDREGTEXT=r"""#!/bin/bash
echo "Testing the dirac-dms-replicate-and-register-request command"
MYDATE=`date +%%s`
env > repregtest.${MYDATE}.txt
echo "File to be uploaded: " repregtest.${MYDATE}.txt
dirac-dms-add-file /gridpp/user/%(DIRACUSERNAME)s/repregtest.${MYDATE}.txt repregtest.${MYDATE}.txt UKI-LT2-IC-HEP-disk
dirac-dms-replicate-and-register-request ddrarr_${MYDATE}  /gridpp/user/%(DIRACUSERNAME)s/repregtest.${MYDATE}.txt UKI-LT2-QMUL2-disk
echo "Sleeping 120 s to give replicate request a chance to finish."
sleep 120
echo -e "\n" 
echo "For reference the request name can be found in rep_and_reg_requests.txt"
echo "ddrarr_${MYDATE} /gridpp/user/%(DIRACUSERNAME)s/repregtest.${MYDATE}.txt" >> rep_and_reg_requests.txt
dirac-rms-show-request ddrarr_${MYDATE}

echo -e "\nPlease remeber to delete the file if transfer was sucess full or cancel the request if it wasn't:"
echo -e "dirac-dms-remove-files /gridpp/user/%(DIRACUSERNAME)s/repregtest.${MYDATE}.txt" 
echo -e "dirac-rms-cancel-request ddrarr_${MYDATE}"

echo -e "\nThe dirac-dms-replicate-and-register-request test script ends here."

"""


def make_jdls(sites_to_check):

  for site in sites_to_check:
    # jdl file name = sitename.jdl
    filename = site + ".jdl"
    dirac_sitename = "LCG." + site + ".uk"
    if site == "EFDA-JET":
      dirac_sitename = "LCG." + site + ".xx"
    jdlfile = open(filename, 'w')
    jdlfile.write(JDLTEXT % (dirac_sitename))
    jdlfile.close() # needed ?
    # after previous problems, make sure the InputData 
    # syntax still works (use Imperial only)
    if site == "UKI-LT2-IC-HEP":
      ic_jdl = open("UKI-LT2-IC-HEP.jdl", "r")
      contents = ic_jdl.readlines()
      ic_jdl.close()
      contents.insert(6, "InputData = {\"/gridpp/user/dbauer/gridpptestfile.txt\"};\n")
      ic_jdl = open("UKI-LT2-IC-HEP.jdl", "w")
      contents = "".join(contents)
      ic_jdl.write(contents)
      ic_jdl.close()


  proxycrap = complex_run(["dirac-proxy-info"])
              
  match = re.search(r'username\s+:\s+(.+)', proxycrap)
  if not match:
    print 'Cannot determine dirac user name. Something has gone terribly wrong.'
    sys.exit(0)

  if proxycrap.find("VOMS fqan") < 0:
    print 'This proxy does not seem to contain a VOMS fqan, must stop.'
    sys.exit(0)


  dirac_username = match.group(1)
  diracinfo = {"DIRACUSERNAME":dirac_username}                        

  # while I am at it, also make the .sh file
  grippshfile = open("gridpp.sh", 'w')
  grippshfile.write(SHFILETEXT %diracinfo)
  os.chmod("gridpp.sh", 0744)
  

  # file to test replicate and register command 
  diracrepandregfile = open("repandreg.sh", "w")
  diracrepandregfile.write(REPANDREGTEXT %diracinfo)
  os.chmod("repandreg.sh", 0744)
