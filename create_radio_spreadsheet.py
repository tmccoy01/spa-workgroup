"""This file is just a simple script to grab all necessary radios needed to recreate at 200NM"""

from Libs.constants import RADIOS
from Libs.DataTools import Parser


def main():
    """Create a spreadsheet for new radio .ter/.flr file creation"""
    radios = Parser()
    radios.load_data()

