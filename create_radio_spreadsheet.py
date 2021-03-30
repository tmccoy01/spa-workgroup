import pandas as pd
import collections

from Libs import DataTools, constants


def main():
    """Create a spreadsheet for new radio .ter/.flr file creation"""
    radio_df = pd.read_csv(constants.RADIOS)
    radio_ids = radio_df['RSID'].to_list()
    radio_svs = [id.split('-')[0] for id in radio_ids]

    eram_data = DataTools.EnRoute()

    radio_sv_map = collections.defaultdict(list)
    for site in eram_data.sv_map.keys():
        radio_sv_map[site]


if __name__ == '__main__':
    main()
