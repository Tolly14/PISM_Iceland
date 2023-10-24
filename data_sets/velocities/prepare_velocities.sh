#!/bin/bash

# download file from https://zenodo.org/records/5517241

infile=iceland_iv_100m_s1_s20141001_e20201231_v1.0.nc
outfile=iceland_iv_100m_s1_s20141001_e20201231_v1.0_myear.nc

cdo -f nc4 -z zip_2 -O aexpr,"land_ice_surface_velocity_magnitude_stddev=sqrt(land_ice_surface_northing_stddev^2+land_ice_surface_easting_stddev^2)" -setattribute,land_ice_surface_easting_velocity@units="m year-1",land_ice_surface_northing_velocity@units="m year-1",land_ice_surface_vertical_velocity@units="m year-1",land_ice_surface_velocity_magnitude@units="m year-1",land_ice_surface_measurement_count@units="",land_ice_surface_easting_stddev@units="m year-1",land_ice_surface_northing_stddev@units="m year-1" -divc,28880.0 -mulc,31556926.0 $infile $outfile

x_min=530000.0
x_max=700000.0
y_min=360000.0
y_max=500000.0

for grid in 500 1000 2000 4000; do
    gdalwarp -r average -tr $grid $grid -overwrite -t_srs EPSG:3057 -of netCDF NETCDF:"$outfile":land_ice_surface_velocity_magnitude iceland_iv_100m_s1_s20141001_e20201231_v1.0_g${grid}m_land_ice_surface_velocity_magnitude.nc;
    gdalwarp -r average -tr $grid $grid -overwrite -t_srs EPSG:3057 -of netCDF NETCDF:"$outfile":land_ice_surface_velocity_magnitude_stddev iceland_iv_100m_s1_s20141001_e20201231_v1.0_g${grid}m_land_ice_surface_velocity_magnitude_stddev.nc;
    cdo -O merge -chname,Band1,land_ice_surface_velocity_magnitude_stddev iceland_iv_100m_s1_s20141001_e20201231_v1.0_g${grid}m_land_ice_surface_velocity_magnitude_stddev.nc -merge -chname,Band1,land_ice_surface_velocity_magnitude iceland_iv_100m_s1_s20141001_e20201231_v1.0_g${grid}m_land_ice_surface_velocity_magnitude.nc iceland_iv_100m_s1_s20141001_e20201231_v1.0_g${grid}m.nc
    
    gdalwarp -r average -tr $grid $grid -te $x_min $y_min $x_max $y_max -overwrite -t_srs EPSG:3057 -of netCDF NETCDF:"$outfile":land_ice_surface_velocity_magnitude vatnajoekull_iv_100m_s1_s20141001_e20201231_v1.0_g${grid}m_land_ice_surface_velocity_magnitude.nc;
    gdalwarp -r average -tr $grid $grid -te $x_min $y_min $x_max $y_max -tr $grid $grid -overwrite  -t_srs EPSG:3057 -of netCDF NETCDF:"$outfile":land_ice_surface_velocity_magnitude_stddev vatnajoekull_iv_100m_s1_s20141001_e20201231_v1.0_g${grid}m_land_ice_surface_velocity_magnitude_stddev.nc;
    cdo -O merge -chname,Band1,land_ice_surface_velocity_magnitude_stddev vatnajoekull_iv_100m_s1_s20141001_e20201231_v1.0_g${grid}m_land_ice_surface_velocity_magnitude_stddev.nc -merge -chname,Band1,land_ice_surface_velocity_magnitude vatnajoekull_iv_100m_s1_s20141001_e20201231_v1.0_g${grid}m_land_ice_surface_velocity_magnitude.nc vatnajoekull_iv_100m_s1_s20141001_e20201231_v1.0_g${grid}m.nc
done



