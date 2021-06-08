import pandas as pd
from pandas import ExcelWriter
from Libs import DataTools, constants


def make_radios_needed_spreadsheet(radios_needed: list) -> None:
    """Create a spreadsheet formatted correctly for floor file creation"""
    eram = DataTools.EnRoute()
    eram.load_radios()
    eram.radios = eram.radios[
        [
            "RSID",
            "Latitude\n(Degrees)",
            "Longitude\n(Degrees)",
            "Site Elevation (MSL)",
            "Antenna Height (AGL)",
        ]
    ]

    eram.radios.columns = ["rsName", "Lat", "Lon", "Ter Elev", "Ant Elev"]

    eram.radios = eram.radios[eram.radios["rsName"].isin(radios_needed)]

    eram.radios["Ter Elev"] = eram.radios["Ter Elev"] / constants.METERS_TO_FEET
    eram.radios["Ant Elev"] = (
        eram.radios["Ant Elev"] / constants.METERS_TO_FEET
    ) + eram.radios["Ter Elev"]
    eram.radios["Range"] = 200

    eram.radios.to_csv("eram_needed_radios.csv", index_label=False)


def get_radios(data_df: pd.DataFrame, site: str) -> list:
    pass


def get_radars(enroute_df: pd.DataFrame, term_df: pd.DataFrame, site: str) -> list:
    enroute_radars = enroute_df[enroute_df["Airspace_ID"] == site]["Radar_ID"].to_list()
    term_radars = term_df[term_df["Airspace_ID"] == site]["Radar_ID"].to_list()

    return enroute_radars + term_radars


def create_sensor_list():
    enroute = DataTools.EnRoute()
    enroute.load_radars()
    term = DataTools.Terminal()
    term.load_radars()
    writer = ExcelWriter("sensor_list.xlsx")
    for site in constants.ERAM_SITES:
        print(site)
        enroute.load_radios(_filter=site)
        curr_radios = enroute.radios["RSID"].to_list()
        curr_radars = get_radars(enroute.radars, term.radars, site)

        radar_df = pd.DataFrame({'radars': curr_radars})
        radio_df = pd.DataFrame({'radios': curr_radios})
        df = pd.concat([radar_df, radio_df], ignore_index=False, axis=1)

        df.to_excel(writer, sheet_name=site, index=False)

    writer.save()


if __name__ == "__main__":
    create_sensor_list()
