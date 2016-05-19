#!/bin/bash
set -x -e 

gdal_translate -a_srs EPSG:3057 -of netCDF Botn/LaBotnLand100x100.grd pism_Langjokull_bed.nc
ncrename -v Band1,topg pism_Langjokull_bed.nc
ncatted -a standard_name,topg,o,c,"bedrock_altitude" -a units,topg,o,c,"m" pism_Langjokull_bed.nc

for year in 1937 1945 1986 1997 2004; do
# 2007 and 2012 have different dims
    echo $year
    gdal_translate -a_srs EPSG:3057 -of netCDF Yfirbord/La${year}-100x100.grd pism_Langjokull_${year}.nc
    ncrename -v Band1,usurf pism_Langjokull_${year}.nc
    ncatted -a standard_name,usurf,o,c,"surface_altitude" -a units,usurf,o,c,"m" pism_Langjokull_${year}.nc
    ncks -A -v topg pism_Langjokull_bed.nc pism_Langjokull_${year}.nc
    ncap2 -O -s "thk=usurf-topg; where(thk<0) thk=0;" pism_Langjokull_${year}.nc pism_Langjokull_${year}.nc
done

for year in 97 98 99 00 01 02 03 04 05 06 07 08 09 10 11 12 13 14; do
#for year in 97; do
    if [ $year  -gt 50 ]; then
	cen=19
    else
	cen=20
    fi
    gdal_translate -a_srs EPSG:3057 -of netCDF Langjo-Afkomu-meðaltöl/Sumar/Lbs${year}-0-fyllt.grd summer_${cen}${year}.nc
    ncrename -v Band1,climatic_mass_balance summer_${cen}${year}.nc 
    ncap2 -O -s "climatic_mass_balance=climatic_mass_balance" summer_${cen}${year}.nc summer_${cen}${year}.nc 
    ncatted -a standard_name,climatic_mass_balance,o,c,"land_ice_surface_specific_mass_balance_flux" -a units,climatic_mass_balance,o,c,"kg m-2 year-1" summer_${cen}${year}.nc
    gdal_translate -a_srs EPSG:3057 -of netCDF Langjo-Afkomu-meðaltöl/Vetur/Lbw${year}-0-fyllt.grd winter_${cen}${year}.nc
    ncrename -v Band1,climatic_mass_balance winter_${cen}${year}.nc 
    ncap2 -O -s "climatic_mass_balance=climatic_mass_balance" winter_${cen}${year}.nc winter_${cen}${year}.nc 
    ncatted -a standard_name,climatic_mass_balance,o,c,"land_ice_surface_specific_mass_balance_flux" -a units,climatic_mass_balance,o,c,"kg m-2 year-1" winter_${cen}${year}.nc
    cdo add summer_${cen}${year}.nc winter_${cen}${year}.nc smb_${cen}${year}.nc
done
