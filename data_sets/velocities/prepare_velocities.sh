#!/bin/bash

# download file from https://zenodo.org/records/5517241

infile=iceland_iv_100m_s1_s20141001_e20201231_v1.0.nc
outfile=iceland_iv_100m_s1_s20141001_e20201231_v1.0_myear.nc

cdo -O setattribute,land_ice_surface_easting_velocity@units="m year-1",land_ice_surface_northing_velocity@units="m year-1",land_ice_surface_vertical_velocity@units="m year-1",land_ice_surface_velocity_magnitude@units="m year-1",land_ice_surface_measurement_count@units="",land_ice_surface_easting_stddev@units="m year-1",land_ice_surface_northing_stddev@units="m year-1" -divc,28880 -mulc,31556926 $infile $outfile


for grid in 500 1000 2000 4000; do
    cdo -O -f nc4 -z zip_2 remapycon,../../grids/pism_iceland_g${grid}m.txt $infile iceland_iv_100m_s1_s20141001_e20201231_v1.0_g${grid}m.nc
done
