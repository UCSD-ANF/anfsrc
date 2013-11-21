"""
File with all global variables for db2json

Will be loaded into script and 
not called directly.

Juan Reyes
reyes@ucsd.edu

"""

stations_pf = 'stations.pf'

subtype_list = ['all']
station_dict = {'decom':{}, 'adopt':{}, 'active':{}}
for k in station_dict.iterkeys():
    subtype_list.append(k)

core_fields = ["snet", "vnet", "lat", "lon", "staname", "time"]
active_fields = core_fields + [
    "commtype",
    "provider",
    "insname",
    "elev",
    "equip_install",
    "cert_time"
]
decom_fields = core_fields + [
    "decert_time",
    "insname",
    "endtime",
    "cert_time"
]
adopt_fields = core_fields + [
    "decert_time",
    "newsnet",
    "newsta",
    "atype",
    "auth"
]
# For station detail pages (individual station JSON files)
detail_dbmaster_fields = core_fields + [
    "sta",
    "ondate",
    "offdate",
    "elev",
    "endtime",
    "equip_install",
    "equip_remove",
    "cert_time",
    "decert_time",
    "commtype",
    "provider",
    "power",
    "dutycycle",
    "insname"
]
detail_dbmaster_adopt_fields  = adopt_fields + [
    "sta",
    "ondate",
    "offdate",
    "elev",
    "endtime",
    "equip_install",
    "equip_remove",
    "cert_time",
    "commtype",
    "provider",
    "power",
    "dutycycle",
    "insname"
]
detail_inst_hist_fields = [
    "insname",
    "instype",
    "ssident",
    "chan",
    "hang",
    "vang",
    "sitechan.ondate",
    "sitechan.offdate",
    "gtype",
    "idtag"
]
detail_deployment_hist_fields = [
    "time",
    "endtime",
    "vnet",
    "cert_time",
    "decert_time"
]
detail_comms_hist_fields = [
    "time",
    "endtime",
    "commtype",
    "provider",
    "power",
    "dutycycle"
]
detail_baler_fields = [
    "model",
    "firm",
    "nreboot",
    "last_reboot",
    "ssident"
]
detail_dlevents = ["dlevtype", "dlcomment"]

