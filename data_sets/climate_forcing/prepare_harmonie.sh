#!/bin/bash

hdir=/media/gua/LSS_backup_drive/smb_offline/Exps/HARMONIE_glac_corr/Output/Daily2D/
if [ ! -z "$1" ]
  then
      hdir=$1
fi

mkdir -p harmonie

# There are too many files to process in one go, we thus process the files by year.
# Merge files, set the grid, change the variable name and set the missing value
for year in {1980..2016}; do
    echo "Processing $year"
    cdo -O setmisstoc,273.15  -chname,tas,ice_surface_temp -selvar,tas, -setgrid,../../grids/harmonie.txt -mergetime ${hdir}/Daily2D_${year}*.nc harmonie/tas_HARMONIE_glac_corr_${year}.nc
    cdo -O setmisstoc,0 -setattribute,climatic_mass_balance@units="kg m-2 day-1" -chname,gld,climatic_mass_balance -selvar,gld -setgrid,../../grids/harmonie.txt -mergetime ${hdir}/Daily2D_${year}*.nc harmonie/gld_HARMONIE_glac_corr_${year}.nc
done

# Merge the files seperately for climatic_mass_balance and ice_surface_temp
cdo -O -f nc4 -z zip_3 mergetime harmonie/gld_HARMONIE_glac_corr_*.nc gld_HARMONIE_glac_corr_1980_2016_DM.nc
cdo -O -f nc4 -z zip_3 mergetime harmonie/tas_HARMONIE_glac_corr_*.nc tas_HARMONIE_glac_corr_1980_2016_DM.nc
# Merge climatic_mass_balance and ice_surface_temp
cdo -O -f nc4 -z zip_3 merge gld_HARMONIE_glac_corr_1980_2016_DM.nc tas_HARMONIE_glac_corr_1980_2016_DM.nc HARMONIE_glac_corr_1980_2016_DM.nc

# Remove missing value attributes
ncatted -a _FillValue,climatic_mass_balance,d,, -a missing_value,climatic_mass_balance,d,, -a _FillValue,ice_surface_temp,d,, -a missing_value,ice_surface_temp,d,, HARMONIE_glac_corr_1980_2016_DM.nc
# Fix the time axis
adjust_timeline.py -d 1980-1-1 -a 1980-1-1 -p daily HARMONIE_glac_corr_1980_2016_DM.nc

# Monthly means (ice_surface_temp) and sums (climatic_mass_balance)
cdo -O -f nc4 -z zip_3 merge -monsum -selvar,climatic_mass_balance HARMONIE_glac_corr_1980_2016_DM.nc -monmean -selvar,ice_surface_temp HARMONIE_glac_corr_1980_2016_DM.nc HARMONIE_glac_corr_1980_2016_MM.nc
# Yearly means (ice_surface_temp) and sums (climatic_mass_balance)
cdo -O -f nc4 -z zip_3 merge -yearsum -selvar,climatic_mass_balance HARMONIE_glac_corr_1980_2016_DM.nc -yearmean -selvar,ice_surface_temp HARMONIE_glac_corr_1980_2016_DM.nc HARMONIE_glac_corr_1980_2016_YM.nc
cdo -O -f nc4 -z zip_3 timmean HARMONIE_glac_corr_1980_2016_YM.nc HARMONIE_glac_corr_1980_2016_TM.nc
