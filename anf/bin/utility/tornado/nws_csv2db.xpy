import sys, os

sys.path.append(os.environ['ANTELOPE'] + '/data/python/')

from antelope.datascope import *
from antelope.stock import str2epoch

not_migrated = ""

def timezone_correction(MM,DD,YYYY,intime,tz,row):
	if int(tz) == 3:
		timesplit = intime.split(":")
		return str2epoch("%s/%s/%s %s:%s:%s" % (MM,DD,YYYY,timesplit[0],timesplit[1],timesplit[2])) + 21600
	elif int(tz) == 9:
		return str2epoch("%s/%s/%s %s" % (MM,DD,YYYY,intime))
	else:
		not_migrated = not_migrated + "Row " + row + " not migrated to db. Time zone not known.\n"
		return -1

def yards2km(x):
	return x*0.0009144

def main():

	if len(sys.argv) < 3:
		print "\nUsage: nws_csv2db infile dbout"
		print "\nThis program will append tornado track data to the tortrk table of dbout."
		print "dbout will be created if necessary."
		print "\nInput file should be csv file obtained from National Weather Services.\n"
		sys.exit(-1)

	filepath = sys.argv[1]
	dbpath = sys.argv[2]

	if not os.path.isfile(dbpath):
		print "css3.0 database descriptor file created:", dbpath
		dbcreate(dbpath, "css3.0", dbpath=dbpath)

	dbout = dbopen(dbpath, "r+")

	dbout = dbout.lookup(table="tortrk")

	infile = open(filepath, "r")

	for a_line in infile:
		line = a_line.split(",")

		time = timezone_correction(line[2],line[3],line[1],line[5],line[6],line[0])

		if time:
			#epoch_time = str2epoch( "%s/%s/%s %s" % (line[2], line[3], line[1], time))

			EFscale = -1 if eval(line[10]) == -9 else eval(line[10])

			print "Processing row - ( time: ", time, ") ( slat: ", eval(line[15]),  ") ( slon: ", eval(line[16]), ") ( elat: ", eval(line[17]), ") ( elon: ", eval(line[18]), ") ( EFscale: ", EFscale, ") ( width: ", yards2km(eval(line[20])), ") ( injuries: ", eval(line[11]), ") ( fatalities: ", eval(line[12]), ")"

			dbout.addv("time", time, "slat", eval(line[15]), "slon", eval(line[16]), "elat", eval(line[17]), "elon", eval(line[18]), "EFscale", EFscale, "width", yards2km(eval(line[20])), "injuries", eval(line[11]), "fatalities", eval(line[12])), ")"

	dbout.close()
	infile.close()

	print "\nThe following migration errors occurred:"
	print "========================================\n"
	if not_migrated == "": print "None\n"
	else: print not_migrated

	return 0

if __name__ == "__main__":
	sys.exit(main())

else:
	raise Exception("Not a module to be imported!")
	sys.exit(-1)

