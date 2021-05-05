""" Using example MCC dataset """

import mat73

# Load in dataset
data_dict = mat73.loadmat('../data/SECTORS.mat', use_attrdict=True)
data_struct = data_dict['SECTORS']
# Parse dataset
region_lats = data_struct['Lat'][6]
region_lons = data_struct['Lon'][6]
region_min_alts = data_struct['Min_Alt_Feet'][6]
region_max_alts = data_struct['Max_Alt_Feet'][6]
# Create kml plots

