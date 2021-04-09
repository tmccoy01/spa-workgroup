import DataTools, constants


def main():
    eram = DataTools.EnRoute()
    eram.load_radios()
    eram.radios = eram.radios[
        [
            'RSID',
            'Latitude\n(Degrees)',
            'Longitude\n(Degrees)',
            'Site Elevation (MSL)',
            'Antenna Height (AGL)'
        ]
    ]

    eram.radios.columns = ['rsName', 'Lat', 'Lon', 'Ter Elev', 'Ant Elev']

    eram.radios['Ter Elev'] = eram.radios['Ter Elev'] / constants.METERS_TO_FEET
    eram.radios['Ant Elev'] = (eram.radios['Ant Elev'] / constants.METERS_TO_FEET) + eram.radios['Ter Elev']
    eram.radios['Range'] = 200

    eram.radios.to_csv('eram_needed_radios.csv')


if __name__ == '__main__':
    main()
