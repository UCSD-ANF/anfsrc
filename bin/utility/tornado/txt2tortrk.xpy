import sys, os

sys.path.append(os.environ['ANTELOPE'] + '/data/python/')

from antelope.datascope import *
from antelope.stock import str2epoch

def main():

	if len(sys.argv) < 3:
		print "\nUsage: txt2tortrk infile dbout"
		print "\nThis program will append tornado track data to the tortrk table of dbout."
		print "dbout will be created if necessary."
		print "\nInput text file is assumed to have whitespace-delimited fields in the following order:"
		print "year month day hour min sec start_lat start_lon end_lat end_lon EFscale length(km) width(m) injuries fatalities\n"
		exit()

	filepath = sys.argv[1]
	dbpath = sys.argv[2]

	if not os.path.isfile(dbpath):
		print "css3.0 database descriptor file created:", dbpath
		dbcreate(dbpath, "css3.0", dbpath=dbpath)

	dbout = dbopen(dbpath, "r+")

	dbout = dbout.lookup(table="tortrk")

	infile = open(filepath, "r")

	for a_line in infile:
		line = a_line.split()

		epoch_time = str2epoch( "%s/%s/%s %s:%s:%s" % (line[1], line[2], line[0], line[3], line[4], line[5]))

		print "Adding row - (time: ", epoch_time, ") (slat: ", eval(line[6]),  ") (slon: ", eval(line[7]), ") (elat: ", eval(line[8]), ") (elon: ", eval(line[9]), ") (EFscale: ", eval(line[10]), ") (width: ", eval(line[12]), ") (injuries: ", eval(line[13]), ") (fatalities: ", eval(line[14])

		dbout.addv("time", epoch_time, "slat", eval(line[6]), "slon", eval(line[7]), "elat", eval(line[8]), "elon", eval(line[9]), "EFscale", eval(line[10]), "width", eval(line[12])/1000.0, "injuries", eval(line[13]), "fatalities", eval(line[14]))

	dbout.close()
	infile.close()

main()
