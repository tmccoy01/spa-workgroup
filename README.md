# spa-workgroup

## Libs

### constants
Holds all paths and constants for the given analysis

### DataTools
Helper classes for importing and parsing data

### GeoTools
Class for lat/lon conversions, distances, and other geocentric calculations

### KmlTools
Helper classes to act as a simple wrapper for _pykml_
- **Parser**
    - Parses kml files from the given _file_name_
    - Can find regions inside a larger polygon
- **KmlCreator**
    - Create kml files with various different features
    - Simple OOP interface
