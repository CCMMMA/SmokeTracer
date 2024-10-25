#!/bin/bash

storage="/storage/ccmmma/prometeo/data/opendap/apps/smoketracer"
dir_smoketracer_frontend="/home/ccmmma/prometeo/apps/smoketracer"
# storage="/storage/ccmmma/prometeo/data/opendap/pippo/smoketracer"
# storage="/scratch/d.caramiello/tmp"

#su fumi2 -c "ssh -o StrictHostKeyChecking=no d.caramiello@193.205.230.5 \"export PATH=$PATH:/usr/sbin; mkdir -p $storage/USER/USER-DATE-ID/out; module load slurm; source $dir_smoketracer_frontend/etc/profile; cd $dir_smoketracer_frontend; ./smoketracer LON LAT DATe HOURS TEMPERATURE $storage/USER/USER-DATE-ID; \" " &
su fumi2 -c "ssh -o StrictHostKeyChecking=no d.caramiello@193.205.230.5 \"export PATH=$PATH:/usr/sbin; mkdir -p $storage/USER/DATE_CODICECOMUNE/out; module load slurm; source $dir_smoketracer_frontend/etc/profile; cd $dir_smoketracer_frontend; ./smoketracer LON LAT DATe HOURS TEMPERATURE $storage/USER/DATE_CODICECOMUNE; \" " &

# / USER / yyyymmdd_codicecoumne_idworkflow

# command compiled to shell execute into the container 
# su fumi2 -c "ssh -o StrictHostKeyChecking=no d.caramiello@193.205.230.5 \"export PATH=$PATH:/usr/sbin; mkdir -p /storage/ccmmma/prometeo/data/opendap/apps/smoketracer/test; module load slurm; source /home/ccmmma/prometeo/apps/smoketracer/etc/profile; cd /home/ccmmma/prometeo/apps/smoketracer; ./smoketracer 14.56278309 41.0558865 20211013Z05 36 1200 /storage/ccmmma/prometeo/data/opendap/apps/smoketracer/test; \" " &

