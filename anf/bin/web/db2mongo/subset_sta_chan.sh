#!/bin/bash

#cmd="dbsubset /anf/TA/dbs/dbmaster/usarray.stage '(iunits !~ /V/ && ounits =~ /V/) || gtype =~ /wxt.*/' |"
cmd="dbsubset /anf/TA/dbs/dbmaster/usarray.stage 'gtype !~ /digitizer|Q330.*|FIR.*/' |"


cmd+="dbjoin -o - :sta :chan :stage.time#calibration.time::calibration.endtime calibration |"

cmd+="dbjoin -o - snetsta |"

if [[ -n $2 ]]
then
    cmd+="dbsubset - 'sta =~/$1/ && chan =~/$2/' |"
elif [[ -n $1 ]]
then
    cmd+="dbsubset - 'sta =~/$1/' |"
fi


cmd+="dbsort - sta chan time |"

if [[ -n $3 ]]
then
    cmd+=$3
else
    cmd+="dbselect -h - sta chan 'strdate(time)' 'strdate(endtime)'  segtype ssident calibration.insname snname dlname"
fi

echo
echo $cmd;
echo
echo

eval $cmd;
