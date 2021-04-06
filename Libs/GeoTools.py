from pykml import parser
from shapely.geometry import Polygon
from pygeodesy.ellipsoidalVincenty import LatLon
import pandas as pd
import matplotlib.pyplot as plt
import warnings
import numpy as np
from Libs import constants


class Geo(object):
    def __init__(self):
        self.earth_radius_nmi = 6371*1000/1852

    @property
    def earth_radius_nmi(self):
        return self.__earth_radius_nmi

    @earth_radius_nmi.setter
    def earth_radius_nmi(self, value):
        self.__earth_radius_nmi = value

    @staticmethod
    def __validate_lat_lon(lat: float, lon: float):
        err = None
        if isinstance(lat, float):
            if err is None and (lat > 90.0 or lat < -90.0):
                err = f'Invalid latitude specified {lat}'
        else:
            if err is None and ((lat > 90.0).any() or (lat < -90.0).any()):
                err = f'Invalid latitude specified {lat}'
        if isinstance(lon, float):
            if err is None and (lon > 180.0 or lon < -180.0):
                err = f'Invalid longitude specified {lon}'
        else:
            if err is None and ((lon > 180.0).any() or (lon < -180.0).any()):
                err = f'Invalid longitude specified {lon}'
        assert (err is None), err

    @staticmethod
    def __validate_as_degress(az_degrees: float):
        err = None
        if (az_degrees < 0) or (az_degrees > 360):
            err = f'Invalid azimuth degrees specified {az_degrees}'
        assert (err is None), err

    @staticmethod
    def __validate_az_acps(az_acps):
        err = None
        if (az_acps < 0) or (az_acps > 4096):
            err = f'Invalid azimuth ACPs specified {az_acps}'
        assert (err is None), err

    @staticmethod
    def __decimal_to_hhmmss(dec: float) -> str:
        """
        Convert decimal degrees lat/lon to hhmmss
        """
        hh = int(dec)
        x1_dec = dec - hh
        mm = int(x1_dec * 60)
        x2_dec = x1_dec - (float(mm) / 60.0)
        ss = (x2_dec * 3600)
        if ss > 59.99999:
            mm += 1
            ss -= 59.99999

        return '%02d:%02d:%05.3f' % (hh, mm, ss)

    @staticmethod
    def parse_latlon(coordinate):
        if isinstance(coordinate, (float, int)):
            if -180 <= coordinate <= 180:
                return coordinate
            else:
                raise ValueError(f'{coordinate} is outside the bounds allowable for a geodesic coordinate.')
        elif isinstance(coordinate, str):
            sign_chars = {'N': 1, 'S': -1, 'E': 1, 'W': -1}
            sign = None
            if not coordinate:
                return None

            try:
                decimal = float(coordinate)
            except ValueError:
                coordinate = coordinate.strip().upper()
                translater = str.maketrans({
                    '"': " ",
                    "'": " ",
                    "°": " ",
                    ":": " "
                })
                coordinate = coordinate.translate(translater)
                lastchar = coordinate[-1]
                firstchar = coordinate[0]
                if firstchar in ['-', '+'] and lastchar in sign_chars:
                    raise ValueError()
                elif lastchar in sign_chars:
                    sign = sign_chars[lastchar]
                    coordinate = coordinate[0:-1].strip()
                elif firstchar == '-':
                    sign = -1
                    coordinate = coordinate[0:-1].strip()
                elif firstchar == '+':
                    sign = 1
                    coordinate = coordinate[1:].strip()
                else:
                    sign = 1

                components = coordinate.split()
                if len(components) == 3:
                    degrees = int(components[0])
                    minutes = int(components[1])
                    seconds = float(components[2])
                    decimal = (degrees + minutes / 60 + seconds / 3600) * sign
                elif len(components):
                    decimal = float(components[0]) * sign
                else:
                    raise ValueError()

            return Geo.parse_latlon(decimal)

    def latlon_dec_to_hhmmss(self, lat: float, lon: float) -> list:
        if lat > 0:
            lat_ns = 'N'
        else:
            lat = -lat
            lat_ns = 'S'
        if lon > 0:
            lon_ew = 'E'
        else:
            lon = -lon
            lon_ew = 'W'

        hhmmss_lat = self.__decimal_to_hhmmss(lat) + ' ' + lat_ns
        hhmmss_lon = self.__decimal_to_hhmmss(lon) + ' ' + lon_ew
        return [hhmmss_lat, hhmmss_lon]

    @staticmethod
    def hhmmss_to_decimal(hhmmss: str) -> float:
        hhmmss_list = hhmmss.split(':')
        hh, mm = hhmmss_list[0], hhmmss_list[1]
        ss_decimal = hhmmss_list[2]
        ss_list = ss_decimal.split('.')
        if len(ss_list) > 1:
            ss = ss_list[0]
            dec_list = ss_list[1].split(' ')
            dec = dec_list[0]
            nsew = dec_list[1]
        else:
            dec = 0
            ss_list_2 = ss_list[0].split(' ')
            ss = ss_list_2[0]
            nsew = ss_list_2[1]

        decimal_val = float(hh) + (float(mm) / 60.0 + float(ss) / 3600.00)
        if nsew in ['S', 'W']:
            decimal_val *= -1

        return decimal_val

    def distance_between_two_lat_lon(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        self.__validate_lat_lon(lat1, lon1)
        self.__validate_lat_lon(lat2, lon2)
        dlat = np.radians(lat2 - lat1)
        dlon = np.radians(lon2 - lat2)
        # Great Circle Formula
        a = (np.sin(dlat / 2) * np.sin(dlat / 2)) + \
            (np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlon / 2) * np.sin(dlon / 2))
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
        d = self.__earth_radius_nmi * c

        return d

    def distance_xy_between_two_lat_lon(self, lat1: float, lon1: float, lat2: float, lon2: float) -> list:
        x_nmi = self.distance_between_two_lat_lon(lat1, lon1, lat1, lon2)
        y_nmi = self.distance_between_two_lat_lon(lat1, lon1, lat2, lon1)
        return [x_nmi, y_nmi]

    def lat_lon_from_reference_give_xy_nmi(self, ref_lat: float, ref_lon: float, x_nmi: float, y_nmi: float) -> list:
        resolution = 0.01
        d_lat = self.distance_between_two_lat_lon(ref_lat, ref_lon, (ref_lat + resolution), ref_lon)
        d_lon = self.distance_between_two_lat_lon(ref_lat, ref_lon, ref_lat, (ref_lon + resolution))
        new_lat = ref_lat + ((y_nmi * resolution) / d_lat)
        new_lon = ref_lon + ((x_nmi * resolution) / d_lon)
        return [new_lat, new_lon]

    def lat_lon_from_reference_multiple_xy_nmi(self, ref_lat: float, ref_lon: float, xy_nmi_list: list) -> list:
        lat_lon_list = []
        for xy_nmi in xy_nmi_list:
            lat_lon = self.lat_lon_from_reference_give_xy_nmi(ref_lat, ref_lon, xy_nmi[0], xy_nmi[1])
            lat_lon_list.append(lat_lon)

        return lat_lon_list

    @staticmethod
    def lat_lon_from_reference_given_range_az_degrees(ref_lat, ref_lon, range_nmi, az_degrees) -> list:
        p = LatLon(ref_lat, ref_lon)
        range_meters = range_nmi * constants.NM_TO_METERS
        d = p.destination(range_meters, az_degrees)
        return (d.lat, d.lon)

    def lat_lon_from_reference_multiple_range_az_degrees(self, ref_lat, ref_lon, range_az_list) -> list:
        lat_lon_list = []
        for range_az in range_az_list:
            lat_lon = self.lat_lon_from_reference_given_range_az_degrees(ref_lat, ref_lon, range_az[0], range_az[1])
            lat_lon_list.append(lat_lon)

        return lat_lon_list

    def lat_lon_from_reference_given_range_az_acps(self, ref_lat, ref_lon, range_nmi, az_acps) -> list:
        self.__validate_az_acps(az_acps)
        az_degrees = (360.0 * az_acps) / 4096.0
        return self.lat_lon_from_reference_given_range_az_degrees(ref_lat, ref_lon, range_nmi, az_degrees)

    def lat_lon_from_reference_multiple_range_az_acps(self, ref_lat, ref_lon, range_az_list) -> list:
        lat_lon_list = []
        for range_az in range_az_list:
            lat_lon = self.lat_lon_from_reference_given_range_az_acps(ref_lat, ref_lon, range_az[0], range_az[1])
            lat_lon_list.append(lat_lon)
        return lat_lon_list

    def lat_lon_circle(self, ref_lat, ref_lon, radius_nmi, num_entries=180) -> list:
        lat_lon_list = []
        az_degrees = 0.0
        delta_az_degree = 360.0/num_entries
        while az_degrees < 360.0:
            (lat_lon) = self.lat_lon_from_reference_given_range_az_degrees(ref_lat, ref_lon, radius_nmi, az_degrees)
            lat_lon_list.append(lat_lon)
            az_degrees += delta_az_degree
        num_items = len(lat_lon_list)
        if num_items > 0 and (lat_lon_list[0] != lat_lon_list[num_items -1]):
            lat_lon_list.append(lat_lon_list[0])

        return lat_lon_list

    @staticmethod
    def lat_lon_to_ecef(lat_lon_array: np.ndarray, alt: np.ndarray) -> tuple:
        if (not isinstance(lat_lon_array, np.ndarray)) or (not isinstance(alt, np.ndarray)):
            raise ValueError(f'Inputs are of  \'{type(lat_lon_array)}\' and \'{type(alt)}\''
                             f'. They must be \'<class np.ndarray>\'')

        try:
            lats = lat_lon_array[:, 0]
            lons = lat_lon_array[:, 1]
        except IndexError:
            lats = lat_lon_array[0]
            lons = lat_lon_array[1]

        f = (constants.SEMI_MAJOR_AXIS_A - constants.SEMI_MAJOR_AXIS_B) / constants.SEMI_MAJOR_AXIS_A
        e = np.sqrt(f * (2 - f))
        # Calculate the length of ellipsoid normal
        eqn1 = np.power(np.sin(np.degrees(lats)), 2)
        bottom_n = np.sqrt(1 - (e**2 * eqn1))
        n = np.divide(constants.SEMI_MAJOR_AXIS_A, bottom_n).ravel()
        # Calculate output values
        cos_lat = np.cos(np.radians(lats))
        cos_lon = np.cos(np.radians(lons))
        sin_lat = np.sin(np.radians(lats))
        sin_lon = np.sin(np.radians(lons))
        eqn2 = (n + alt.T).ravel() * cos_lat
        x_ecef = eqn2 * cos_lon
        y_ecef = eqn2 * sin_lon
        eqn3 = ((n * (1 - e**2)) + alt.T).ravel()
        z_ecef = eqn3 * sin_lat
        return x_ecef, y_ecef, z_ecef

    def enu_to_lat_lon_alt(self, enu, system_ref):
        if enu.shape[1] != 3:
            raise ValueError(f'Size of enu must be nx3, not nx{enu.shape[1]}')

        lat_ref, lon_ref, alt_ref = system_ref
        lat_ref = np.deg2rad(lat_ref)
        lon_ref = np.deg2rad(lon_ref)
        xr, yr, zr, e = self.__reference_values(system_ref, lon_ref, lat_ref, alt_ref)

        x = -np.sin(lon_ref)*enu[:, 0] - np.cos(lon_ref) * np.sin(lat_ref)*enu[:, 1] + np.cos(lon_ref) * \
            np.cos(lat_ref)*enu[:, 2] + xr
        y = np.cos(lon_ref)*enu[:, 0] - np.sin(lon_ref) * np.sin(lat_ref)*enu[:, 1] + np.cos(lat_ref) * \
            np.sin(lon_ref)*enu[:, 2] + yr
        z = np.cos(lat_ref)*enu[:, 1] + np.sin(lat_ref)*enu[:, 2] + zr

        p = np.sqrt(np.power(x, 2) + np.power(y, 2)).T
        phi_loop = np.arctan2(z, p * (1 - e**2))
        lam = np.arctan2(y, x)
        n_loop = n_loop = (constants.SEMI_MAJOR_AXIS_A) / (np.sqrt(1 - (e * np.sin(phi_loop))**2))

        # Iterate through until you find the correct values
        done_test = 1000
        k = 1
        while done_test > (1*10**-10) and (k < 100):
            k += 1
            h_loop = p / (np.cos(phi_loop) - n_loop)
            phi_loop_tmp = np.arctan2(z, (p * (1-e**2)*np.divide(n_loop, (n_loop + h_loop))))
            phi_loop_delta = phi_loop_tmp - phi_loop
            phi_loop = phi_loop_tmp

            top = (constants.SEMI_MAJOR_AXIS_A * np.ones((enu.shape[0], 1))).T
            bot = np.sqrt(1 - np.power(e * np.sin(phi_loop), 2))
            n_loop = np.divide(top, bot).flatten()
            done_test = max(np.abs(phi_loop_delta))

        return np.array((np.rad2deg(phi_loop), np.rad2deg(lam), h_loop))

    def great_circle_distance(self, lat0, lon0, lat1, lon1):
        lat0 = np.deg2rad(lat0)
        lon0 = np.deg2rad(lon0)
        lat1 = np.deg2rad(lat1)
        lon1 = np.deg2rad(lon1)

        dist = np.arccos(
            np.cos(lat0) * np.sin(lat1) + np.cos(lat0) * np.cos(lat1) * np.cos(lon0 - lon1)
        ) * self.__earth_radius_nmi
        return dist

    @staticmethod
    def __reference_values(system, lon_ref, lat_ref, alt_ref):
        b = constants.SEMI_MAJOR_AXIS_A * (1 - constants.RECIPROCAL_FLATTENING)
        e = np.sqrt((constants.SEMI_MAJOR_AXIS_A ** 2 - b ** 2) / (constants.SEMI_MAJOR_AXIS_A ** 2))
        e2 = (2 * constants.RECIPROCAL_FLATTENING) - (constants.RECIPROCAL_FLATTENING ** 2)

        chi_ref = np.sqrt(1 - e2 * np.power(np.sin(lat_ref), 2))
        part_one = np.multiply(np.divide(constants.SEMI_MAJOR_AXIS_A, chi_ref) + alt_ref, np.cos(lat_ref))

        xr = np.multiply(part_one, np.cos(lon_ref))
        yr = np.multiply(part_one, np.sin(lon_ref))
        zr = np.multiply(np.divide(constants.SEMI_MAJOR_AXIS_A * (1 - e2), chi_ref) + alt_ref, np.sin(lat_ref))

        return xr, yr, zr, e


if __name__ == '__main__':
    from CoverageAnalysis.Libs.Surveillance import Radar
    xy = np.arange(-150, 150 + 0.1, 0.1).T * constants.NM_TO_METERS
    xm, ym = np.meshgrid(xy, xy)
    x = xm.flatten()
    y = xm.flatten()
    enu = np.array((x, y, np.ones(x.size) * 1500 * constants.FEET_TO_METERS)).T
    sensor = Radar('mcc')
    geo = Geo()
    system_lla = geo.enu_to_lat_lon_alt(enu, sensor.observer)
    aaa = 1