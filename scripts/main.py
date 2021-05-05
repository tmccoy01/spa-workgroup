import pandas as pd
import collections

from pandas.core.frame import DataFrame
from Libs import (
    DataTools,
    KmlTools,
    GeoTools,
    constants
)

_geo = GeoTools.Geo()


def plot_eram(data, kml, parent):
    """Test to load and plot the ERAM areas"""
    eram_folder = kml.add_folder(parent, name="ERAM Boundaries")
    data.load_radars()
    data.load_radios()
    for site in constants.ERAM_SITES:
        curr_sv = int(data.sv_map[site])
        curr_radars = data.radars[data.radars.Airspace_ID == site]
        curr_radios = data.radios[data.radios['Enclosed By SV.1'] == curr_sv]
        temp_node = kml.add_folder(eram_folder, name=site)
        # Plot the radars for the current ARTCC region
        radar_node = kml.add_folder(temp_node, name='Radars')
        for ix, row in curr_radars.iterrows():
            if pd.isna(row['PSR Type']):
                shape = 'blank'
            else:
                shape = constants.RADAR_SHAPES[row['PSR Type']]

            color = constants.RADAR_COLORS[row['SSR Type']]

            kml.add_special(
                row['Radar_Lat'],
                row['Radar_Lon'],
                base_shape='paddle',
                parent_node=radar_node,
                color=color,
                shape=shape,
                name=row['Radar_ID'],
                description=str(row['SSR Type']) + "_" + str(row['PSR Type']) + "\n" + row['Radar_Name']
            )

        # Plot the radios for the current ARTCC region
        radio_node = kml.add_folder(temp_node, name='Radios')
        for ix, row in curr_radios.iterrows():
            if row['Operational Status'] == 'Operational' and row['ADS-B/WAM Usage'] == 'ADS-B':
                if 'Thales' in row['Radio Variant']:
                    shape = 'circle'
                else:
                    shape = constants.RADIO_SHAPES[row['Radio Variant']]

                color = constants.RADIO_COLORS[row['1090ES Antenna']]

                kml.add_special(
                    row['Latitude\n(Degrees)'],
                    row['Longitude\n(Degrees)'],
                    base_shape='square',
                    parent_node=radio_node,
                    color=color,
                    shape=shape,
                    name=row['RSID'],
                    description=str(row['LID\n(GBT/[MRU])']) + " " + row['Facility Location']
                )

        # Plot the ARTCC region boundary
        kml.add_polygon(
            data.sv_bounds[site],
            filled=False,
            parent_node=temp_node,
            color=[0xff, 0x00, 0x00],
            opacity=100,
            line_width=3
        )

    return kml


def plot_radios_terminal(kml, sensors, node):
    for ix, row in sensors.iterrows():
        if row['Operational Status'] == 'Operational' and row['ADS-B/WAM Usage'] == 'ADS-B':
            if 'Thales' in row['Radio Variant']:
                shape = 'circle'
            else:
                shape = constants.RADIO_SHAPES[row['Radio Variant']]

            color = constants.RADIO_COLORS[row['1090ES Antenna']]

            kml.add_special(
                row['Latitude\n(Degrees)'],
                row['Longitude\n(Degrees)'],
                base_shape='square',
                parent_node=node,
                color=color,
                shape=shape,
                name=row['RSID'],
                description=str(row['LID\n(GBT/[MRU])']) + " " + row['Facility Location']
            )

    return kml


def plot_radars_terminal(kml, sensors, node):
    # TODO: Implement a '_get_sensor_plot_type' method for this.
    for ix, row in sensors.iterrows():
        if pd.isna(row['PSR Type']):
            shape = 'blank'
        else:
            shape = constants.RADAR_SHAPES[row['PSR Type']]

        color = constants.RADAR_COLORS[row['SSR Type']]

        kml.add_special(
            row['Radar_Lat'],
            row['Radar_Lon'],
            base_shape='paddle',
            parent_node=node,
            color=color,
            shape=shape,
            name=row['Radar_ID'],
            description=str(row['SSR Type']) + "_" + str(row['PSR Type']) + "\n" + row['Radar_Name']
        )

    return kml


def _plot_single_bound(sensor_info, kml, parent, color):
    lat_lon = _geo.lat_lon_circle(
        sensor_info['SV_Lat'], sensor_info['SV_Lon'], radius_nmi=sensor_info['SV_Range_NM']
    )
    kml.add_polygon(
        lat_lon,
        parent_node=parent,
        color=color,
        line_width=3,
        opacity=30,
        name=sensor_info['Arpt_Name']
    )

    return kml


def _filter_type(sensor_info: pd.DataFrame, sensor_type: str, filter: str = None):
    """
    return a dataframe filter by given 'sensor_type' and 'filter'
    """
    filtered_df = None
    if filter is not None:
        filtered_df = sensor_info[sensor_info[sensor_type] == filter]

    return filtered_df


def plot_all_types(kml, parent: str = None):
    """
    plot each sensor type so that it can be individually turned on and off
    """
    # TODO: grab all of the different sensor types


def plot_sv_bounds(sv_regions, kml, parent):
    types = ['B', 'C', 'D']
    colors = [
        [0xff, 0x00, 0x00],
        [0x00, 0xff, 0x00],
        [0x00, 0x00, 0xff]
    ]
    for ix, _type in enumerate(types):
        current_info = sv_regions[_type][0]
        current_folder = kml.add_folder(parent, name=f'Class {_type}')
        for _, row in current_info.iterrows():
            kml = _plot_single_bound(row, kml, current_folder, colors[ix])

    return kml


def create_terminal_data(kml_obj):
    terminal_folder = kml_obj.add_folder(name='Terminal')

    terminal = DataTools.Terminal()
    terminal.load_radars()
    terminal.load_radios()

    radar_folder = kml_obj.add_folder(terminal_folder, name='Radars')
    kml_obj = plot_radars_terminal(kml_obj, terminal.radars, radar_folder)

    radio_folder = kml_obj.add_folder(terminal_folder, name='Radios')
    kml_obj = plot_radios_terminal(kml_obj, terminal.radios, radio_folder)

    sv_folder = kml_obj.add_folder(terminal_folder, name='SV Bounds')
    kml_obj = plot_sv_bounds(terminal.airspace_info, kml_obj, sv_folder)

    return kml_obj


def main(file_name):
    """Main function"""
    kml_obj = KmlTools.KmlCreator()
    kml_obj.create_kml(file_name)
    # Terminal
    kml_obj = create_terminal_data(kml_obj)
    # EnRoute
    en_route = DataTools.EnRoute()
    en_route_folder = kml_obj.add_folder(name='En Route')
    kml_obj = plot_eram(en_route, kml_obj, en_route_folder)
    kml_obj.save()


if __name__ == '__main__':
    test_num = 1
    if test_num == 1:
        main('test.kml')
