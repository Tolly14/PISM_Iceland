from argparse import ArgumentParser

from netCDF4 import Dataset as NC
import numpy as np

# set up the argument parser
parser = ArgumentParser()
parser.description = "Script to adjust PISM x,y coordinates for Iceland runs"
parser.add_argument("FILE", nargs=1)
options = parser.parse_args()

nc = NC(options.FILE[0], "a")

x = nc.variables["x"][:]
y = nc.variables["y"][:]

x0 = 324500
y0 = 324500

dx = 500
nx = len(x)
ny = len(y)

x = np.linspace(x0, x0 + (nx - 1) * dx, nx)
y = np.linspace(y0, y0 + (ny - 1) * dx, ny)

nc.variables["x"][:] = x
nc.variables["y"][:] = y 

if "mapping" in nc.variables:
    attributes = ["false_easting", 
                  "false_northing",
                  "latitude_of_projection_origin",
                  "standard_parallel",
                  "straight_vertical_longitude_from_pole"]

    mapping = nc.variables["mapping"]
    mapping.grid_mapping_name = "lambert_conformal_conic" ;
    mapping.longitude_of_central_meridian = -19.
    mapping.false_easting = 500000.
    mapping.false_northing = 500000.
    mapping.latitude_of_projection_origin = 65.
    mapping.standard_parallel = [64.25, 65.75]
    mapping.longitude_of_prime_meridian = 0.
    mapping.semi_major_axis = 6378137.
    mapping.inverse_flattening = 298.257222101

    nc.variables["mapping"] = mapping

else:

    print("Mapping variable not found. You may need to set the CRS in QGIS manually")

nc.close()
