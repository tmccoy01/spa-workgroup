from Libs import (
    DataTools,
    KmlTools
)


def plot_eram():
    """Test to load and plot the ERAM areas"""
    # First load in the data
    data = DataTools.Importer()
    data.load_eram()
    data.load_radars()
    # Create a kml object
    kml = KmlTools.KmlCreator()
    kml.create_kml('please.kml')
    # Get all the sites and loop through them
    artcc_sites = list(data.eram_bounds.keys())
    eram_folder = kml.add_folder(name="ERAM Boundaries")
    for site in artcc_sites:
        curr_radars = data.radar_info[data.radar_info.Airspace_ID == site]
        temp_node = kml.add_folder(parent_folder=eram_folder, name=site)
        # Plot the radars for the current ARTCC region
        for ix, row in curr_radars.iterrows():
            kml.add_point(
                row['Radar_Lat'],
                row['Radar_Lon'],
                parent_node=temp_node,
                color=[0xff, 0x00, 0x00],
                name=row['Radar_ID'],
                description=str(row['SSR Type']) + "_" + str(row['PSR Type']) + "/n" + row['Radar_Name']
            )
        # Plot the ARTCC region boundary
        kml.add_polygon(
            data.eram_bounds[site],
            filled=False,
            parent_node=temp_node,
            color=[0xff, 0x00, 0x00],
            opacity=100,
            line_width=3
        )

    kml.save()


if __name__ == '__main__':
    plot_eram()

