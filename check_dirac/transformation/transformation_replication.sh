#!/bin/bash

#Upload random files to Imperial and tried to replicate to RALPP
# notes:
# dirac-transformation-cli
# get <transformation number>
# files are submitted in groups of 2
# so with 5 files one will be left over
# this should be processed once the transformation is cleaned

SOURCE_SE="UKI-LT2-IC-HEP-disk"
TARGET_SE="UKI-SOUTHGRID-RALPP-disk"

# what does the test filter actually do ?
usage="$(basename "$0") needs -test_filter option to be set:
Example:
$(basename "$0") -test_filter [True,False]"
if [[ $# -ne 2 ]]; then
  echo "$usage"
exit 1
fi

TestFilter="False"
if [[ "$1" = "-test_filter" ]]; then
   if [[ "$2" == "True" ]] || [[ "$2" == "False" ]]; then
     TestFilter=$2
   else
     echo "$usage"
     exit 1
   fi
fi

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# I can't use prod, this has to work with a VO proxy
# (or maybe later with a VO production proxy, but must be VO specific)
# The submitting user miust have the ProductionManagement Property

# echo "dirac-login dirac_prod"
# dirac-login dirac_prod
echo "dirac-proxy-init -g gridpp_user"
dirac-proxy-init -g gridpp_user
if [[ "${?}" -ne 0 ]]; then
   exit 1
fi

echo " "

#Values to be used
stime=$(date +"%H%M%S")
tdate=$(date +"20%y-%m-%d")
version=$(dirac-version)

if [[ -d "TransformationSystemTest" ]]; then
  echo "Removing TransformationSystemTest"
  rm -R TransformationSystemTest
fi

echo "Creating TransformationSystemTest"
mkdir -p TransformationSystemTest
directory=/gridpp/diracCertification/Test/INIT/$version/$tdate/$stime/replication

echo "Source: UKI-LT2-IC-HEP-disk"
echo "Target: UKI-SOUTHGRID-RALPP-disk"

# Create unique files"
echo ""
echo "Creating unique test files"
"${SCRIPT_DIR}/random_files_creator.sh" --Files=5 --Name="Test_Transformation_System_" --Path=$PWD/TransformationSystemTest

# Add the random files to the transformation
echo ""echo "Adding files to Storage Element ${SOURCE_SE}"
filesToUpload=$(ls TransformationSystemTest/)
for file in $filesToUpload
do
  echo "$directory/$file ./TransformationSystemTest/$file ${SOURCE_SE}" >> TransformationSystemTest/LFNlist.txt
done

echo "Uploading files, see TransformationSystemTest/upload.log"
dirac-dms-add-file TransformationSystemTest/LFNlist.txt -ddd &> TransformationSystemTest/upload.log

cat TransformationSystemTest/LFNlist.txt | awk '{print $1}' | sort > ./LFNstoTS.txt

echo "Checking if files have been uploaded..."
dirac-dms-lfn-replicas ./LFNstoTS.txt | grep "No such file"
# grep returns 1 if it cannot find anything, if we cannot find "No such file" we successfully uploaded all files
if [[ "${?}" -ne 1 ]]; then
    echo "Failed to upload all files, please check"
    exit 1
fi
echo "...files successfully uploaded"

echo ""
echo "Submitting test production"
dirac-transformation-replication 0 ${TARGET_SE} -G 2 -ddd -N replication_${version}_${tdate}_${stime} --Enable | tee TransformationSystemTest/trans.log
if [[ "${?}" -ne 0 ]]; then
    echo "Failed to create transformation"
    exit 1
fi

transID=$(grep "Created transformation" TransformationSystemTest/trans.log | sed "s/.*Created transformation //")
echo "Adding files to transformation ${transID}"
if [[ $TestFilter == "False" ]]; then
  echo ""
  echo "Adding the files to the test production"
  dirac-transformation-add-files $transID LFNstoTS.txt
  if [[ "${?}" -ne 0 ]]; then
    exit 1
  fi
fi

echo ""
echo "Checking if the files have been added to the transformation"
dirac-transformation-get-files ${transID} | sort > ./transLFNs.txt
diff --ignore-space-change LFNstoTS.txt transLFNs.txt
if [[ "${?}" -ne 0 ]]
then
  echo 'Error: files have not been  added to the transformation'
  exit 1
else
  echo 'Successful check'
fi
