# PISM_Iceland

First, create the bed and ice surface DEM

cd data_sets/bed_dem
sh prepare_all_iceland.sh /home/gua/Work/FraFP/Island-með-og-an-jokla ../shape_files/

cd data_sets/climate_forcing
sh prepare_harmonie.sh 