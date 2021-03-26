import collections
import pandas as pd

from Libs.constants import RADARS, RADIOS


class Parser(object):
    """Load in necessary data"""
    def __init__(self):
        self.eram_bounds = collections.defaultdict(list)
        self.stars_bounds = {}
        self.enroute_radars = None
        self.terminal_radars = None
        self.service_volumes = None

    def _load_service_volumes(self):
        """Load in all of the service volume information"""
        self.service_volumes.classB = self._filter_sv(airspace_class='B')
        self.service_volumes.classC = self._filter_sv(airspace_class='C')
        self.service_volumes.classD = self._filter_sv(airspace_class='D')

    def _load_eram(self, path):
        """Load in the ERAM information"""
        artcc_sites = pd.read_excel(path, sheet_name="EnRoute")
        current_id = None
        for row, id in enumerate(artcc_sites.ARTCC_ID):
            if isinstance(id, str):
                current_id = id
                self.eram_bounds[id].append(
                    [artcc_sites.SV_Lat[row], artcc_sites.SV_Lon[row]]
                )
            else:
                self.eram_bounds[current_id].append(
                    [artcc_sites.SV_Lat[row], artcc_sites.SV_Lon[row]]
                )

    def _load_radars(self, path):
        """Load in the radar information"""
        radar_info = [
            'Radar_Name',
            'Radar_ID',
            'Radar_Lat',
            'Radar_Lon',
            'PSR Type',
            'SSR Type',
            'Airspace_ID',
            'Comments'
        ]

        enroute_df = pd.read_excel(path, sheet_name='En Route Radars')
        self.enroute_radars = enroute_df[radar_info]

        terminal_df = pd.read_excel(path, sheet_name='Terminal Radars')
        self.terminal_radars = terminal_df[radar_info]

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
        self._load_service_volumes()

    @staticmethod
    def _filter_sv(airspace_class=None, path=RADARS):
        """Load in the service volumes for a given airspace class"""
        if not airspace_class:
            sv_df = pd.read_excel(path, sheet_name=f'Terminal Class{airspace_class}')
        else:
            sv_df = pd.read_excel(path, sheet_name='3rdPartySVs')
        sv_df = sv_df[
            [
                'SV ID',
                'Arpt_Name',
                'SV_Lat',
                'SV_Lon',
                'SV_Range_NM'
            ]
        ]

        return sv_df

