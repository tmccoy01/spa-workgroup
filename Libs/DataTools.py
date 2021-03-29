import collections
import pandas as pd

from Libs.constants import RADARS, RADIOS, ERAM_SITES


class Parser(object):
    """Load in necessary data"""
    # TODO: Refactor this to work more cleanly. Maybe, create a new datatype for the Radar's and Radio's?
    def __init__(self):
        self.eram_bounds = collections.defaultdict(list)
        self.service_volumes = {}
        self.stars_bounds = {}
        self.enroute_radars = None
        self.terminal_radars = None

        self._sv_map = {}

    def _load_service_volumes(self):
        """Load in all of the service volume information"""
        self.service_volumes['B'] = self._filter_sv(airspace_class='B')
        self.service_volumes['C'] = self._filter_sv(airspace_class='C')
        self.service_volumes['D'] = self._filter_sv(airspace_class='D')

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

        # Create a map of ARTCC ID --> Service Volume ID
        artcc_sites = artcc_sites[['ARTCC_ID', 'SV ID']].dropna()
        self._sv_map = dict(zip(artcc_sites['ARTCC_ID'], artcc_sites['SV ID']))

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

    def map_radios(self, artcc_id=ERAM_SITES) -> dict:
        """Create a dictionary mapping of ADS-B radios to ARTCC region"""
        assert self.radio_info is not None
        radio_ids = self.radio_info['RSID'].to_list()
        radio_svs = [id.split('-')[0] for id in radio_ids]
        for site in ERAM_SITES:
            sv_id = self._sv_map[site]
            radio_idx = [ix for ix, val in enumerate(radio_svs) if sv_id in val]

    @staticmethod
    def _filter_sv(airspace_class=None, path=RADARS):
        """Load in the service volumes for a given airspace class"""
        if airspace_class is None:
            sv_df = pd.read_excel(path, sheet_name='3rdPartySVs')
        else:
            sv_df = pd.read_excel(path, sheet_name=f'Terminal Class{airspace_class}')
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


class SurveillanceSystem(object):
    """Main parent class to carry all data for NAS Surveillance Systems"""
    def __init__(self, sv_path=RADARS, radio_path=RADIOS, radar_path=RADARS):
        # Public attributes
        self.sv_bounds = {}
        self.radio_map = {}
        self.radar_map = {}
        # Private attributes
        self._sv_path = sv_path
        self._radio_path = radio_path
        self._radar_path = radar_path

    # TODO: Implement these two private methods below inside of the parent class
    @staticmethod
    def _map_radios():
        """Placeholder until this is implemented"""
        pass

    @staticmethod
    def _map_radars():
        """Placeholder until this is implemented"""
        pass


class Terminal(SurveillanceSystem):
    """Structure to hold all Terminal Service Volume information"""
    def __init__(self, airspace_class):
        super().__init__()
        self._airspace_df= pd.read_excel(RADARS, sheet_name=f'Terminal Class{airspace_class}')
        self._airspace_df = self._airspace_df[
            'SV ID',
            'Arpt_Name',
            'SV_Lat',
            'SV_Lon',
            'SV_Range_NM'
        ]

