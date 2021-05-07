import pandas as pd
from Libs import DataTools, KmlTools, GeoTools, constants

_geo = GeoTools.Geo()


def get_indexes(sensor_data: pd.DataFrame, sensor_type: str) -> dict:
    """return the indexes for the given sensor type"""
    filter_idx = {}
    all_types = set(sensor_data[sensor_type].to_list())
    for _type in all_types:
        if pd.isna(_type):
            filter_idx["N/A"] = pd.isna(sensor_data[sensor_type])
        else:
            # idx = sensor_data.index
            # tf = sensor_data[sensor_type] == _type
            # filter_idx[_type] = idx[tf]
            filter_idx[_type] = sensor_data[sensor_type] == _type

    return filter_idx


def filter_sensor_data(sensor_data: pd.DataFrame, sensor_type: str):
    """return a dict of dataframes for the given sensor_type"""
    filtered_idx = get_indexes(sensor_data, sensor_type)
    filtered_dict = {}
    for _type, idx in filtered_idx.items():
        filtered_dict[_type] = sensor_data[idx]

    return filtered_dict


def plot_single_sensor_type(kml, sensor_data: pd.DataFrame, parent: str):
    """not yet implemented"""
    pass


def plot_sensor_types(kml, data: pd.DataFrame, parent: str, sensor_type: str = "radar"):
    """plot each sensor type so that it can be individually turned on and off"""
    sensor_type_folder = kml.add_folder(parent, name="Sensor Types")
    sensor_types = {
        "radar": ["PSR Type", "SSR Type"],
        "radio": ["Antenna Types", "1090ES Variant"],
    }

    if "radar" in sensor_type.lower():
        sensor_data = data.radars
    else:
        sensor_data = data.radios

    for _type in sensor_types[sensor_type.lower()]:
        curr_folder = kml.add_folder(parent_folder=sensor_type_folder, name=_type)
        curr_sensor_types = filter_sensor_data(sensor_data, sensor_type=_type)
        kml = plot_single_sensor_type(
            kml, sensor_data=curr_sensor_types, parent=curr_folder
        )

    return kml


def plot_eram(data, kml, parent):
    """Test to load and plot the ERAM areas"""
    eram_folder = kml.add_folder(parent, name="ERAM Boundaries")
    data.load_radars()
    data.load_radios()
    for site in constants.ERAM_SITES:
        curr_sv = int(data.sv_map[site])
        curr_radars = data.radars[data.radars.Airspace_ID == site]
        curr_radios = data.radios[data.radios["Enclosed By SV.1"] == curr_sv]
        temp_node = kml.add_folder(eram_folder, name=site)
        # Plot the radars for the current ARTCC region
        radar_node = kml.add_folder(temp_node, name="Radars")
        kml = _plot_radars(kml, sensors=curr_radars, node=radar_node)
        # Plot the radios for the current ARTCC region
        radio_node = kml.add_folder(temp_node, name="Radios")
        kml = _plot_radios(kml, sensors=curr_radios, node=radio_node)

    # Plots for individual sensor types
    kml = plot_sensor_types(kml, data, parent=eram_folder)

    return kml


def plot_stars(data, kml, parent):
    """placeholder for later implementation"""
    pass


def _plot_radios(kml, sensors, node):
    for ix, row in sensors.iterrows():
        if (
            row["Operational Status"] == "Operational"
            and row["ADS-B/WAM Usage"] == "ADS-B"
        ):
            if "Thales" in row["Radio Variant"]:
                shape = "circle"
            else:
                shape = constants.RADIO_SHAPES[row["Radio Variant"]]

            color = constants.RADIO_COLORS[row["1090ES Antenna"]]

            kml.add_special(
                row["Latitude\n(Degrees)"],
                row["Longitude\n(Degrees)"],
                base_shape="square",
                parent_node=node,
                color=color,
                shape=shape,
                name=row["RSID"],
                description=str(row["LID\n(GBT/[MRU])"])
                + " "
                + row["Facility Location"],
            )

    return kml


def _plot_radars(kml, all_data, node):
    """plot radar locations and types"""

    all_radar_folder = kml.add_folder(parent_folder=node, name="All")
    sensors = all_data.radars
    for ix, row in sensors.iterrows():
        if pd.isna(row["PSR Type"]):
            shape = "blank"
        else:
            shape = constants.RADAR_SHAPES[row["PSR Type"]]

        color = constants.RADAR_COLORS[row["SSR Type"]]

        kml.add_special(
            row["Radar_Lat"],
            row["Radar_Lon"],
            base_shape="paddle",
            parent_node=node,
            color=color,
            shape=shape,
            name=row["Radar_ID"],
            description=str(row["SSR Type"])
            + "_"
            + str(row["PSR Type"])
            + "\n"
            + row["Radar_Name"],
        )

    kml = plot_sensor_types(kml, all_data, parent=node, sensor_type="radar")

    return kml


def _plot_single_bound(sensor_info, kml, parent, color):
    lat_lon = _geo.lat_lon_circle(
        sensor_info["SV_Lat"],
        sensor_info["SV_Lon"],
        radius_nmi=sensor_info["SV_Range_NM"],
    )
    kml.add_polygon(
        lat_lon,
        parent_node=parent,
        color=color,
        line_width=3,
        opacity=30,
        name=sensor_info["Arpt_Name"],
    )

    return kml


def plot_sv_bounds(sv_regions, kml, parent):
    types = ["B", "C", "D"]
    colors = [[0xFF, 0x00, 0x00], [0x00, 0xFF, 0x00], [0x00, 0x00, 0xFF]]
    for ix, _type in enumerate(types):
        current_info = sv_regions[_type][0]
        current_folder = kml.add_folder(parent, name=f"Class {_type}")
        for _, row in current_info.iterrows():
            kml = _plot_single_bound(row, kml, current_folder, colors[ix])

    return kml


def create_terminal_data(kml_obj):
    terminal_folder = kml_obj.add_folder(name="Terminal")

    terminal = DataTools.Terminal()
    terminal.load_radars()
    terminal.load_radios()

    radar_folder = kml_obj.add_folder(terminal_folder, name="Radars")
    kml_obj = _plot_radars(kml_obj, all_data=terminal, node=radar_folder)

    radio_folder = kml_obj.add_folder(terminal_folder, name="Radios")
    kml_obj = _plot_radios(kml_obj, sensors=terminal, node=radio_folder)

    sv_folder = kml_obj.add_folder(terminal_folder, name="SV Bounds")
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
    en_route_folder = kml_obj.add_folder(name="En Route")
    kml_obj = plot_eram(en_route, kml_obj, en_route_folder)
    kml_obj.save()


if __name__ == "__main__":
    test_num = 1
    if test_num == 1:
        main("test.kml")
