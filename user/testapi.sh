#!/bin/bash
date
pwd
sleep 2
echo -e "\nChecking the environment \n"
ghostname=`hostname --long 2>&1`
gipname=`hostname --ip-address 2>&1`
echo $ghostname "has address" $gipname
uname -a
cat /etc/redhat-release
env | sort

echo -e " \n ================================== \n"

# **** who am i ***
dirac-proxy-info


which nvidia-smi 2> /dev/null
if [ $? == 0 ]; then 
    echo -e "Checking for GPUs"
    nvidia-smi
    echo -e "****"
fi

echo "All Arguments: $@"
echo -e "Checking for input parameter"
echo "Is it magic ?"
echo $1

echo "End of script"

