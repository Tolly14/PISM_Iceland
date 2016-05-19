#!/bin/bash
set -x -e 

for year in 97 98 99 00 01 02 03 04 05 06 07 08 09 10 11 12 13 14; do
#for year in 97; do
    if [ $year  -gt 50 ]; then
	cen=19
    else
	cen=20
    fi
    gdal_translate -a_srs EPSG:3057 -of netCDF summer/Lbs${year}-0-fyllt.grd summer_${cen}${year}.nc
    ncrename -v Band1,climatic_mass_balance summer_${cen}${year}.nc 
    ncap2 -O -s "climatic_mass_balance=climatic_mass_balance" summer_${cen}${year}.nc summer_${cen}${year}.nc 
    ncatted -a standard_name,climatic_mass_balance,o,c,"land_ice_surface_specific_mass_balance_flux" -a units,climatic_mass_balance,o,c,"kg m-2 year-1" summer_${cen}${year}.nc
    gdal_translate -a_srs EPSG:3057 -of netCDF winter/Lbw${year}-0-fyllt.grd winter_${cen}${year}.nc
    ncrename -v Band1,climatic_mass_balance winter_${cen}${year}.nc 
    ncap2 -O -s "climatic_mass_balance=climatic_mass_balance" winter_${cen}${year}.nc winter_${cen}${year}.nc 
    ncatted -a standard_name,climatic_mass_balance,o,c,"land_ice_surface_specific_mass_balance_flux" -a units,climatic_mass_balance,o,c,"kg m-2 year-1" winter_${cen}${year}.nc
    cdo add summer_${cen}${year}.nc winter_${cen}${year}.nc smb_${cen}${year}.nc
done
rm summer_*.nc winter_*.nc

# sh prepare_temp_forcing.sh

ncks -A -v Lambert_Conformal smb_1997.nc t2m_iceland_ymean_1997-1-1_2015-1-1.nc 
ncatted -a mapping,T2m,o,c,"Lambert_Conformal" -a standard_name,x,o,c,"projection_x_coordinate" -a standard_name,y,o,c,"projection_y_coordinate" t2m_iceland_ymean_1997-1-1_2015-1-1.nc
ncks -O -v day,month,year -x t2m_iceland_ymean_1997-1-1_2015-1-1.nc climate_iceland_ymean_1997-1-1_2015-1-1.nc
ncrename -d t,time -v t,time -v T2m,ice_surface_temp climate_iceland_ymean_1997-1-1_2015-1-1.nc
python add_timebounds.py climate_iceland_ymean_1997-1-1_2015-1-1.nc
cdo -b F32 copy  climate_iceland_ymean_1997-1-1_2015-1-1.nc  tmp_climate_iceland_ymean_1997-1-1_2015-1-1.nc
ncap2 -O -s "x=x*1e3; y=y*1e3;" tmp_climate_iceland_ymean_1997-1-1_2015-1-1.nc tmp_climate_iceland_ymean_1997-1-1_2015-1-1.nc
ncatted -a units,ice_surface_temp,o,c,"Celsius" -a units,x,o,c,"m" -a units,y,o,c,"m" tmp_climate_iceland_ymean_1997-1-1_2015-1-1.nc
mv tmp_climate_iceland_ymean_1997-1-1_2015-1-1.nc climate_iceland_ymean_1997-1-1_2015-1-1.nc
ncks -O smb_1997.nc langjokull_g100m.nc
nc2cdo.py --srs EPSG:3057 langjokull_g100m.nc
nc2cdo.py --srs EPSG:3057 climate_iceland_ymean_1997-1-1_2015-1-1.nc
cdo remapbil,langjokull_g100m.nc climate_iceland_ymean_1997-1-1_2015-1-1.nc climate_langjokull_ymean_1997-1-1_2015-1-1.nc
ncks -A -v x,y,Lambert_Conformal  langjokull_g100m.nc climate_langjokull_ymean_1997-1-1_2015-1-1.nc
ncatted -a mapping,ice_surface_temp,o,c,"Lambert_Conformal" climate_langjokull_ymean_1997-1-1_2015-1-1.nc 
python create_climate_forcing.py -i climate_langjokull_ymean_1997-1-1_2015-1-1.nc smb_*.nc
