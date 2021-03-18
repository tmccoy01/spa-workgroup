from Libs import (
    DataTools,
    KmlTools
)


def plot_eram():
    """Test to load and plot the ERAM areas"""
    # First load in the data
    data = DataTools.Importer()
    data.load_eram()
    # Create a kml object
    kml = KmlTools.KmlCreator()
    kml.create_kml('test.kml')
    # Get all the sites and loop through them
    artcc_sites = list(data.eram_bounds.keys())
    eram_folder = kml.add_folder(name="ERAM Boundaries")
    for site in artcc_sites:
        temp_node = kml.add_folder(parent_folder=eram_folder, name=site)
        kml.add_polygon(
            data.eram_bounds[site],
            filled=False,
            parent_node=temp_node,
            color=[0xff, 0x00, 0x00],
            opacity=100,
        )

    kml.save()


if __name__ == '__main__':
    plot_eram()
