# PISM_Iceland

First, create the bed and ice surface DEM

cd data_sets/bed_dem
sh prepare_all_iceland.sh /home/gua/Work/FraFP/Island-með-og-an-jokla ../shape_files/

cd data_sets/climate_forcing
sh prepare_harmonie.sh


To copy forcing data to husbondi:

rsync -rvu --progress /home/gua/Work/PISM/PISM_Iceland/data_sets/bed_dem/pism_g*2010.nc  gua@husbondi.rhi.hi.is:/mnt/storage/gua/PISM_Iceland/data_sets/bed_dem/


rsync -rvu --progress /home/gua/Work/PISM/PISM_Iceland/data_sets/climate_forcing/HAR*.nc  gua@husbondi.rhi.hi.is:/mnt/storage/gua/PISM_Iceland/data_sets/climate_forcing/

To get files from husbondi
rsync -rvu --progress  gua@husbondi.rhi.hi.is:/mnt/storage/gua/PISM_Iceland/initialization/2021_10_hybrid .
