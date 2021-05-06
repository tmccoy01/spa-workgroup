# 3rd party imports
import os
import collections
import pandas as pd

# Lib imports
from constants import RADARS, RADIOS, SV_LIST
import GeoTools


class SurveillanceSystem(object):
    """Main parent class to carry all data for NAS Surveillance Systems"""

    def __init__(self, sv_path=RADARS, radio_path=RADIOS, radar_path=RADARS):
        # Public attributes
        self.sv_bounds = collections.defaultdict(list)
        self.airspace_info = collections.defaultdict(list)
        self.radars = None
        self.radios = None
        # Radars
        self.psr_type = None
        self.ssr_type = None
        # Radios
        self.radio_variants = None
        self.radio_antennas = None
        # Private attributes
        self._sv_path = sv_path
        self._radio_path = radio_path
        self._radar_path = radar_path
        self._geo = GeoTools.Geo()

    def load_radios(self):
        radio_df = pd.read_excel(RADIOS, header=6)
        radio_df = radio_df[
            [
                "Operational Status",
                "LID\n(GBT/[MRU])",
                "Facility Location",
                "RSID",
                "Latitude\n(Degrees)",
                "Longitude\n(Degrees)",
                "Enclosed By SV.1",
                "ADS-B/WAM Usage",
                "Site Elevation (MSL)",
                "Antenna Height (AGL)",
                "1090ES Antenna",
                "Radio Variant",
            ]
        ]

        radio_df = radio_df.dropna(subset=["Radio Variant"])
        antennas = list(set(radio_df["1090ES Antenna"].to_list()))
        variants = list(set(radio_df["Radio Variant"].to_list()))

        # Filter repeated variants (if they occur)
        repeat_index = [ix for ix, var in enumerate(variants) if "/" in var]
        if repeat_index:
            del variants[repeat_index[0]]

        self.radios = radio_df
        self.radio_antennas = antennas
        self.radio_variants = variants

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

    def __init__(self, airspace_class="all"):
        # Initialize the SurveillanceSystem super class
        super().__init__()
        self.__load_airspace_info(airspace_class.upper())

    def __load_airspace_info(self, airspace_class):
        valid_classes = ["C", "B", "D"]
        if airspace_class == "ALL":
            for _class in valid_classes:
                self.airspace_info[_class].append(
                    self.__load_one_airspace_class(_class)
                )
        elif airspace_class not in valid_classes:
            raise ValueError(f"{airspace_class} is an incorrect class.")
        else:
            self.airspace_info[airspace_class].append(
                self.__load_one_airspace_class(airspace_class)
            )

    def __load_one_airspace_class(self, airspace_class):
        airspace_df = pd.read_excel(
            RADARS, sheet_name=f"Terminal Class{airspace_class}"
        )
        airspace_df = airspace_df[
            ["SV ID", "Arpt_Name", "SV_Lat", "SV_Lon", "SV_Range_NM"]
        ]
        airspace_df = airspace_df.dropna()

        # Parse out the bounds for each sv region
        for row, id in enumerate(airspace_df["SV ID"]):
            self.sv_bounds[id].append(
                self._geo.lat_lon_circle(
                    airspace_df["SV_Lat"][row],
                    airspace_df["SV_Lon"][row],
                    int(airspace_df["SV_Range_NM"][row]),
                )
            )

        return airspace_df

    def load_radars(self):
        radar_df = pd.read_excel(self._radar_path, sheet_name="Terminal Radars")
        radar_df = radar_df[
            ["Radar_Name", "Radar_ID", "Radar_Lat", "Radar_Lon", "SSR Type", "PSR Type"]
        ]

        radar_df = radar_df[:256].dropna(how="all", subset=["SSR Type", "PSR Type"])
        self.radars = radar_df[radar_df["SSR Type"] != "WAM"]
        self.psr_type = list(set(self.radars["PSR Type"].to_list()))
        self.ssr_type = list(set(self.radars["SSR Type"].to_list()))


class EnRoute(SurveillanceSystem):
    """Enroute Service Volume Description (Includes ERAM info)"""

    def __init__(self):
        super().__init__()
        self.sv_map = {}
        self.__load_bounds()

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
        artcc_sites = artcc_sites[["ARTCC_ID", "SV ID"]].dropna()
        self.sv_map = dict(zip(artcc_sites["ARTCC_ID"], artcc_sites["SV ID"]))

    def load_radars(self):
        radar_df = pd.read_excel(RADARS, sheet_name="En Route Radars")
        radar_df = radar_df[
            [
                "Radar_Name",
                "Radar_ID",
                "Radar_Lat",
                "Radar_Lon",
                "SSR Type",
                "PSR Type",
                "Airspace_ID",
            ]
        ]

        radar_df = radar_df.dropna(how="all", subset=["SSR Type", "PSR Type"])
        self.radars = radar_df[radar_df["SSR Type"] != "WAM"]
        self.psr_type = list(set(self.radars["PSR Type"].to_list()))
        self.ssr_type = list(set(self.radars["SSR Type"].to_list()))


class SurveillanceSource(object):
    """Gather all information for a given surveillance source"""

    def __init__(self, path: str, sv: str, sheet_name: int = 0, header: int = 0):
        self._sv = sv
        self.sensor_df = None
        self._path = path
        self.__load_sensors(sheet_name, header)

    @property
    def sv(self):
        return self._sv

    @sv.setter
    def sv(self, value):
        if value not in SV_LIST:
            raise ValueError(f"{value} is not a valid SV region.")

        self._sv = value

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, value):
        if not os.path.exists(value):
            raise ValueError("Path does not exist. Please input a valid path.")

        self._path = value

    def plot(self):
        """Not yet implemented"""
        pass

    def __load_sensors(self, sheet_name, header):
        """Simple base function to load in sensor info"""
        self.sensor_df = pd.read_excel(self._path, sheet_name=sheet_name, header=header)


class Radios(SurveillanceSource):
    """Gather all pertinent information for radios"""

    def __init__(self, sv: str = "ALL"):
        super().__init__(path=RADIOS, sv=sv, header=6)
        self.__filter_sensors()

    def __filter_sensors(self):
        if self.sv != "ALL":
            self.sensor_df = self.sensor_df[
                self.sensor_df["Enclosed By SV.1"] == self.sv
            ]

        self.sensor_df = self.sensor_df[
            [
                "Operational Status",
                "LID\n(GBT/[MRU])",
                "Facility Location",
                "RSID",
                "Latitude\n(Degrees)",
                "Longitude\n(Degrees)",
                "Enclosed By SV.1",
                "ADS-B/WAM Usage",
            ]
        ]

    # def plot(self, plot_type='kml', color='Red', shape=None):
    #     """Plot the radio locations"""
    #     plot_obj = self.__get_plot(plot_type)
    #
    # @staticmethod
    # def __get_plot(_type):
    #     """Get the correct plotting type"""
    #     opts = {'kml': plot_kml(), 'matplotlib': plot_matplot()}
    #     return opts[_type]


class Radars(SurveillanceSource):
    """Gather all pertinent information for radars"""

    def __init__(self, sv: str = "ALL"):
        super().__init__(path=RADARS, sv=sv, sheet_name=0)


if __name__ == "__main__":
    test = Radios()
