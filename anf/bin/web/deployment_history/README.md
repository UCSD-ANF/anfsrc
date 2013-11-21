Introduction
------------

These are scripts for generating maps and movies of the deployment of
seismic and inframet sensors over the lifetime of the USArray
Transportable Array network. These maps and movies are provided for the
public on the [station deployment history][deploy] page of the
[ANF website][anf_web].

  [deploy]: http://anf.ucsd.edu/stations/deployment_history.php
  [anf_web]: http://anf.ucsd.edu

Dependencies
------------

GMT - the generic mapping tools

ffmpeg - for movies

BRTT Antelope with Python bindings. 5.1-64 or earlier for the time being

### Map Data ###

The script usarray_deploy_map.py requires a number of GMT data files that are not included in this Git repository:

 * alaska.grad
 * alaska.grd
 * deathvalley.grad
 * deathvalley.grd
 * deathvalley.xy
 * saltonsea.grad
 * saltonsea.grd
 * saltonsea.xy
 * usa.grad
 * usa.grd
 * land_ocean.cpt
 * land_only.cpt

These [data files are available on the ANF website][data]. To install
them, change directories the data subdirectory and untar the files
there. You may also symlink them if you have them unpacked somewhere
else on your system.

  [data]: http://anf.ucsd.edu/data/support/webproc-deployment_history.data.tgz

Configuration
-------------

The scripts in this archive make use of the Antelope parameter file
format. They expect to have common.pf and stations.pf in the PFPATH
somewhere.
