from argparse import ArgumentParser

from netCDF4 import Dataset as NC
import numpy as np
from pyproj import Proj

p = Proj("+init=epsg:3057")

xm, ym = p(-19., 64.7)

# set up the argument parser
parser = ArgumentParser()
parser.description = "Script to adjust PISM x,y coordinates for Iceland runs"
parser.add_argument("FILE", nargs=1)
options = parser.parse_args()

ne = 289
nn = 229
dx = 2500

easting = np.linspace(xm - (ne - 1) / 2  * dx, xm + (ne - 1) / 2  * dx, ne)
northing = np.linspace(ym - (nn - 1) / 2  * dx, ym + (nn - 1) / 2 * dx, nn)

print(easting[0], northing[0])

nc = NC(options.FILE[0], "a")

if "x" not in nc.dimensions:
    nc.createDimension("x", size=ne)
if "y" not in nc.dimensions:
    nc.createDimension("y", size=nn)

var = "x"
if var not in nc.variables:
    var_out = nc.createVariable(var, "d", dimensions=("x"))
else:
    var_out = nc.variables[var]
var_out.axis = "X"
var_out.long_name = "X-coordinate in Cartesian system"
var_out.standard_name = "projection_x_coordinate"
var_out.units = "meters"
var_out[:] = easting

var = "y"
if var not in nc.variables:
    var_out = nc.createVariable(var, "d", dimensions=("y"))
else:
    var_out = nc.variables[var]
var_out.axis = "Y"
var_out.long_name = "Y-coordinate in Cartesian system"
var_out.standard_name = "projection_y_coordinate"
var_out.units = "meters"
var_out[:] = northing

if "mapping" not in nc.variables:
    mapping = nc.createVariable("mapping", "c")
else:
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


nc.close()
