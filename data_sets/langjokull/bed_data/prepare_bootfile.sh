#!/bin/bash
set -x -e 

gdal_translate -a_srs EPSG:3057 -of netCDF LaBotnLand100x100.grd pism_Langjokull_bed.nc
ncrename -v Band1,topg pism_Langjokull_bed.nc
ncatted -a standard_name,topg,o,c,"bedrock_altitude" -a units,topg,o,c,"m" pism_Langjokull_bed.nc

for year in 1937 1945 1986 1997 2004; do
# 2007 and 2012 have different dims
    echo $year
    gdal_translate -a_srs EPSG:3057 -of netCDF La${year}-100x100.grd pism_Langjokull_${year}.nc
    ncrename -v Band1,usurf pism_Langjokull_${year}.nc
    ncatted -a standard_name,usurf,o,c,"surface_altitude" -a units,usurf,o,c,"m" pism_Langjokull_${year}.nc
    ncks -A -v topg pism_Langjokull_bed.nc pism_Langjokull_${year}.nc
    ncap2 -O -s "thk=usurf-topg; where(thk<0) thk=0;" pism_Langjokull_${year}.nc pism_Langjokull_${year}.nc
    ncatted -a standard_name,thk,o,c,"land_ice_thickness" -a _FillValue,thk,d,, -a _FillValue,usurf,d,, -a _FillValue,topg,d,, pism_Langjokull_${year}.nc
    ncap2 -O -s "where(thk>4000) {thk=0; usurf=0;}; mask=topg*0; mask=mask+1;" pism_Langjokull_${year}.nc pism_Langjokull_${year}.nc
    
done

