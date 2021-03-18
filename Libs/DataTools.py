import collections
import pandas as pd
from Libs.constants import ERAM_PATH, RADAR_PATH


class Importer(object):
    """Load in necessary data"""
    def __init__(self):
        self.eram_bounds = collections.defaultdict(list)
        self.stars_bounds = {}
        self.radar_info = None
        self.radio_info = None

    def load_eram(self):
        """Only load in the ERAM information"""
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

    def load_radars(self):
        """Only load in the radar information"""
        radar_df = pd.read_csv(RADAR_PATH)
        self.radar_info = radar_df[
            [
                'SVDDSite',
                'RadarType',
                'SVDDLID',
                'Lat',
                'Lon',
                'PSR',
                'SSR'
            ]
        ]
