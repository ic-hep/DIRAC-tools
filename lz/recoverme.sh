#!/bin/bash

# input is of type LFN: /lz/data/MDC3/background/BACCARAT-4.11.0_DER-8.5.13/20180401/lz_201804010002_000172_035741_raw.root
# TODO: As theses files need to be registered, output should be of type
# srm://gfe02.grid.hep.ph.ic.ac.uk/pnfs/...
# so I put that in, but didn't test it
# It's Christmas.
lfiles=`cat doomedfiles_tryagain.txt`

for f in $lfiles
do
    echo $f
    gfal-ls gsiftp://dtn02.nersc.gov/projecta/projectdirs${f}
    if [ $? == 0 ]; then
	echo "Trying to recover $f"
	gfal-copy -f gsiftp://dtn02.nersc.gov/projecta/projectdirs${f} /pnfs/hep.ph.ic.ac.uk/data/lz${f}
	if [ $? == 0 ]; then
	   echo "${f} sucessfully recovered, getting chksum and size"
	   chksum=`adler32 /pnfs/hep.ph.ic.ac.uk/data/lz${f}`
	   size=`stat --format=%s /pnfs/hep.ph.ic.ac.uk/data/lz${f}`
	   echo "Got the full set"
	   echo "srm://gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/lz${f}    ${chksum}    ${size}" >> recovered_files.txt
	else
	    echo "Something went wrong with ${f}"
	    echo "${f}" >> possiblydoomed.txt
	fi
    else
	echo "File ${f} truly lost"
	echo "${f}" >> doomedfiles.txt
    fi
done


    
