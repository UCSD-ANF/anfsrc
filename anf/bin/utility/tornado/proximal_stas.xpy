from antelope.datascope import *
from antelope.stock import str2epoch, epoch2str, now

from math import pow, sqrt, sin, pi

import time, re

def min_dist(site_lat, site_lon, tor_slat, tor_slon, tor_elat, tor_elon):
	db_dummy = Dbptr()

	#s - tornado start location
	#e - tornado end location
	#r - station (receiver location)

	azimuth = lambda lat1,lon1,lat2,lon2: db_dummy.ex_eval("azimuth(%f,%f,%f,%f)"%(lat1,lon1,lat2,lon2))
	distance = lambda lat1,lon1,lat2,lon2: db_dummy.ex_eval("distance(%f,%f,%f,%f)"%(lat1,lon1,lat2,lon2))
	deg2km = lambda d: db_dummy.ex_eval("deg2km(%f)"%d)

	if tor_slat == tor_elat and tor_slon == tor_elon: return deg2km(distance(tor_slat, tor_slon, site_lat, site_lon))

	delta_sr_se = abs(azimuth(tor_slat,tor_slon,site_lat,site_lon) - azimuth(tor_slat,tor_slon,tor_elat,tor_elon))
	delta_er_es = abs(azimuth(tor_elat,tor_elon,site_lat,site_lon) - azimuth(tor_elat,tor_elon,tor_slat,tor_slon))

	theta_sr_se = delta_sr_se if delta_sr_se <= 180.0 else (360.0 - delta_sr_se)
	theta_er_es = delta_er_es if delta_er_es <= 180.0 else (360.0 - delta_er_es)

	if theta_sr_se >= 90.0: return deg2km(distance(tor_slat,tor_slon,site_lat,site_lon))

	elif theta_er_es >= 90.0: return deg2km(distance(tor_elat,tor_elon,site_lat,site_lon))

	else:
		min_dist_a = deg2km(distance(tor_slat,tor_slon,site_lat,site_lon))*sin(theta_sr_se*pi/180.0)
		min_dist_b = deg2km(distance(tor_elat,tor_elon,site_lat,site_lon))*sin(theta_er_es*pi/180.0)

		if min_dist_a < MAX_DIST and abs(min_dist_a - min_dist_b) > 0.1:
			print "abs(min_dist_a - min_dist_b) < 0.1",min_dist_a, min_dist_b 
			sys.exit()

		return min_dist_a

def main():
	global MAX_DIST
	MAX_DIST = float(sys.argv[6])

	#open site table
	site_tbl = dbopen(sys.argv[1],"r").lookup(table="site").sort("sta",unique=True).sort("ondate")


	#open tortrk table
	tortrk_tbl = dbopen(sys.argv[2],"r").lookup(table="tortrk").sort("time")
	tortrk_tbl.record = 0

	path2wfdisc = sys.argv[3]

	first_yr = int(epoch2str(tortrk_tbl.getv("time")[0], "%Y"))
	tortrk_tbl.record = tortrk_tbl.nrecs() - 1
	last_yr = int(epoch2str(tortrk_tbl.getv("time")[0], "%Y"))

	wfdisc_in = {}

	for yr in range(first_yr,last_yr+1,1): wfdisc_in[yr] = dbopen(path2wfdisc + "_" + str(yr), "r").lookup(table="wfdisc")

	path2wfs = sys.argv[4]

	dbout_path = sys.argv[5]
        if not os.path.isfile(dbout_path):
		dbcreate(dbout_path, "css3.0", dbpath=dbout_path)
	        print "css3.0 database descriptor file created:", dbout_path

	dbout = dbopen(dbout_path,"r+")
	wfdisc_out = dbout.lookup(table="wfdisc")
	arrival_out = dbout.lookup(table="arrival")


	for tortrk_tbl.record in range(tortrk_tbl.nrecs()):
		tor_slat, tor_slon, tor_elat, tor_elon, tor_stime = tortrk_tbl.getv("slat","slon","elat","elon","time")
		yr = int(epoch2str(tor_stime, "%Y"))
		hr = int(epoch2str(tor_stime, "%H"))
		tor_YYYYJJJ = int(epoch2str(tor_stime,"%Y%j"))

		print "Processing tornado track - start time: ", epoch2str(tor_stime, "%D %T")

		for site_tbl.record in range(site_tbl.nrecs()):
			site_lat, site_lon, sta = site_tbl.getv("lat","lon","sta")

			if min_dist(site_lat, site_lon, tor_slat, tor_slon, tor_elat, tor_elon) < MAX_DIST and int(site_tbl.getv("ondate")[0]) < tor_YYYYJJJ and int(site_tbl.getv("offdate")[0]) > tor_YYYYJJJ:

				print "Station: %s close encounter - %.2f km. Adding to wfdisc." % (sta, min_dist(site_lat, site_lon, tor_slat, tor_slon, tor_elat, tor_elon))

				wfdisc_in_tmp = wfdisc_in[yr]
				wfdisc_in_tmp.record = -1

				while True:
					wfdisc_in_tmp.record = wfdisc_in_tmp.find("sta =~ /%s/ && time <= _%f_ && endtime > _%f_" % (sta,tor_stime,tor_stime), first=wfdisc_in_tmp.record)

					if wfdisc_in_tmp.record >= 0:
						wfdisc_out.record = wfdisc_out.addnull()
						for wfdisc_in_tmp.field in range(wfdisc_in_tmp.query(dbFIELD_COUNT)):
							field = wfdisc_in_tmp.query(dbFIELD_NAME)
							wfdisc_out.putv(field,wfdisc_in_tmp.getv(field)[0])

					else: break

				#if the tornado occurred during the first hour of the day copy the wfdisc row for the previous day to the output db as well
				#doesn't handle events at 23:00 Dec 31 or 00:00 Jan 1
				if hr == 0:
					wfdisc_in_tmp.record = -1

					while True:
						wfdisc_in_tmp.record = wfdisc_in_tmp.find("sta =~ /%s/ && time <= _%f_ && endtime > _%f_" % (sta,tor_stime-172800.0,tor_stime-172800.0), first=wfdisc_in_tmp.record)

						if wfdisc_in_tmp.record >= 0:
							wfdisc_out.record = wfdisc_out.addnull()
							for wfdisc_in_tmp.field in range(wfdisc_in_tmp.query(dbFIELD_COUNT)):
								field = wfdisc_in_tmp.query(dbFIELD_NAME)
								wfdisc_out.putv(field,wfdisc_in_tmp.getv(field)[0])

						else: break

				#if the tornado occurred during the last hour of the day copy the wfdisc row for the following day to the output db as well
				#doesn't handle events at 23:00 Dec 31 or 00:00 Jan 1
				elif hr == 23:
					wfdisc_in_tmp.record = -1

					while True:
						wfdisc_in_tmp.record = wfdisc_in_tmp.find("sta =~ /%s/ && time <= _%f_ && endtime > _%f_" % (sta,tor_stime+172800.0,tor_stime+172800.0), first=wfdisc_in_tmp.record)

						if wfdisc_in_tmp.record >= 0:
							wfdisc_out.record = wfdisc_out.addnull()
							for wfdisc_in_tmp.field in range(wfdisc_in_tmp.query(dbFIELD_COUNT)):
								field = wfdisc_in_tmp.query(dbFIELD_NAME)
								wfdisc_out.putv(field,wfdisc_in_tmp.getv(field)[0])

						else: break

				#create "T" arrivals on vertical channels
				sitechan_tbl = site_tbl.subset("sta =~ /%s/" % sta).join("sitechan").subset("chan =~ /.*Z.*/")

				for sitechan_tbl.record in range(sitechan_tbl.nrecs()):
					arrival_out.record = arrival_out.addnull()
					arrival_out.putv("sta",sta,"time",tor_stime,"chan",sitechan_tbl.getv("chan")[0],"iphase","T")

	#fix wfdisc.dir field
	for wfdisc_out.record in range(wfdisc_out.nrecs()):
		dir = wfdisc_out.getv("dir")[0]
		if re.match("\d{4}/\d{3}",dir) is not None:
			wfdisc_out.putv("dir","%s/%s" % (path2wfs, wfdisc_out.getv("dir")[0]))

	return 0


if __name__ == "__main__":
	if len(sys.argv) < 7:
		print "\nUsage - proximal_stas dbin_site dbin_track path2wfdisc path2wfs dbout max_dist\n"
		print "dbin_site: path to db containing site table"
		print "dbin_track: path to db containing tornado track table"
		print "path2wfdisc: path to wfdiscs (assumption - yearly wfdiscs are used and have name path2wfdisc_YYYY)"
		print "path2wfs: path to top-level wf directory"
		print "dbout: path to output db"
		print "max_dist: maximum distance for close encounter\n"
		print "eg: proximal_stas /anf/TA/rt/usarray/usarray ~/staging/tornado/testdb /anf/TA/dbs/wfs/certified/usarray /anf/TA/dbs/wfs/certified ~/staging/tornado/proximal_stas 10.0\n"
		sys.exit(-1)

	sys.exit(main())

else:
	print "proximal_stas - Not a module to import!"
	sys.exit(-1)
