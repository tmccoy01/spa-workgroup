import collections
import pandas as pd

from Libs import GeoTools
from Libs.constants import RADARS, RADIOS, ERAM_SITES


class SurveillanceSystem(object):
    """Main parent class to carry all data for NAS Surveillance Systems"""
    def __init__(self, sv_path=RADARS, radio_path=RADIOS, radar_path=RADARS):
        # Public attributes
        self.sv_bounds = collections.defaultdict(list)
        self.radio_map = {}
        self.radar_map = {}
        # Private attributes
        self._sv_path = sv_path
        self._radio_path = radio_path
        self._radar_path = radar_path
        self._geo = GeoTools.Geo()

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
    """Terminal Service Volume Description"""
    def __init__(self, airspace_class):
        # Initialize the SurveillanceSystem super class
        super().__init__()

        # Load in the correct airspace data
        self._airspace_df = pd.read_excel(RADARS, sheet_name=f'Terminal Class{airspace_class}')
        self._airspace_df = self._airspace_df[
            [
                'SV ID',
                'Arpt_Name',
                'SV_Lat',
                'SV_Lon',
                'SV_Range_NM'
            ]
        ].dropna()

        # Parse out the bounds for each sv region
        for row, id in enumerate(self._airspace_df['SV ID']):
            self.sv_bounds[id].append(
                self._geo.lat_lon_circle(
                    self._airspace_df['SV_Lat'][row], self._airspace_df['SV_Lon'][row],
                    int(self._airspace_df['SV_Range_NM'][row])
                )
            )


class EnRoute(SurveillanceSystem):
    """Enroute Service Volume Description (Includes ERAM info)"""
    def __init__(self):
        super().__init__()
        self.sv_map = {}
        self.__load_bounds()

    def radio_map(self, radios=None):
        """Not yet implemented"""


    def __load_bounds(self):
        """Load in the ERAM bounds"""
        artcc_sites = pd.read_excel(self._radar_path, sheet_name="EnRoute")
        current_id = None
        for row, id in enumerate(artcc_sites.ARTCC_ID):
            if isinstance(id, str):
                current_id = id
                self.sv_bounds[id].append(
                    [artcc_sites.SV_Lat[row], artcc_sites.SV_Lon[row]]
                )
            else:
                self.sv_bounds[current_id].append(
                    [artcc_sites.SV_Lat[row], artcc_sites.SV_Lon[row]]
                )

        # Create a map of ARTCC ID --> Service Volume ID
        artcc_sites = artcc_sites[['ARTCC_ID', 'SV ID']].dropna()
        self.sv_map = dict(zip(artcc_sites['ARTCC_ID'], artcc_sites['SV ID']))


class Radios(object):
    """Gather all pertinent information for all radios"""
    def __init__(self, sv=None):
        self._sv = sv
        self.radio_df = None
        self.__load_radios()

    def __load_radios(self):
        self.radio_df = pd.read_excel(RADIOS, header=6)
        if self._sv is not None:
            self.radio_df = self.radio_df[self.radio_df['Enclosed By SV.1'] == self._sv]

        self.radio_df = self.radio_df[
            [
                'Operational Status',
                'LID\n(GBT/[MRU])',
                'Facility Location',
                'RSID',
                'Latitude\n(Degrees)',
                'Longitude\n(Degrees)',
                'Enclosed By SV.1',
                'ADS-B/WAM Usage'
            ]
        ]
