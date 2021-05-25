DATA_PATH = "/Users/tannermccoy/Development/Work/config"
RADARS = (
    DATA_PATH + "/SBS_Service_Volume_Description_Document_v4.9.1_dated_2018-10-16.xlsx"
)
RADIOS = DATA_PATH + "/radio_locations.xlsx"

""" Constants """
METERS_TO_FEET = 3.2808399
FEET_TO_METERS = 1 / METERS_TO_FEET
NM_TO_METERS = 1852.0
SEMI_MAJOR_AXIS_A = 6378137.0
SEMI_MAJOR_AXIS_B = 6356752.3142
RECIPROCAL_FLATTENING = 1 / 298.257223563

ERAM_SITES = [
    "ZAB",
    "ZAN",
    "ZAU",
    "ZBW",
    "ZDC",
    "ZDV",
    "ZFW",
    "ZHN",
    "ZHU",
    "ZID",
    "ZJX",
    "ZKC",
    "ZLA",
    "ZLC",
    "ZMA",
    "ZME",
    "ZMP",
    "ZNY",
    "ZOA",
    "ZOB",
    "ZSE",
    "ZSU",
    "ZTL",
    "ZUA",
    "ZHU",
]

SRR_TYPES = ["ASR-8", "ASR-9", "ASR-11"]

SV_LIST = ["ALL"]

# PSR
RADAR_SHAPES = {
    "ASR-7": "7",
    "ASR-8": "8",
    "ASR-9": "9",
    "ASR-11": "1",
    "ARSR-4": "4",
    "CARSR": "circle",
    "DASR": "stars",
    "MPN-14K": "diamond",
    "FPS-117": "square",
    "N/A": "blank",
}

# SSR
RADAR_COLORS = {
    "ATCBI-5": "a6cee3",
    "ATCBI-6": "1f78b4",
    "ATCBI-6M": "b2df8a",
    "BDAT": "33a02c",
    "Canadian SSR": "fb9a99",
    "MODES": "78c679",
    "MSSR": "fdbf6f",
    "MSSR-2000i": "ff7f00",
    "TPX-42": "cab2d6",
}

RADIO_COLORS = {
    "omni": "8dd3c7",
    "2-sector": "ffffb3",
    "4-sector": "b2df8a",
    "virtual": "fb8072",
}

RADIO_SHAPES = {"Thales": "circle", "Selex": "diamond", "Aireon": "stars"}
