#!/bin/bash
set -x -e 

grid=100
python ../../../scripts/create_langjokull_epsg3057_grid.py -g $grid langjokull_g${grid}m.nc

for year in 97 98 99 00 01 02 03 04 05 06 07 08 09 10 11 12 13 14; do
    if [ $year  -gt 50 ]; then
	cen=19
    else
	cen=20
    fi
    gdal_translate -a_srs EPSG:3057 -of netCDF summer/Lbs${year}-0-fyllt.grd summer_${cen}${year}.nc
    ncks -A -v mapping langjokull_g${grid}m.nc summer_${cen}${year}.nc    
    ncatted -a grid_mapping,Band1,o,c,"mapping" summer_${cen}${year}.nc
    ncks -O -v Lambert_Conformal -x summer_${cen}${year}.nc summer_${cen}${year}.nc  
    ncrename -v Band1,climatic_mass_balance summer_${cen}${year}.nc
    ncap2 -O -s "climatic_mass_balance=climatic_mass_balance*910;" summer_${cen}${year}.nc summer_${cen}${year}.nc 
    ncatted -a standard_name,climatic_mass_balance,o,c,"land_ice_surface_specific_mass_balance_flux" -a units,climatic_mass_balance,o,c,"kg m-2 year-1" summer_${cen}${year}.nc
    gdal_translate -a_srs EPSG:3057 -of netCDF winter/Lbw${year}-0-fyllt.grd winter_${cen}${year}.nc
    ncks -A -v mapping langjokull_g${grid}m.nc winter_${cen}${year}.nc    
    ncatted -a grid_mapping,Band1,o,c,"mapping" winter_${cen}${year}.nc
    ncks -O -v Lambert_Conformal -x winter_${cen}${year}.nc winter_${cen}${year}.nc  
    ncrename -v Band1,climatic_mass_balance winter_${cen}${year}.nc 
    ncap2 -O -s "climatic_mass_balance=climatic_mass_balance" winter_${cen}${year}.nc winter_${cen}${year}.nc 
    ncatted -a standard_name,climatic_mass_balance,o,c,"land_ice_surface_specific_mass_balance_flux" -a units,climatic_mass_balance,o,c,"kg m-2 year-1" winter_${cen}${year}.nc
    cdo add summer_${cen}${year}.nc winter_${cen}${year}.nc smb_${cen}${year}.nc
    nc2cdo.py --srs EPSG:3057 smb_${cen}${year}.nc
    if [ $year  == 97 ]; then
	cdo genbil,langjokull_g${grid}m.nc smb_${cen}${year}.nc remapweights_g${grid}m.nc
    fi
    cdo remap,langjokull_g${grid}m.nc,remapweights_g${grid}m.nc smb_${cen}${year}.nc smb_g${grid}m_${cen}${year}.nc
    ncks -A -v mapping langjokull_g${grid}m.nc smb_g${grid}m_${cen}${year}.nc
    ncatted -a grid_mapping,climatic_mass_balance,o,c,"mapping" smb_g${grid}m_${cen}${year}.nc
done
rm summer_*.nc winter_*.nc

# sh prepare_temp_forcing.sh

ncks -A -v mapping langjokull_g${grid}m.nc t2m_iceland_ymean_1997-1-1_2015-1-1.nc 
ncatted -a grid_mapping,T2m,o,c,"mapping" -a mapping,T2m,d,, -a standard_name,x,o,c,"projection_x_coordinate" -a standard_name,y,o,c,"projection_y_coordinate" t2m_iceland_ymean_1997-1-1_2015-1-1.nc
ncks -O -v day,month,year -x t2m_iceland_ymean_1997-1-1_2015-1-1.nc climate_iceland_ymean_1997-1-1_2015-1-1.nc
ncrename -d t,time -v t,time -v T2m,ice_surface_temp climate_iceland_ymean_1997-1-1_2015-1-1.nc
python add_timebounds.py climate_iceland_ymean_1997-1-1_2015-1-1.nc
cdo -b F32 copy  climate_iceland_ymean_1997-1-1_2015-1-1.nc  tmp_climate_iceland_ymean_1997-1-1_2015-1-1.nc
ncap2 -O -s "x=x*1e3; y=y*1e3;" tmp_climate_iceland_ymean_1997-1-1_2015-1-1.nc tmp_climate_iceland_ymean_1997-1-1_2015-1-1.nc
ncatted  -a grid_mapping,ice_surface_temp,o,c,"mapping" -a units,ice_surface_temp,o,c,"Celsius" -a units,x,o,c,"m" -a units,y,o,c,"m" tmp_climate_iceland_ymean_1997-1-1_2015-1-1.nc
mv tmp_climate_iceland_ymean_1997-1-1_2015-1-1.nc climate_iceland_ymean_1997-1-1_2015-1-1.nc
nc2cdo.py --srs EPSG:3057 climate_iceland_ymean_1997-1-1_2015-1-1.nc
ncks -A -v mapping langjokull_g${grid}m.nc climate_iceland_ymean_1997-1-1_2015-1-1.nc 
cdo remapbil,langjokull_g${grid}m.nc climate_iceland_ymean_1997-1-1_2015-1-1.nc climate_langjokull_${grid}m_ymean_1997-1-1_2015-1-1.nc
ncks -A -v x,y,mapping  langjokull_g${grid}m.nc climate_langjokull_${grid}m_ymean_1997-1-1_2015-1-1.nc
ncatted -a grid_mapping,ice_surface_temp,o,c,"mapping" climate_langjokull_${grid}m_ymean_1997-1-1_2015-1-1.nc 
python create_climate_forcing.py -i climate_langjokull_${grid}m_ymean_1997-1-1_2015-1-1.nc smb_g${grid}m_*.nc
ncatted -a missing_value,ice_surface_temp,d,, -a _FillValue,ice_surface_temp,d,, -a _FillValue,climatic_mass_balance,d,, climate_langjokull_${grid}m_ymean_1997-1-1_2015-1-1.nc
ncap2 -O -s "where(climatic_mass_balance>1e20) climatic_mass_balance=0.;" climate_langjokull_${grid}m_ymean_1997-1-1_2015-1-1.nc climate_langjokull_${grid}m_ymean_1997-1-1_2015-1-1.nc

# Create time mean
cdo timmean  climate_langjokull_${grid}m_ymean_1997-1-1_2015-1-1.nc climate_langjokull_${grid}m_mean_1997-1-1_2015-1-1.nc
ncatted -a grid_mapping,ice_surface_temp,o,c,"mapping" -a grid_mapping,climatic_mass_balance,o,c,"mapping" climate_langjokull_${grid}m_mean_1997-1-1_2015-1-1.nc
ncks -A -v x,y,mapping langjokull_g${grid}m.nc climate_langjokull_${grid}m_mean_1997-1-1_2015-1-1.nc
ncks -O -v climatic_mass_balance climate_langjokull_${grid}m_mean_1997-1-1_2015-1-1.nc smb_langjokull_${grid}m_mean_1997-1-1_2015-1-1.nc
ncks -O -v ice_surface_temp climate_langjokull_${grid}m_mean_1997-1-1_2015-1-1.nc t2m_langjokull_${grid}m_mean_1997-1-1_2015-1-1.nc
ncrename -d x_2,x -d y_2,y t2m_langjokull_${grid}m_mean_1997-1-1_2015-1-1.nc
ncks -O smb_langjokull_${grid}m_mean_1997-1-1_2015-1-1.nc climate_langjokull_${grid}m_mean_1997-1-1_2015-1-1.nc
ncks -A -v ice_surface_temp t2m_langjokull_${grid}m_mean_1997-1-1_2015-1-1.nc climate_langjokull_${grid}m_mean_1997-1-1_2015-1-1.nc
ncks -A -v mapping langjokull_g${grid}m.nc climate_langjokull_${grid}m_mean_1997-1-1_2015-1-1.nc
