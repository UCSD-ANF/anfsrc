#!/bin/bash

### Static configuration variables
### (addtional variables are loaded from a parameter file)

# Parameter file name to search for additional configuration
PFNAME="common"

# Filename prefix for generated movies
PROJECT_PREFIX="USArray_"

# temporary output and working directory
TMPDIR="/tmp/mk_deployment_movies.$$"

# list of deployment and history types
DEPLOYTYPES="seismic inframet"
HISTTYPES="cumulative rolling"

### The following variables are set in load_pf_globals
# Directory where map images are located
declare -A MAPDIR
# Prefix to map image file
declare -A MAPPREFIX
# Directory where movie files are located
declare -A MOVDIR
# Prefix to movie file
declare -A MOVPREFIX

### Functions

# pfghetto
#
# Work around broken pfecho -q
# gets a single pf key and returns it, stripping the key name off.
# It's needed because pfecho -q doesn't replace variable references, but
# pfecho without the -q option does
#
# For example:
#
#     $ pfecho -q common CACHEIMAGES
#     &{WEBROOT}/cacheimages
#     $ pfecho common CACHEIMAGES
#     CACHEIMAGES     /anf/web/vhosts/anf.ucsd.edu/htdocs/cacheimages
#
# Note how the value of CACHEIMAGES has expanded in the second command.
# Hence this cheesy wrapper.
function pfghetto {
  local pfname=$1
  local key=$2

  pfecho $pfname $key | sed "s/^${key}[ \t]*//"
}

# This function creates a directory full of images in jpg format named
# sequentially which can then be passed to the movie encoder
# Originally, we tried keeping the images in png format and symlinking,
# but ffmpeg didn't like working with PNG.
function create_stills {

  #echo TMPDIR is $TMPDIR

  local dt=$1 # one of seismic, inframet
  local ht=$2 # one of cumulative, rolling

  # Verify tempdir exists
  if ! [ -d $TMPDIR ]; then
    elog -l MAKING TMPDIR
    mkdir -p $TMPDIR;
  fi

  local x=1
  local imagefile

  echo -n Creating temporary still images 1>&2

  for imagefile in $( ls ${MAPDIR[$dt]}/${MAPPREFIX[$dt]}*.$ht.png | sort ); do
    local counter=$(printf %03d $x)
    local outfilep=$TMPDIR/img"$counter"
    local outfile

    outfile=$outfilep.jpg
    #echo Converting $imagefile to $outfile
    echo -n . 1>&2 # spit out a progress dot for each image
    convert -quality 100 $imagefile $outfile
    if [ ! $? ]; then
      elog -c "ERROR: converting files from png to jpg failed for source file $imagefile, dest $outfile"
      return 1
    fi

    x=$(($x+1))
  done

  echo "done" 1>&2
  return 0
}

function remove_stills {
  # Deployment type, seismic or inframet
  local dt=$1
  # ht is either cumulative or rolling
  local ht=$2
  # ft - file type, always jpg
  local ft=jpg

  rm -f $TMPDIR/img*.$ft
}

function mk_movies {
  # Deployment type, seismic or inframet
  local dt=$1
  # ht is either cumulative or rolling
  local ht=$2
  # ft - file type - always jpg now
  local ft=jpg

  mk_android_movie $dt $ht $ft || return $?
  mk_qt_movie $dt $ht $ft || return $?
  mk_iphone_movie $dt $ht $ft || return $?
  return 0
}

function mk_android_movie {
  local dt=$1 ht=$2 ft=$3
  local fname="${PROJECT_PREFIX}${MOVPREFIX[$dt]}${YEAR}_${MONTH}_android.${ht}.mp4"

  ffmpeg -r 2 -qscale 1 \
    -i $TMPDIR/img%03d.$ft \
    -r 6 -s 320x240 \
    "$TMPDIR/$fname" && \
    mv -f "$TMPDIR/$fname" "${MOVDIR[$dt]}/$fname"
  return $?
}

function mk_qt_movie {
  local dt=$1 ht=$2 ft=$3
  local fname="${PROJECT_PREFIX}${MOVPREFIX[$dt]}${YEAR}_${MONTH}_qt.${ht}.mov"


  ffmpeg -r 2 -qscale 5 \
    -i $TMPDIR/img%03d.$ft \
    -r 6 \
    $TMPDIR/$fname && \
    mv -f "$TMPDIR/$fname" "${MOVDIR[$dt]}/$fname"
  return $?
}

function mk_iphone_movie {
  local dt=$1 ht=$2 ft=$3
  local fname="${PROJECT_PREFIX}${MOVPREFIX[$dt]}${YEAR}_${MONTH}_iphone.${ht}.m4v"


  # We have to manually specify the -vcodec on linux because we have to
  # provide -vpre medium when making m4v files. Works ok without
  # -vcodec and -vpre on Darwin with macports ffmpeg
  ffmpeg -r 2 -qscale 1 \
    -i $TMPDIR/img%03d.$ft \
    -vcodec libx264 -vpre medium -s 480:320 \
    "$TMPDIR/$fname" && \
    mv -f "$TMPDIR/$fname" "${MOVDIR[$dt]}/$fname"
  return $?
}

function cleanup {
  rm -rf $TMPDIR
}

# Gets the current month and year, calculates the previous month and
# year, then sets the global variables YEAR and MONTH to the previous
# year and month, with MONTH zero padded to two digits
function set_prev_year_month {
  # Numeric representation of the year and month
  tyear=$(date +%Y)
  tmonth=$(date +%m | sed 's/^0//') # strip leading 0

  tmonth=$(($tmonth - 1))
  if [ $tmonth -eq 0 ]; then
    tmonth=12
    tyear=$(($curyear - 1))
  fi

  YEAR=$(printf '%04d' $tyear)
  MONTH=$(printf '%02d' $tmonth)

  unset tyear tmonth
}

function validate_pf {
  local mypfname=$1
  if [ "$(pfecho -w $mypfname)" != '' ] ; then return 0; fi
  elog -c "Can't find parameter file \"$mypfname\""
  return 1
}

function load_pf_globals {
  # Directory where map images are located
  MAPDIR["seismic"]=$(pfghetto $PFNAME CACHE_MONTHLY_DEPLOYMENT)
  MAPDIR["inframet"]=$(pfghetto $PFNAME CACHE_MONTHLY_DEPLOYMENT_INFRA)

  # Prefix to map image file
  MAPPREFIX["seismic"]="deploymap_"
  MAPPREFIX["inframet"]="deploymap_inframet_"

  # Directory where movie files are located
  MOVDIR["seismic"]=$(pfghetto $PFNAME CACHE_MOV_MONTHLY_DEPLOYMENT)
  MOVDIR["inframet"]=$(pfghetto $PFNAME CACHE_MOV_MONTHLY_DEPLOYMENT_INFRA)

  # Prefix to movie file
  MOVPREFIX["seismic"]="deployment_"
  MOVPREFIX["inframet"]="inframet_deployment_"

  return 0
}


### Main ###

elog -n $0 starting
validate_pf $PFNAME || exit 1

load_pf_globals

### load parameters from parameter file

# Since this script is intended to run at the beginning of the month
# after the monthly image generation script, it will only have images
# up to the end of the last month to work with.
set_prev_year_month

for d in $DEPLOYTYPES; do
  for h in $HISTTYPES; do
    elog -n "Processing $d $h"
    create_stills $d $h && \
    mk_movies $d $h && \
    remove_stills $d $h
  done
done

res=$?
if [ $res ]; then
  cleanup
  elog -n $0 finished successfully
else
  elog -c "an error occured, skipping cleanup"
fi
exit $res
