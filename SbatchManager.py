import os
import time
import subprocess
import threading
import re
import geopandas as gpd

from werkzeug.security import safe_join
from shutil import copyfile, copytree, rmtree
from DBManager import DBProxy
from timeit import default_timer as timer
from datetime import date
from ParserManager import Parser, JOBINFO
from datetime import datetime
from SpatialQueryManager import SpatialQueryManager
from DagonOnServiceManager import DagonOnServiceManager



class SbatchManager():

    scratch_path = None
    storage_path = None
    model_path = None
    root_path = None
    sbatch_file = None
    job_name = None
    db = None

    def __init__(self, scratch_path, storage_path, model_path, root_path, sbatch_file, job_name):
        self.scratch_path = scratch_path
        self.storage_path = storage_path
        self.model_path = model_path
        self.root_path = root_path
        self.sbatch_file = sbatch_file
        self.job_name = job_name
    

    def run(self, user, date_str, params=None):
        
        millis = str(int(round(time.time() * 1000)))
        date = datetime.now()
        formatted_date_for_user_dir = date.strftime("%Y%m%dz%H%M%S")
        formatted_date_for_job = str(params[2]) + "Z" + str(params[3]).zfill(2) 

        # example : 
        # start sim = 15
        # hours sim = 5
        # calmet doto che inizia sempre da 00 dovrà calcolcolare una simulazione dalle 00 alle 15 e sommare la durata della simulazione 
        # quindi la formula sarà : 00 + start_sim + durata_sim 

        hour_calmet = int(params[3]) + int(params[4])
        hour_calpuff = int(params[4])
        formatted_date_calmet = str(params[2]) + "Z" + str("00")
        formatted_date_calpuff = str(params[2]) + "Z" + str(params[3].zfill(2))

        gdf = gpd.read_file('static/centroidi_comuni/centroidi_comuni.geojson')
        comune_name = params[5]
        cod_com = gdf.loc[gdf['COMUNE'] == comune_name, 'COD_COM'].values
        if cod_com.size <= 0:
            print(f"Comune {comune_name} non trovato nel file.", flush=True)

        script_path = "/home/fumi2/FUMI2"
        subprocess.run(['mkdir', '{}/tmp_script_lunch'.format(script_path)])
        subprocess.run(['cp', '{}/lunch_remote_job.sh'.format(script_path), '{}/tmp_script_lunch/lunch_remote_job_{}.sh'.format(script_path, millis)])
        self.substitute("{}/tmp_script_lunch/lunch_remote_job_{}.sh".format(script_path, millis), "USER", user)
        self.substitute("{}/tmp_script_lunch/lunch_remote_job_{}.sh".format(script_path, millis), "DATE", date_str)
        self.substitute("{}/tmp_script_lunch/lunch_remote_job_{}.sh".format(script_path, millis), "CODICECOMUNE", cod_com[0])
        # self.substitute("{}/tmp_script_lunch/lunch_remote_job_{}.sh".format(script_path, millis), "ID", millis)
        self.substitute("{}/tmp_script_lunch/lunch_remote_job_{}.sh".format(script_path, millis), "LON", params[6])
        self.substitute("{}/tmp_script_lunch/lunch_remote_job_{}.sh".format(script_path, millis), "LAT", params[7])
        self.substitute("{}/tmp_script_lunch/lunch_remote_job_{}.sh".format(script_path, millis), "TEMPERATURE", params[8].replace("°C", "").strip())

        self.substitute("{}/tmp_script_lunch/lunch_remote_job_{}.sh".format(script_path, millis), "DatE_CALMET", formatted_date_calmet)
        self.substitute("{}/tmp_script_lunch/lunch_remote_job_{}.sh".format(script_path, millis), "HourS_Calmet", str(hour_calmet))
        self.substitute("{}/tmp_script_lunch/lunch_remote_job_{}.sh".format(script_path, millis), "DATe", formatted_date_calpuff)
        self.substitute("{}/tmp_script_lunch/lunch_remote_job_{}.sh".format(script_path, millis), "HOURS", str(hour_calpuff))


        # self.substitute("{}/tmp_script_lunch/lunch_remote_job_{}.sh".format(script_path, millis), "DATe", formatted_date_for_job)
        # self.substitute("{}/tmp_script_lunch/lunch_remote_job_{}.sh".format(script_path, millis), "HOURS", params[4])
        subprocess.run(['mkdir', '{}/tmp'.format(script_path,)])
        subprocess.run(['mkdir', '{}/tmp/{}'.format(script_path, user)])

        var_millis = millis

        # time.sleep(5)
        
        with open('tmp/{}/out_from_job_{}_runcmd_{}.txt'.format(user, user, var_millis), 'w') as f:
            subprocess.Popen(
                './tmp_script_lunch/lunch_remote_job_{}.sh'.format(millis),
                stdout=f,
                stderr=f,
                start_new_session=True
            )
        # tempo necessario per accedere da remoto al frontend ( dove c'è SLURM ), lanciare la simulazione, ed aspettare la scrittura dell'id del workflow 
        # (da parte di smoketracer ) sul file per poi ritrovarcelo su Blackjeans ( nel container ( nel volume ) )
        time.sleep(9)

        try:
            with open('tmp/{}/out_from_job_{}_runcmd_{}.txt'.format(user, user, var_millis), 'r') as f:
                file_tmp = f.read()
        except Exception as e:
            print(e, flush=True)
        
        line_match = re.search(r'.*Workflow registration success id = \w+.*', file_tmp)
        if line_match:
            line = line_match.group(0)
            id_match = re.search(r'id = (\w+)', line)
            if id_match:
                id_value = id_match.group(1)
                print(f"-- id workflow lunched : {id_value}")
                subprocess.run(['rm', 'tmp/{}/out_from_job_{}_runcmd_{}.txt'.format(user, user, var_millis)])
                # path_out_user = 'static/smoketracer/' + user + '/' + date_str + '_' + cod_com[0]  
                # return id_value, path_out_user
                return id_value
        else:
            print('[*] ID non trovato nel file.', flush=True)
            return None, None
            # return None
            
    # Controlla lo stato del workflow e appena tutte le task sono completate aggiorna il la tupla di quella specifica simulazione come completata
    # def check_progress(self, id_workflow, path_out_user, user):
    def check_progress(self, id_workflow):
        print("Start thread : check_progress()", flush=True)

        # dagonManager = DagonOnServiceManager('http://193.205.230.6:1727', ['calmet', 'calpost', 'calpufff', 'calwrff', 'ctgproc', 'dst', 'lnd2', 'makegeo', 'terrel', 'wrf2calwrf', 'www'], 11)
        dagonManager = DagonOnServiceManager('http://193.205.230.7:1727', ['calmet', 'calpost', 'calpufff', 'calwrff', 'ctgproc', 'dst', 'lnd2', 'makegeo', 'terrel', 'wrf2calwrf', 'www'], 11)
        array_jobs = ['calmet', 'calpost', 'calpufff', 'calwrff', 'ctgproc', 'dst', 'lnd2', 'makegeo', 'terrel', 'wrf2calwrf', 'www']
        db = DBProxy()

        while True:
            response_dagon = dagonManager.getStatusByID(id_workflow)
            #print(f"\n\n-- SbatchManager -- response dagon : {response_dagon}\n\n")
            count_finish = 0

            for i in range(11):
                if response_dagon[array_jobs[i]] == 'FINISHED':
                    count_finish+=1
            
            if count_finish == 11:
                print("End thread : workflow finished", flush=True)
                
                # path_final = str(path_out_user) + '_' + str(id_workflow)
                # subprocess.run(['mv', path_out_user, path_final])
                # Set the workflow as completed
                db.update_column("JOBINFO", "COMPLETED", "JOBID", [1, id_workflow])
                break        
    
    def substitute(self, filepath, tmp, sub):
        with open(filepath, 'r') as file:
            data = file.read()
            data = data.replace(tmp, sub)

        with open(filepath, 'w') as file:
            file.write(data)

 