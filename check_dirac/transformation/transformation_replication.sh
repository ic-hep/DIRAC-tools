#!/bin/bash

# Upload random files to Imperial and tried to replicate to RALPP
# adapted from "DIRAC/tests/System/transformation_replication.sh -test_filter False"
# notes:
# We are currently using:
# ./transformation_replication.sh t2k.org_user
# dirac-transformation-cli
# get <transformation number>
# files are submitted in groups of 2
# so with 5 files one will be left over
# this should be processed once the transformation is cleaned
# needs random_files_creator.sh in the same directory

SOURCE_SE="UKI-LT2-IC-HEP-disk"
TARGET_SE="UKI-SOUTHGRID-RALPP-disk"

# do some checks
if [ "$#" -lt 1 ]; then
    echo "Usage: ./transformation_replication.sh dirac_group_name, e.g: ./transformation_replication.sh gridpp_user"
    exit 0
fi

if [ -z "$DIRACOS" ]
then
  echo "DIRACOS not set. Did you forget to set up/activate a DIRAC UI ?"
  exit 0
fi

if [ ! -f "random_files_creator.sh" ] && [ ! -L "random_files_creator.sh" ]
then
  echo "This script relies on DIRAC/tests/System/random_files_creator.sh being present in the same directory."
  exit 0
fi

user_vo=$(echo $1 | cut -d_ -f1)


# what does the test filter actually do ?
# it's currently hardcoded to: -test_filter False
#usage="$(basename "$0") needs -test_filter option to be set:
#Example:
#$(basename "$0") -test_filter [True,False]"
#if [[ $# -ne 2 ]]; then
#  echo "$usage"
#exit 1
#fi

TestFilter="False"
#if [[ "$1" = "-test_filter" ]]; then
#   if [[ "$2" == "True" ]] || [[ "$2" == "False" ]]; then
#     TestFilter=$2
#   else
#     echo "$usage"
#     exit 1
#   fi
#fi

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# I can't use prod, this has to work with a VO proxy
# (or maybe later with a VO production proxy, but must be VO specific)
# The submitting user miust have the ProductionManagement Property

# echo "dirac-login dirac_prod"
# dirac-login dirac_prod
echo "dirac-proxy-init -g $1"
dirac-proxy-init -g $1
if [[ "${?}" -ne 0 ]]; then
   exit 1
fi

echo " "

# bad hack to get the dirac user name
# this is what happens when you try to make
# this script available to different people
# quickly
# I hang my head in shame
user_name=`dirac-proxy-info | grep username | cut -d: -f2 | xargs`

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
directory=/${user_vo}/user/${user_name:0:1}/${user_name}/transformationCertification/Test/INIT/$version/$tdate/$stime/replication

echo "Source SE: $SOURCE_SE"
echo "Target SE: $TARGET_SE"
echo "Trying to write to $directory"

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

echo "====================================="
echo "This script has finished."
echo "Your transformation id is: ${transID}"
echo "You can check on your transformation using:"
echo "dirac-transformation-cli"
echo "get ${transID}"
