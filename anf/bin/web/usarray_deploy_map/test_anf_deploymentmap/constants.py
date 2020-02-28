"""Constants for test cases."""
DEFAULT_PF_NAME = "usarray_deploy_map"
TEST_REGION_DATA = [
    "  conus,       Contiguous US,    15,     50,     -119,   -64,    usa.grd,         usa.grad",
    "  saltonsea,   Salton Sea,       15,     50,     -119,   -64,    saltonsea.grd,   saltonsea.grad",
    "  deathvalley, Death Valley,     15,     50,     -119,   -64,    deathvalley.grd, deathvalley.grad",
    "  alaska,      Alaska,           51,     71,     -169,   -119,   alaska.grd,      alaska.grad",
]
#  1262304000.000 (001) 2010-01-01  00:00:00.00000 UTC Friday
METADATA_TIME = 1262304000.000
#  1264982400.000 (032) 2010-02-01  00:00:00.00000 UTC Monday
METADATA_ENDTIME = 1264982400.000
METADATA_DEFAULTS = {
    "snet": "XX",
    "sta": "TEST",
    "lat": "33.12345",
    "lon": "-118.12345",
    "time": METADATA_TIME,
    "endtime": METADATA_ENDTIME,
    "extra_channels": None,
}
