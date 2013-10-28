#!/bin/bash
 
# For WWW-239
# This script regenerates the deployment maps for the specified months and places the images
# in the proper directory
 
# Usage:
# Edit the section below MAIN to include the maps you want to generate
 
# Must be run from www rtsystem on anfwebproc
cd ~rt/rtsystems/www
 
#smdir=/anf/web/vhosts/anf.ucsd.edu/htdocs/cacheimages/maps/monthly_deployment
#imdir=/anf/web/vhosts/anf.ucsd.edu/htdocs/cacheimages/maps/monthly_deployment_inframet
 
function make_year_month {
    year=$1
    month=$2
 
    # seismic cumulative
    echo Making seismic cumulative for $year $month
    bin/deployment_history/usarray_deploy_map.py -t cumulative \
    -d seismic $year $month 
 
    # seismic rolling
    echo Making seismic rolling for $year $month
    bin/deployment_history/usarray_deploy_map.py -t rolling \
    -d seismic $year $month 
}
 
function make_year_month_infra {
    year=$1
    month=$2
 
    # inframet cumulative
    echo Making inframet cumulative for $year $month
    bin/deployment_history/usarray_deploy_map.py -t cumulative \
    -d inframet $year $month
 
    # inframet rolling
    echo Making inframet rolling for $year $month
    bin/deployment_history/usarray_deploy_map.py -t rolling \
    -d inframet $year $month 
}
 
### MAIN
 
for y in {2008..2013};
do
    for m in `seq -w 1 12`;
    do  
        if [ $y -eq 2013 ] && [ $m -gt 10 ] 
        then
            echo "Done."
            break
        fi  
        echo "$m-$y:"
        make_year_month $y $m
        make_year_month_infra $y $m
    done
done

