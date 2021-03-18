import collections
import pandas as pd
from constants import ERAM_PATH


class DataLoader(object):
    """Load in necessary data"""
    def __init__(self):
        self.eram_bounds = collections.defaultdict(list)
        self.stars_bounds = {}
        self.radar_locs = {}
        self.radio_locs = {}

    def load_eram(self):
        """Only load in the ERAM dataframe"""
        ctvs = pd.read_excel(ERAM_PATH, sheet_name="CTV - En Route")
        current_id = None
        for row, id in enumerate(ctvs.ARTCC_ID):
            if isinstance(id, str):
                current_id = id
                self.eram_bounds[id].append(
                    [ctvs.CTV_Lat[row], ctvs.CTV_Lon[row]]
                )
            else:
                self.eram_bounds[current_id].append(
                    [ctvs.CTV_Lat[row], ctvs.CTV_Lon[row]]
                )
