import collections
import pandas as pd

from Libs.constants import RADARS, RADIOS


class Importer(object):
    """Load in necessary data"""
    def __init__(self):
        self.eram_bounds = collections.defaultdict(list)
        self.stars_bounds = {}
        self.radar_info = None
        self.radio_info = None

    def _load_eram(self, path):
        """Load in the ERAM information"""
        ctvs = pd.read_excel(path, sheet_name="CTV - En Route")
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

    def _load_radars(self, path):
        """Load in the radar information"""
        radar_df = pd.read_excel(path, sheet_name="En Route Radars")
        self.radar_info = radar_df[
            [
                'Radar_Name',
                'Radar_ID',
                'Radar_Lat',
                'Radar_Lon',
                'PSR Type',
                'SSR Type',
                'Airspace_ID'
            ]
        ]

    def _load_radios(self, path=RADIOS):
        """Only load in the radio information"""
        radio_df = pd.read_csv(path)
        self.radio_info = radio_df[
            [
                'Alternate Location\n(Airport)',
                'RSID',
                'Latitude\n(Degrees)',
                'Longitude\n(Degrees)',
                'Enclosed By SV',
                'ADS-B/WAM Usage'
            ]
        ]

    def load_data(self, eram_path=RADARS, radar_path=RADARS, radio_path=RADIOS):
        """Load in the ERAM, Radar, and Radio information all at once"""
        self._load_eram(path=eram_path)
        self._load_radars(path=radar_path)
        self._load_radios(path=radio_path)
