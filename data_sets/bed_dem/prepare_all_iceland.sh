#!/bin/bash
set -x -e 

indir="$1"
rgidir="$2"
echo $1
echo $2
gdal_translate -a_srs EPSG:3057 -of netCDF ${indir}/island500x500_an_jökla_landgrunni93.grd pism_Iceland_bed.nc
ncrename -v Band1,topg pism_Iceland_bed.nc
ncatted -a standard_name,topg,o,c,"bedrock_altitude" -a units,topg,o,c,"m" pism_Iceland_bed.nc

cut="-cutline 06_rgi60_Iceland_fixed.shp"
gdalwarp -overwrite -srcnodata 1.70141e+38 -dstnodata 0 -s_srs EPSG:3057 $cut -of netCDF ${indir}/island500x500.grd pism_Iceland_1993.nc
ncrename -v Band1,usurf pism_Iceland_1993.nc
ncatted -a standard_name,usurf,o,c,"surface_altitude" -a units,usurf,o,c,"m" pism_Iceland_1993.nc
ncks -A -v topg pism_Iceland_bed.nc pism_Iceland_1993.nc
ncap2 -O -s "thk=usurf-topg; where(thk<0) thk=0; where(usurf<=0) thk=0;" pism_Iceland_1993.nc pism_Iceland_1993.nc
ncatted -a standard_name,thk,o,c,"land_ice_thickness" -a _FillValue,thk,d,, -a _FillValue,usurf,d,, -a _FillValue,topg,d,, pism_Iceland_1993.nc
    

