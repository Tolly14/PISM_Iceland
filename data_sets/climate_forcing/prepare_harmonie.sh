#!/bin/bash

hdir=/Volumes/helheim/smb_offline/Exps/HARMONIE_glac_corr/Output/Daily2D/
if [ ! -z "$1" ]
  then
      hdir=$1
fi

mkdir -p harmonie

for year in {1980..2016}; do
    cdo selvar,tas,gld -mergetime ${hdir}/Daily2D_${year}*.nc harmonie/HARMONIE_glac_corr_${year}.nc
done
cdo setgrid,../../grids/harmonie.txt -mergetime harmonie/HARMONIE_glac_corr_*.nc HARMONIE_glac_corr_1980_2016_DM.nc
adjust_timeline.py -d 1980-1-1 -a 1980-1-1 -p daily HARMONIE_glac_corr_1980_2016_DM.nc
