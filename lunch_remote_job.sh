#!/bin/bash

storage="/storage/ccmmma/prometeo/data/opendap/apps/smoketracer"
dir_smoketracer_frontend="/home/ccmmma/prometeo/apps/smoketracer"

# su fumi2 -c "ssh -o StrictHostKeyChecking=no d.caramiello@193.205.230.5 \"export PATH=$PATH:/usr/sbin; mkdir -p $storage/USER/DATE_CODICECOMUNE/out; module load slurm; source $dir_smoketracer_frontend/etc/profile; cd $dir_smoketracer_frontend; ./smoketracer LON LAT DATe HOURS TEMPERATURE $storage/USER/DATE_CODICECOMUNE; \" " &
su fumi2 -c "ssh -o StrictHostKeyChecking=no ccmmma@193.205.230.5 \"export PATH=$PATH:/usr/sbin; mkdir -p $storage/USER/DATE_CODICECOMUNE/out; module load slurm; source $dir_smoketracer_frontend/etc/profile; cd $dir_smoketracer_frontend; ./smoketracer LON LAT DatE_CALMET HourS_Calmet DATe HOURS TEMPERATURE $storage/USER/DATE_CODICECOMUNE; \" " &



