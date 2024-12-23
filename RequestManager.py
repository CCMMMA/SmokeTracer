### Module Import 
from flask import Flask, render_template, request, url_for, session, make_response, flash, jsonify, redirect
#from werkzeug.security import safe_join, safe_str_cmp, generate_password_hash
from werkzeug.security import safe_join, generate_password_hash
from flask_paginate import Pagination
from flask_mail import Mail, Message
from shutil import copyfile, rmtree
from dotenv import load_dotenv
from datetime import datetime
from threading import Lock
import secrets
import zipfile
import base64
import uuid
import re 
import os
import hmac
import requests
import random
import time
import json
import threading
# Custom Import
from DBManager import DBProxy, DBManager
from SbatchManager import SbatchManager
from NcDumper import NCODump
from ParserManager import Parser
from DagonOnServiceManager import DagonOnServiceManager
from HandlerSpatialQuery import HandlerSpatialQuery

##############
##  INIT   ##
#############

load_dotenv(dotenv_path='/home/fumi2/FUMI2/secrets/secrets.env')

### APP AND OBJECTS
app = Flask(__name__)
sbatchmanager = SbatchManager(os.getenv('SCRATCH_PATH'), 
                              os.getenv('STORAGE_PATH'), 
                              os.getenv('MODEL_TEMPLATE_PATH'), 
                              os.getenv('ROOT_PATH'), 
                              os.getenv('SBATCH_TEMPLATE'), 
                              os.getenv('PROJECT_NAME'))
port = os.getenv('PROJECT_PORT')

queue_lock = Lock()
parser = Parser()
ncdump = NCODump()

### Configuring SMTP data and info to send mails
app.config['MAIL_SERVER']= os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = os.getenv('MAIL_PORT')
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
#app.config.update(SESSION_COOKIE_SAMESITE="None", SESSION_COOKIE_SECURE=True) da decommentare quando si usa https 
mail = Mail(app)

##############
## HELPERS ##
#############

def redirect_to_dashboard(user):

    # Istanciate a db object to perform queries
    db = DBProxy()

    # If we're logging in, we redirect to adminpane/dashboard based on  
    # The user privilege
    if db.is_admin(user):
        # We redirect to adminpane
        return redirect(url_for('adminpane'))
    else: 
        return redirect(url_for('dashboard'))

def validate_string(string, pattern="[a-zA-Z0-9._]"):
    """
    This function takes a string and uses a regular expression pattern to validate its format.
    """
    # Define the regular expression pattern for a username
    pattern = rf"^{pattern}+$"
    
    # Use the match() method to check if the username matches the pattern
    if re.match(pattern, string) is not None:
        return True
    else:
        return False

def validate_password(string, pattern="^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$"):
    """
    This function takes a password as a string and uses a regular expression pattern to validate its format.
    """

    # Use the match() method to check if the username matches the pattern
    if re.match(pattern, string) is not None: 
        return True
    else: 
        return False

def generate_unique_link(username, route):

    # We first generate an unique link and an encoded user
    unique_id = str(uuid.uuid4().hex[:11])
    encoded_name = base64.b64encode(username.encode('utf-8')).decode('utf-8')
    split = base64.b64encode("split".encode('utf-8')).decode('utf-8')

    #TODO: fare il link dinamico con url for
    link = f"{os.getenv('PROJECT_DOMAIN')}/{route}/{encoded_name}{split}{unique_id}"

    # we return the link
    return link
   
def get_group_label(structure_label):
    if(structure_label == "Regione Campania"):
        return "regione_campania"
    elif(structure_label == "IZSM"):
        return "izsm"
    elif(structure_label == "ASL Avellino"):
        return "asl_avellino"
    elif(structure_label == "ASL Benevento"):
        return "asl_benevento"
    elif(structure_label == "ASL Caserta"):
        return "asl_caserta"
    elif(structure_label == "ASL Napoli Centro"):
        return "asl_napoli_centro"
    elif(structure_label == "ASL Napoli Nord"):
        return "asl_napoli_nord"
    elif(structure_label == "ASL Napoli Sud"):
        return "asl_napoli_sud"


#############
## WEBSITE ##
#############

'''
@app.route('/get-status-workflow/<id>', methods=['GET'])
def workflowStatus(id):
    dagonManager = DagonOnServiceManager('http://193.205.230.6:1727', ['calmet', 'calpost', 'calpufff', 'calwrff', 'ctgproc', 'dst', 'lnd2', 'makegeo', 'terrel', 'wrf2calwrf', 'www'], 11)
    workflow_status = dagonManager.getStatusByID(id)
    return workflow_status
'''
@app.route('/', methods=['POST', 'GET'])
def login():
    #if "user" in session:   
        # return redirect(url_for('dashboard'))
    #    return redirect_to_dashboard(session["user"])
 
    if request.method == "POST":

        if 'button_admin_panel' in request.form:
            return redirect(url_for('adminpane'))
        
        if 'button_user_panel' in request.form:
           return redirect(url_for('dashboard'))

        db = DBProxy()

        username = request.form.get("username")
        password = request.form.get("password")

        exists = db.user_exists(username, password)
        is_active = db.user_active(username)

        if exists:            
            if is_active:
                session["user"] = username
                session["jobinfo_queue"] = []
                session["job_sim_singola"] = False
                # tiene traccia dei dati sottomessi per la simulazione singola 
                session["info_single_job"] = []
                session["tot_jobs_queue"] = 0
                # tiene traccia dei dati sottomessi per le simulazioni nella queue
                session["info_jobs_queue"] = []
                session['path_show_kml'] = ""
                session['admin'] = False

                db.update_access(session["user"])
                session["access"] = db.get_last_access(session["user"])

                groups_user = db.get_groups_user(username)

                if 'admin' in str(groups_user):
                    session["admin"] = True
                    return redirect(url_for('login'))
                    # return redirect(url_for('redirectTo'))

                # return redirect_to_dashboard(session["user"])
                return redirect(url_for('dashboard'))

            else:
                flash("Utente non attivo. Richiederne l'attivazione!")
                session['admin'] = False
                return redirect(url_for('login'))
        else:
            flash("Username o Password non corrette.")
            session['admin'] = False
            return redirect(url_for('login'))

    # Assign the redirectionn to the template login
    return render_template('login.html')

@app.route('/redirect_to', methods=['POST', 'GET'])
def redirectTo():
    if "user" not in session:
        return redirect(url_for('login'))

    if request.method == "POST":

        if 'button_admin_panel' in request.form:
            return redirect(url_for('adminpane'))
        
        if 'button_user_panel' in request.form:
           return redirect(url_for('dashboard'))

    return render_template("redirect_to.html")
 
@app.route('/dashboard', methods=['POST', 'GET'])
def dashboard():

    if "user" not in session:
        return redirect(url_for('login'))
    
    #if db.is_admin(session["user"]):
    #    return redirect(url_for('adminpane'))

    user = session["user"]
    last_access= session["access"]
   
    return render_template("dashboard.html", user=user, last_access=last_access)

'''
@app.route('/simulazione-singola', methods=['POST', 'GET'])
def simulazione_singola():

    if "user" not in session:
        return redirect(url_for('login'))

    db = DBProxy()
    
    if db.is_admin(session["user"]):
        return redirect(url_for('adminpane'))

    user = session["user"]
    last_access= session["access"]

    hours = [f"0{i}" if i < 10 else f"{i}" for i in range(24)]

    if request.method == "POST":
        if "generate" in request.form:
            
            if session['job_sim_singola'] != False:
                flash("Un'operazione è attualmente in atto. Aspettare che finisca o sottometterne di nuove nella dashboard per le code.") 
                return redirect(url_for('interattivo'))
            else:
                session['job_sim_singola'] = True
           
            area = request.form.get("area")
            if not validate_string(area, "[a-zA-Z]"):
                flash("Area inserita non valida. Unici caratteri consentiti: Lettere [a-z e A-Z]. Riprovare!")
                return redirect(url_for('simulazione_singola'))

            data = request.form.get("data")
            ora = request.form.get("hours")
            durata = request.form.get("durata")
            comune = request.form.get("comune")
            longit = request.form.get("long")
            latit = request.form.get("lat")
            temp = request.form.get("temp")
            codice_GISA = request.form.get("codice_gisa")

            session['area'] = area
            session['data'] = data
            session['ora'] = ora
            session['durata'] = durata
            session['comune'] = comune
            session['lon'] = longit
            session['lat'] = latit
            session['temp'] = temp
            session['codice_GISA'] = codice_GISA
            session['data2'] = "".join(data.split('-'))
            session['ora_inizio'] = str(int(ora))
            
            job_info = ["./EmsSmoke.sh", area, "".join(data.split('-')), str(int(ora)), durata, comune, longit, latit, temp, codice_GISA]
            job_info.append(str(user))
            
            id_workflow = sbatchmanager.run(user, job_info)

            if id_workflow is not None:
                job_info[0] = id_workflow
                db.new_job(job_info)
                session['workflow_id'] = id_workflow
            else:
                session['workflow_id'] = ""
                flash("Non è stato possibile inserire l'operazione in coda. Riprovare!")
                return redirect(url_for('interactive'))

    
        elif "dresetmap" in request.form:
            session['user_dir_name'] = ""
            session['workflow_id'] = ""
            session['area'] = ""
            session['data'] = ""
            session['ora'] = ""
            session['durata'] = ""
            session['comune'] = ""
            session['lon'] = ""
            session['lat'] = ""
            session['temp'] = ""
            session['codice_GISA'] = ""
            session['data2'] = ""
            session['ora_inizio'] = ""
            session['job_sim_singola'] = False
    else: 
        print("no post method")

    return render_template('interactive.html',
                            user=user, 
                            last_access=last_access, 
                            # update=update, 
                            # info_str=info_str, 
                            # state=session["jobstate_interactive"],
                            # info=session["jobinfo_interactive"], 
                            hours=hours)
                            # kmlpath = session["kmlpath_dash"])
'''

@app.route('/simulazioni', methods=['POST', 'GET'])
def coda():
    
    if "user" not in session:
        return redirect(url_for('login'))

    db = DBProxy()

    user = session["user"]
    last_access = session["access"]

    '''
    1) prendere tutti i gruppi di cui fa parte l'utente 
    2) se per tutti i gruppi l'utente non ha i permessi di scrittura , non puo accedere alle simulazioni 
    3) se ha dei permessi di scrittura di qualche gruppo su true allora puo generare una simulazione.
    4) alla fine della simulazione viene salvata associando la siulazione a tutti i gruppi dove l'utente ha i permessi di scrittura.
    '''

    user_groups = db.get_groups_user(user)
    count_false = 0
    for group in user_groups:
        permissions = db.get_permission_of_group(user, group[0])
        for permission in permissions:
            if permission[1] == False:
                count_false+=1
    if count_false == len(user_groups):
        print("- simulazioni - User non ha i permessi di scrittura in nessun gruppo", flush=True)
        return redirect(url_for('dashboard'))

    # Sezione dedicata per assicurare che l'utente quando fa il logout con una simulazione ancora in corso
    # al suo prossimo login ritroverà la simulazione in corso

    query = '''SELECT JOBINFO.JOBID, NAME_SIM, \"DATE\", \"TIME\", DURATION, LONG, LAT, TEMPERATURE, CODICE_GISA, COMMON, JOBINFO.COMPLETED
                FROM JOBINFO 
                JOIN JOBS ON JOBINFO.JOBID=JOBS.JOBID 
                JOIN \"USER\" ON JOBS.USERNAME=\"USER\".USERNAME 
                JOIN SIMULATION_GROUP ON JOBINFO.JOBID = SIMULATION_GROUP.JOBID
                JOIN GROUPS ON SIMULATION_GROUP.NAME_GROUP = GROUPS.NAME_GROUP
                WHERE \"USER\".USERNAME=\'{}\' 
                '''.format(user) 

    all_jobs_user = db.get_db().execute(query)

    if session["tot_jobs_queue"] == 0: 
        for i in range(0, len(all_jobs_user), 2):
            if all_jobs_user[i][10] == 0:
                var_info = [all_jobs_user[i][0], all_jobs_user[i][1], all_jobs_user[i][2], all_jobs_user[i][3], all_jobs_user[i][4], all_jobs_user[i][5], all_jobs_user[i][6], all_jobs_user[i][7], all_jobs_user[i][8], all_jobs_user[i][9]]
                session["info_jobs_queue"].append(var_info)
                session["tot_jobs_queue"] += 1
            # print("job in progress", flush=True)
    # print(f"all_jobs_user : {all_jobs_user}", flush=True)
    # ---------------------------------------------------------    

    hours = [f"0{i}" if i < 10 else f"{i}" for i in range(24)]

    if request.method == "POST":
        
        if "generate" in request.form:
            session["tot_jobs_queue"] += 1
            area = request.form.get("area")
            #if not validate_string(area, "[a-zA-Z]"):
            #    flash("Area inserita non valida. Unici caratteri consentiti: Lettere [a-z e A-Z]. Riprovare!")
            #    return redirect(url_for('coda'))

            data = request.form.get("data")
            ora = request.form.get("hours")
            durata = request.form.get("durata")
            comune = request.form.get("comune")
            longit = request.form.get("long")
            latit = request.form.get("lat")
            temp = request.form.get("temp")
            codice_GISA = request.form.get("codice_gisa")

            job_info = ["./EmsSmoke.sh", area, "".join(data.split('-')), str(int(ora)), durata, comune, longit, latit, temp, codice_GISA]
            job_info.append(str(user))
            
            data_to_run = data.replace("-", "")

            # id_workflow, path_out_user = sbatchmanager.run(user, data_to_run, job_info)
            id_workflow = sbatchmanager.run(user, data_to_run, job_info)

            if id_workflow is not None:
                job_info[0] = id_workflow
                db.new_job(job_info, user_groups, id_workflow)
                var_info = [id_workflow, area, data, ora, durata, longit, latit, temp, codice_GISA, comune]
                session["info_jobs_queue"].append(var_info)
                # Create thread to check workflow status
                # Once the Workflow finished, the thread update db
                # t1 = threading.Thread(target=sbatchmanager.check_progress, args=(str(id_workflow), str(path_out_user)))                
                t1 = threading.Thread(target=sbatchmanager.check_progress, args=(str(id_workflow), )) 
                t1.start()

            else:
                flash("Non è stato possibile inserire l'operazione in coda. Riprovare!")
                return redirect(url_for('dashboard'))

        elif "hshowbutton" in request.form:
            id_job = request.form.get("idJOB")
            # print("- coda - show button - id_job : " + id_job, flush=True)
            session["kml_info_show"] = db.get_all_groups()
            # print("coda - show button - session['kml_info_show] : " + str(session['kml_info_show']), flush=True)
            # da finire quando ottengo gli out del workflow

        elif "hdeletebutton" in request.form:
            print("-coda - delete button", flush=True)
            id_job = request.form.get("idJOB")
            db.delete_row("JOBINFO", "JOBID", id_job)

        ''' 
        # Second case: the user want to cancel the job
        elif "qcancel" in request.form:
            
            # We lock the thread for the entire request to avoid multiple elimination request
            # at once, we may lost something
            queue_lock.acquire()
            if not session["queue_ops_in_act"]:
                
                # Operation in act 
                session["queue_ops_in_act"] = True

                # Unlock 
                queue_lock.release()

                # We get the index of the array in which the button has been pressed 
                index = int(request.form['qcancel'])
                print(index)
                
                # We fetch the jobid from the jobinfo array 
                jobid = session["jobinfo_queue"][index][7]

                # Before trying to eliminate the job, we check if the sbatch manager has finalized
                # the routine for the starting of a new job: to do so, we just query the database 
                # given the jobid of the selected job in the selected table row, and we got the 
                # PATH: basically if none, the job hasn't finalized yet 
                path = None
                try:

                    # We try to fetch the path from the given jobid
                    path = db.specific_select("JOBIDENTIFIER", "PATH", "JOBID", jobid)

                except: 
                    
                    # Flash an error and render again
                    flash("Non è stato possibile trovare l'operazione in coda. Riprovare!")
                    return redirect(url_for('coda'))

                # If we returned something
                if path is not None:

                    # We try to submit the scancel [jobid] command
                    try: 
                        sbatchmanager.cancel_job(jobid)
                    except:
                        flash("Errore nella cancellazione dell'operazione. Riprovare!")

                    # We update the session deleting the element
                    del session["jobinfo_queue"][index]
                    session.modified = True
                
                else:

                    # We flash a message 
                    flash("Operazione in finalizzazione. Riprovare tra qualche secondo.")

                # No ops in act 
                queue_lock.acquire()
                session["queue_ops_in_act"] = False
                queue_lock.release()
            
            else: 

                # Unlock 
                queue_lock.release()

                # We flash a message 
                flash("Operazione di eliminazione in finalizzazione. Riprovare tra qualche secondo.")
        '''

        # elif "qresetjob" in request.form:
        #    pass

            # If we reload the job, we do an integrity check to understand if 
            # some job has been lost. We get the queue state by the parser
            # We retry the dictionarized squeue job list 
            # jobs = get_slurm_queue("g.hauber")
            
            # Fetch a local structure of jobinfo queue
            # queue_lock.acquire()
            # jobinfo_queue = session["jobinfo_queue"]
            # queue_lock.release()

            # Now we iterate the jobinfo queue
            # print("RESET JOB")
    
    page = int(request.args.get('page', 1))
    per_page = 10
    offset = (page - 1) * per_page
    pagination_data = session["jobinfo_queue"][offset: offset + per_page]
    
    if len(pagination_data) == 0 and len(session["jobinfo_queue"]) != 0: 
        # We subtract a page then doing the offset calculation again
        page -= 1
        offset = (page - 1) * per_page
        # We do assign the new pagination data belonging to the previous page, only if 
        # the lenght of the jobinfo queue is diff than 0 (still job in queue)
        pagination_data = session["jobinfo_queue"][offset: offset + per_page]
   
    pagination = Pagination(page=page, per_page=per_page, total=len(session["jobinfo_queue"]), css_framework='bootstrap5')
    datainfo = [offset, offset + per_page, len(session["jobinfo_queue"])]

    return render_template('queue.html', 
                           user=user, 
                           last_access=last_access, 
                           # update=update, 
                           queue=pagination_data,
                           pagination=pagination, 
                           datainfo=datainfo,
                           hours=hours,
                           info_jobs = session["info_jobs_queue"]
                        )

@app.route('/profilo', methods=['POST', 'GET'])
def profilo(alert_category=""):

    if "user" not in session:
        return redirect(url_for('login'))

    db = DBProxy()

    user = session["user"]
    # session["searchval"] = ""
    
    last_access=db.get_last_access(user)
    profile=db.get_profile(user)

    # We init the alert category to the input 
    category = alert_category

  
    if request.method == "POST":

        firstname = request.form.get("firstname")
        lastname = request.form.get("lastname")
        password = request.form.get("password")
        telephone = request.form.get("telephone")

        hashed_password = generate_password_hash(password)

        try:
            db.update_profile(user, firstname, lastname, hashed_password, telephone)
        except Exception as E:
            category = "alert-danger"
            flash("Impostazioni salvate correttamente!")
            return redirect(url_for('profilo', alert_category=category))


        category = "alert-success"
        flash("Impostazioni salvate correttamente!")

        profile=[firstname if firstname!="" else profile[0], 
                lastname if lastname!="" else profile[1], 
                telephone if telephone!="" else profile[2]]

    return render_template('profilo.html', user=user, last_access=last_access, profile=profile, category=category)

@app.route('/storico', methods=['POST', 'GET'])
def storico():

    if "user" not in session:
        return redirect(url_for('login'))

    db = DBProxy()

    user = session["user"]
    last_access=db.get_last_access(user)

    user_groups = db.get_groups_user(user)
    count_false = 0
    for group in user_groups:
        permissions = db.get_permission_of_group(user, group[0])
        for permission in permissions:
            if permission[0] == False:
                count_false+=1
    if count_false == len(user_groups):
        # print("- simulazioni - User non ha i permessi di scrittura in nessun gruppo", flush=True)
        flash("L'utente non ha i permessi di scrittura in nessun gruppo")
        return redirect(url_for('dashboard'))

    jobs = []
    string_search = ""
    
    for group in user_groups:
        # print("- requestmanager - group : " + str(group), flush=True)
        if str(group[0]) != str(user):
            # print("- requestmanager - group : " + str(group[0]) + " - user : " + str(user), flush=True)
            permissions = db.get_permission_of_group(user, group[0])
            if permission[0] == True:
                jobs_of_user_group = db.fetch_user_group(user, group[0])
                # print("- storico - jobs return to db query : " + str(jobs_of_user_group),  flush=True)
                for jobs_var in jobs_of_user_group:
                    jobs.append(jobs_var)
        '''
        for permission in permissions:
            if permission[0] == True:
                jobs_of_user_group = db.fetch_user_group(user, group[0])
                for jobs_var in jobs_of_user_group:
                    jobs.append(jobs_var)
        '''
    


    if request.method=="POST":  
        if "hsearchbutton" in request.form:
            print("[*] Search Button - coda", flush=True)
 
        elif "hshowbutton" in request.form:
            print("[*] Show Button - coda", flush=True)
       
        elif "hdeletebutton" in request.form:
            job_to_remove=request.form.get("idJOB")
            db.delete_row('JOBINFO', 'JOBID', job_to_remove)
            # print("[*] Delete Button - coda", flush=True)
            return redirect(url_for('storico'))
          
        elif "hresetmap" in request.form:
            print("[*] Reset Button - coda", flush=True)
            
        elif "hresetjob" in request.form:
            print("[*]  Button - coda", flush=True)

        elif "hdownloadbutton" in request.form:
            return redirect(url_for('download'))

    page = int(request.args.get('page', 1))
    per_page = 5
    offset = (page - 1) * per_page
    pagination_data = jobs[offset: offset + per_page]
    pagination = Pagination(page=page, per_page=per_page, total=len(jobs), css_framework='bootstrap5')
    datainfo = [offset, offset + per_page, len(jobs)]

    return render_template('storico.html', 
                           user=user, 
                           last_access=last_access, 
                           jobs=pagination_data, 
                           pagination=pagination,
                           datainfo=datainfo)

@app.route('/getPermissionsUser', methods=['POST'])
def getPermissionsUser():
    data = request.get_json()
    user = data.get('user')
    group = data.get('group')
    db = DBProxy()
    # print("- getPermissionsUser - user : " + str(user), flush=True)
    # print("- getPermissionsUser - group : " + str(group), flush=True)
    return jsonify(db.get_permission_of_group(user, group))

@app.route('/interfaceUserGroup', methods=['POST', 'GET'])
def interfaceUserGroup():
    db = DBProxy()
    all_names_groups = db.get_all_groups()
    username = session['user_to_interface']

    # username = request.form.get('username_hidden')
    # print("-interfaceUserGroup - username : " + str(username), flush=True)
    last_access=db.get_last_access(username)
    user_groups = db.get_groups_user(username)
    all_names_group_whitout_user_group = all_names_groups

    for group in all_names_groups:
        for user_group in user_groups:
            if group == user_group:
                all_names_group_whitout_user_group.remove(group)

    x = []
    for i in range(len(all_names_group_whitout_user_group)):
        # ex [ 0, 'asl_napoli_nord ] , [1, 'asl_napolis_sud'], ... 
        x.append([str(i), all_names_group_whitout_user_group[i][0]])

    # TODO : controllare se l'user fa parte del gruppo admin , se non fa parte ritorna al login
    if request.method == "POST":
        if "add_group_action" in request.form:
            button_value = request.form.get('add_group_action')
            if button_value is not None:
                #index = int(button_value)
                index = str(button_value)
                # print("- interfaceUserGroup - add group button", flush=True)
                # print("- interfaceUserGroup - index : " + index, flush=True)
                # username = request.form.get(f'hidden_username_{index}')
                add_group_name = request.form.get(f'add_name_group_{index}')
                # print("- interfaceUserGroup - username : " + str(username), flush=True)
                # print("- interfaceUserGroup - add_group_name : " + str(add_group_name), flush=True)
                db.add_user_to_group(username, add_group_name, True, False)
            return redirect(url_for('interfaceUserGroup'))
        
        elif "button_remove_to_group" in request.form:
            button_value = request.form.get('button_remove_to_group')
            if button_value is not None:
                # print("- interfaceUserGroup - remove group button", flush=True)
                db.remove_user_to_group(username, button_value)
            return redirect(url_for('interfaceUserGroup'))
        
        elif "button_change_permissions" in request.form:
            write_permission = request.form.get('writePermission')
            read_permission = request.form.get('readPermission')
            user = request.form.get('name_user')
            group = request.form.get('group_selected')

            if write_permission == 'on':
                db.change_user_permissions(user, group, False, True)
            elif write_permission == None:
                db.change_user_permissions(user, group, False, False)
                
            if read_permission == 'on':
                db.change_user_permissions(user, group, True, True)
            elif read_permission == None:
                db.change_user_permissions(user, group, True, False)
               
            # print("- interfaceUsersGroup - writePermission : " + str(write_permission), flush=True)
            # print("- interfaceUsersGroup - readPermission : " + str(read_permission), flush=True)
            # print("- interfaceUsersGroup - group : " + str(group), flush=True)
            # print("- interfaceUsersGroup - user : " + str(user), flush=True)
            return redirect(url_for('interfaceUserGroup'))

    return render_template('interfaceUsersGroups.html', last_access=last_access, user=username, user_groups=user_groups, all_names_groups=x)
    
@app.route('/adminpane', methods=['POST', 'GET'])
def adminpane():

    if "user" not in session:
        return redirect(url_for('login'))

    db = DBProxy()

    # if not db.is_admin(session["user"]):
    #   return render_template('blank.html')

    user = session["user"] 
    last_access=db.get_last_access(user)

    users = db.fetch_users()
    # print("-coda - users : " + str(users), flush=True)

    #for user in users:
    #    print(str(user), flush=True)

    all_jobs = db.return_all_jobs()

    #for elem in all_jobs:
    #    print(str(elem), flush=True)
    
    # print("- adminpane - all_jobs : " + str(all_jobs), flush=True)

    # print("-coda - all-jobs : " + str(all_jobs), flush=True)

    all_group_with_user = db.get_all_groups_with_user()
    # print("- coda - all group of user : " + str(all_group_with_user), flush=True)

    all_names_groups = db.get_all_groups()
    # print("-code - all names group : " + str(all_names_groups), flush=True)


    if request.method=="POST":  

        if "savebutton" in request.form: 
            username = request.form.get("username")
            firstname = request.form.get("firstname")
            lastname = request.form.get("lastname")
            email = request.form.get("email")
            struttura = request.form.get("struttura")
            ruolo = request.form.get("ruolo")
            cellulare = request.form.get("cellulare")

            # print("- adminpane - username : " + str(username), flush=True)

            user_ok = validate_string(username)
            if user_ok==False: 
                flash("Errore: caratteri non consentiti nell'username! (ammissibili: a-z A-z 0-9 . e _)")
                return redirect(url_for('adminpane'))

            try:
                # crea utente
                db.add_user(username.lower(), firstname, lastname, email, cellulare, struttura, ruolo)
                # crea gruppo personale utente
                db.add_group(username.lower())
                # aggiungi l'utente al gruppo della struttura senza permessi di scrittura  
                db.add_user_to_group(username.lower(), get_group_label(struttura), False, False)
                # aggiungi l'utente al suo gruppo personale con i permessi di scrittura 
                db.add_user_to_group(username.lower(), username.lower(), True, True)
            except Exception as e:
                flash("Errore nell'inserimento dell'utente e del gruppo. Riprovare!")
                print("Error insert : {}".format(str(e)), flush=True)       
                return redirect(url_for('adminpane'))

            link = generate_unique_link(username, "registrazione")
            msg = Message('Registrazione al sistema FUMI2', sender = 'regionefumi2@gmail.com', recipients = [email])
            msg.body = f"Benvenuto al sistema FUMI2, {username}!. Visitare il link per completare la registrazione: {link}"

            try:
                mail.send(msg)
            except:
                flash("Errore nell'invio della mail. Rimandarla con l'apposito pulsante per generazione password!")
                return redirect(url_for('adminpane'))
                
            flash("Utente {} registrato con successo! Link di registrazione generato.".format(username))
            return redirect(url_for('adminpane'))

        elif "button_change_group" in request.form:
            # db = DBProxy()

            user = request.form['modify-user-group']
            action = request.form['action-modify-group']
            group = request.form['modify-group-group']

            #print("[*] modify user permission : " + str(user), flush=True)
            #print("[*] modify action permission : " + str(action), flush=True)
            #print("[*] modify group permission : " + str(group), flush=True)

            if action == 'Rimuovi':
                db.remove_user_to_group(user, group)
            elif action == 'Aggiungi':
                db.add_user_to_group(user, group, False, False)
            
            return redirect(url_for('adminpane'))

        elif "button_change_permissions" in request.form:

            user = request.form['modify-permission-user']
            action = request.form['modify-permission-action']
            type_permission = request.form['modify-permission-type']
            group = request.form['modify-permission-group']
            
            # print("-coda user : " + user, flush=True)
            # print("-coda action : " + action, flush=True)
            # print("-coda type : " + type_permission, flush=True)
            # print("-coda group : " + group, flush=True)

            if action == 'Rimuovi':
                action = False
            elif action == 'Aggiungi':
                action = True
            
            if type_permission == 'Lettura':
                type_permission = True
            elif type_permission == 'Scrittura':
                type_permission = False

            # db = DBProxy()
            db.change_user_permissions(user, group, type_permission, action)

            return redirect(url_for('adminpane'))

        elif "button_create_group" in request.form:
            new_group_name = request.form['name_new_group']
            db.create_group(new_group_name)
            return redirect(url_for('adminpane'))

        elif "deletebutton" in request.form:
            username = request.form['username_hidden']
            # print("--adminpane -- username : " + str(username), flush=True)
            db.delete_user(username)
            flash("Utente cancellato correttamente")
            return redirect(url_for('adminpane')) 

        elif "passwordbuttclon" in request.form:
            
            username = request.form.get("username_hidden").lower()
            is_active = db.user_active(username)

            link = ""
            title = ""
            body = ""

            if is_active:
                link = generate_unique_link(username, "ripristino")
                title = "Ripristino Password FUMI2"
                body = "Ciao {}! Hai richiesto un ripristino della password. Visitare il link per completare la procedura".format(username)
            
            else:
                link = generate_unique_link(username, "registrazione")
                title = "Registrazione al sistema FUMI2"
                body = "Benvenuto al sistema FUMI2, {}!. Visitare il link per completare la registrazione".format(username)

            email = db.specific_select("\"USER\"", "EMAIL", "USERNAME", username)
            msg = Message(title, sender = 'regionefumi2@gmail.com', recipients = [email])
            msg.body = f"{body}: {link}"

            try:
                mail.send(msg)
            except:
                flash("Errore nell'invio della mail. Rimandarla con l'apposito pulsante per generazione password!")
                
            flash("Ripristino password effettuato per {}".format(username))
            return redirect(url_for('adminpane'))
       
        elif "deactivatebutton" in request.form:
            username = request.form.get("deactivatebutton").lower()
 
            try:
                db.update_column("\"USER\"", "ACTIVE", "USERNAME", [0, username])

            except Exception as e:
                flash("Errore nella disattivazione dell'utente {}. Riprovare!".format(username))       
                return redirect(url_for('adminpane'))

            flash("Utente {} disattivato con successo.".format(username))
            return redirect(url_for('adminpane'))

        elif "activatebutton" in request.form: 
            username = request.form.get("activatebutton").lower()

            # Since an user can be inactive because he just got registered, we need to check
            # a simple thing: does he got a password yet? If so, that means the user is already registered
            # and he got disactivated due to some circumstance. If he doesn't have a password, that means 
            # he need to complete his registation yet; in that case we can't activate him and a new
            # registration form must be sent again.
            has_pass = db.specific_select("\"USER\"", "PASSWORD", "USERNAME", username)

            # If he has a pass
            if has_pass is not None:

                # We proceed to activate the user 
                # We try to submit a deactivation query 
                try:
                    db.update_column("\"USER\"", "ACTIVE", "USERNAME", [1, username])

                except Exception as e:

                    # We put the category of the error inside the variable
                    # session["category"] = "alert-danger"

                    # We flash the message
                    flash("Errore nella disattivazione dell'utente {}. Riprovare!".format(username))       

                    # Redirect to adminpane
                    return redirect(url_for('adminpane'))
            else:
                
                # Else, the user has not been registered yet. We need to inform the admin
                # Setting category     
                # session["category"] = "alert-danger"

                # We flash the message
                flash("Errore: L'utente {} deve ancora completare la registrazione. Prova a generare un'altra registrazione con il pulsante [Password!]".format(username))       

                # Redirect to adminpane
                return redirect(url_for('adminpane'))

            # Flash success if no error given
            # session["category"] = "alert-success"
            flash("Utente {} attivato con successo.".format(username))

            # Redirect to adminpane to load users again
            # return redirect('adminpane.html')
            return render_template('adminpane.html')

        elif "show_interface_usergroup" in request.form:
            session['user_to_interface'] = request.form.get('username_hidden')
            return redirect(url_for('interfaceUserGroup'))

        elif "aresetusers" in request.form:
            pass

    
        

    else: 
        pass
        
        # If here, that means the user submitted a search and now is searching for the 
        # next/prev pages in his search. Use the search val stored in session to resume his 
        # search 
        #if "searchval" in session:
        #    users = filters(session["searchval"], users)
        #    print(users)
   
    page = int(request.args.get('page', 1))
    per_page = 5
    offset = (page - 1) * per_page

    pagination_data = users[offset: offset + per_page]
    pagination = Pagination(page=page, per_page=per_page, total=len(users), css_framework='bootstrap5')
    datainfo = [offset, offset + per_page, len(users)]
  
    pagination_data2 = all_group_with_user[offset: offset + per_page]
    pagination2 = Pagination(page=page, per_page=per_page, total=len(all_group_with_user), css_framework='bootstrap5')
    datainfo2 = [offset, offset+per_page, len(all_group_with_user)]

    pagination_data3 = all_jobs[offset: offset + per_page]
    pagination3 = Pagination(page=page, per_page=per_page, total=len(all_jobs), css_framework='bootstrap5')
    datainfo3 = [offset, offset+per_page, len(all_jobs)]

    return render_template('adminpane.html',
                           last_access=last_access,
                           users=pagination_data,
                           pagination=pagination,
                           datainfo=datainfo,
                           all_group_with_user=pagination_data2,
                           pagination2=pagination2,
                           datainfo2=datainfo2,
                           all_jobs=pagination_data3,
                           pagination3=pagination3,
                           datainfo3=datainfo3,
                           all_names_groups=all_names_groups
                           )
                    
@app.route('/registrazione/<unique_id>', methods=['GET', 'POST'])
def registration(unique_id):

    if request.method == "POST":    
        
        db = DBProxy()

        split = base64.b64encode("split".encode('utf-8')).decode('utf-8')
        user = unique_id.split(split)[0]
        decoded_name = base64.b64decode(user.encode('utf-8')).decode('utf-8')

        password = request.form.get("password")
        password_again = request.form.get("password-again")
        birthdate = request.form.get("date")
        
        # We compare the password: if they're not equal, we flash a message
        # and basically reload the page again
        if not hmac.compare_digest(password, password_again):
            flash("Le password non corrispondono.")
        else:
            if not validate_password(password):
                flash("La password deve contenere 8 caratteri ed almeno una lettera, un carattere speciale ed un numero.")
            else:
                db.update_column("\"USER\"", "\"PASSWORD\"", "USERNAME", [generate_password_hash(password), decoded_name])
                db.update_column("\"USER\"", "BIRTHDATE", "USERNAME", [birthdate, decoded_name])
                db.update_column("\"USER\"", "ACTIVE", "USERNAME", [1, decoded_name])
                
                session['admin'] = False
                return redirect(url_for('login'))
    return render_template('registrationform.html')

@app.route('/ripristino/<unique_id>', methods=['GET', 'POST'])
def restoration(unique_id):

    # Simple password reset mechanism. This page is uniquely visited when an admin does
    # create a new user into the system, automatically sending him a mail to complete his ripristination.
    # We got two argument there: Password and Password again.jobinfo_queue

    # We fetch the username by decoding his string: logic described in the admipane save section
    split = base64.b64encode("split".encode('utf-8')).decode('utf-8')
    user = unique_id.split(split)[0]
    decoded_name = base64.b64decode(user.encode('utf-8')).decode('utf-8')

    # If the user has pressed a button
    if request.method == "POST":

        # We fetch the pass info
        password = request.form.get("password")
        password_again = request.form.get("password-again")

        # We compare the password: if they're not equal, we flash a message
        # and basically reload the page again
        # if not safe_str_cmp(password, password_again):
        if not hmac.compare_digest(password, password_again):
            flash("Le password non corrispondono.")

        else:

            # We check if the password are at least: 8 character long and contains at least:
            # 1 character / 1 number / 1 special char
            if not validate_password(password):

                # If not we flash a message and render again 
                flash("La password deve contenere 8 caratteri ed almeno una lettera, un carattere speciale ed un numero.")
                
            else:

                # Istanciate a db object to perform queries
                db = DBProxy()
                
                # Else, we then update the table with the password
                # db.update_column("USER", "PASSWORD", "USERNAME", [generate_password_hash(password), decoded_name])
                db.update_column("\"USER\"", "\"PASSWORD\"", "USERNAME", [generate_password_hash(password), decoded_name])

                # We also check if the user isn't active, to set his active state to true 
                is_active = db.user_active(decoded_name)

                # If not we update his state
                if not is_active:
                    db.update_column("\"USER\"", "ACTIVE", "USERNAME", [1, decoded_name])

                # After the registration, we redirect for login
                return redirect(url_for('login'))

    # render the registation form
    return render_template('passwordform.html', user=decoded_name)

######################
## EXTERNAL ROUTES ##
#####################

@app.route('/logout', methods=['POST', 'GET'])
def logout():

    # Simple logout mechanism. We do pop the user from the session stack
    # and redirect to login.
    session.pop("user", None)
    session['admin'] = False
    
    return redirect(url_for('login'))

@app.route('/download', methods=['POST', 'GET'])
def download(): 

    
    # Fourth and last case of the historic, the download button. When this button is pressed,
    # We must organize an output zip file containing all the model output files for that given id.
    # NOTE that, to avoid memory consumption we'll make all the object in memory!
    if request.method == "POST":

        # Istanciate a db object to perform queries
        db = DBProxy()

        # Fetch the jobid
        jobid = int(request.form['hdownloadbutton'])

        # Get the output path based on the jobid 
        OUTPATH = db.get_output_path(jobid, "root")

        # Init an IO object to store object in memory
        fileobj = io.BytesIO()

        # Create a ZipFile Object
        with zipfile.ZipFile(fileobj, 'w') as zip_file:

            # For the element of the output folder: 
            for file in os.listdir(OUTPATH):
                
                # Safe join the file and the filepath 
                file_path = safe_join(OUTPATH, file)

                # Add multiple files to the zip
                zip_file.write(file_path, os.path.basename(file_path))

        # Seek at 0th byte
        fileobj.seek(0)

        # Make a response to send back
        response = make_response(fileobj.read())
        response.headers.set('Content-Type', 'zip')
        response.headers.set('Content-Disposition', 'attachment', filename="{}.zip".format(jobid))
        return response

#TODO: Is safe ? 
#    : Should get a password of requested user ? 
@app.route('/getInfoJobsQueue')
def getInfoJobsQueue():
    return jsonify(session['info_jobs_queue'])

#TODO: Is safe ? 
@app.route('/getStatusJobsQueue', methods=['POST', 'GET'])
def getStatusJobsQueue():
    out_states = []
    dagonManager = DagonOnServiceManager('http://193.205.230.6:1727', ['calmet', 'calpost', 'calpufff', 'calwrff', 'ctgproc', 'dst', 'lnd2', 'makegeo', 'terrel', 'wrf2calwrf', 'www'], 11)
    for job in session['info_jobs_queue']:
        response_dagon = dagonManager.getStatusByID(str(job[0]))
        out_states.append([response_dagon])
    return jsonify(out_states)

#TODO: Is safe ? 
@app.route('/adminGroupYesOrNot', methods=['POST', 'GET'])
def adminGroupTesOrNot():
    username = request.form.get("username")
    if 'admin' in db.get_groups_user(username):
        return "True"
    else:
        return "False"

#TODO: Is safe ? 
@app.route('/extractCommons', methods=['GET'])
def extractCommons():
    spatial_handler_query = HandlerSpatialQuery()
    path_kml = path_kml = request.args.get('path_kml') 
    result = spatial_handler_query.read_polygon_from_kml(path_kml)
    # chiudo il ring  ( box di coordinate ) dell'isolinea piu esterna del kml
    result[-1][-1] = result[-1][0]
    extracted_commons = spatial_handler_query.spazial_query_box(result[-1])
    return jsonify(extracted_commons)

'''
@app.route('/progress')
def progress():
    
    # Route called by the AJAX function that checks at a given interval files into a given directory  
    # To update the progress bar. To do so, the structure of progress is composed as follow: 
    # [percentage of files, path to kml file, completed state]
    # We call the get progress function to return such structure
    progress = get_progress()
    
    # After we get the progress elements, we need to check for the percentage. 
    # If we reached 100%, we need to pop the first element (and unique at each time) from 
    # the jobdash_state list, so an user can submit a new job if wanted.
    if int(round(progress[0])) == 100:

        # Reset the state array
        session["jobstate_interactive"] = []

        # Update the info state and kml file based on the state fetched
        if progress[2] == 1:

            # If state is 1, then we succeded and completed the job: we put the right info
            # into the cookie session
            session["jobinfo_interactive"][8] = "COMPLETATO"
            session["jobinfo_interactive"][9] = progress[2]
            session["kmlpath_dash"] = progress[1]
        else: 

            # else, we did not succeed. If the info state is different than 3 (canceled)
            # We update the info str, so if the user change pages will find the results
            # back on available. 
            if session["jobinfo_interactive"][9] == 3:
                session["jobinfo_interactive"][8] = "CANCELLATO"
            else:
                session["jobinfo_interactive"][8] = "ERRORE"
    
    # We return the json data
    return jsonify({"progress": progress[0], "kmlpath": progress[1], "state": progress[2]})

@app.route('/queue')
def queue():
    
    # Istanciate a db object to perform queries
    db = DBProxy()

    # This function takes care of updating the states of the job currently in queue, displaying 
    # their state (completed or error) in the apposite table. 
    # This function is called by an AJAX function following the same logic of the progress one. 
    # The difference is that we want to check at each request just the state of a given job. 
    # We init an empty dictionary to return later as a json to the function:
    data = {}

    # Init key values 
    data["qsize"] = 0
    data["states"] = []

    # We acquire session info locking
    queue_lock.acquire()
    data["tsize"] = len(session["jobinfo_queue"])
    queue_lock.release()

    # We retry the dictionarized squeue job list 
    squeue_list = parser.dictionarize("squeue")

    # We extract all the jobs corresponding to the machine user (a.riccio)
    # And their states (R, PD)
    user = "g.hauber"
    jobs = {}
    for key in squeue_list: 
        if safe_str_cmp(squeue_list[key]["USER"], user):
            jobs[key] = squeue_list[key]["ST"]
    
    # Now qsize is the len of the jobs dict
    data["qsize"] = len(jobs)

    # If there are any jobs in the queue left
    if data["qsize"] > 0:

        # We check the entire last updated session jobinfo array to update states 
        for i, job in enumerate(session["jobinfo_queue"]): 

            # Fetch the jobid
            cur_jobid = job[7]

            # We fetch the state for the current jobid
            # State initially is a value not handled in the js ajax func cases
            state = -2

            # We try to fetch state in db
            try:
                state = db.specific_select("JOBINFO", "COMPLETED", "JOBID", cur_jobid)
            except Exception:
                pass

            # Now, if the job is running we need to check his state
            if cur_jobid in jobs:

                # If is in a pending state, set to -1 (waiting for resources) else the state itself
                state = -1 if jobs[cur_jobid]=="PD" else state

            # We append the state to the state array: 
            data["states"].append(state)

            # Then we update the jobinfo info state string, switching states and assign right label
            # Also, if a job is completed/deleted or canceled, we delete it from the session
            #TODO: label not showing properly, but everything seems to work!
            if state == -1:
                session["jobinfo_queue"][i][8] = "IN ATTESA"
            elif state == 0:
                session["jobinfo_queue"][i][8] = "IN CORSO"
            elif state == 1:
                del session["jobinfo_queue"][i]
            elif state == 2:
                del session["jobinfo_queue"][i]
            elif state == 3:
                del session["jobinfo_queue"][i]

            # We set modified 
            session.modified = True
            #print(session["jobinfo_queue"])

    else: 

        # Else, queue is empty: we fetch all the states of the jobinfo array and
        # build the last state array to return and update finally all the remaining jobs
        for jobinfo in session["jobinfo_queue"]:
            data["states"].append(db.specific_select("JOBINFO", "COMPLETED", "JOBID", jobinfo[7]))

        # No jobs left: we reset the structures
        session["jobinfo_queue"] = []
        session.modified = True


    # We return the data array 
    return jsonify(data)
'''

if __name__ == "__main__":
    
    # Secret app key for session cookies (each time we restart the server, a new key is created:
    # doing so, all the cookies will be deleted and the user will need to sign in and create them again)
    app.secret_key = secrets.token_hex()

    print("PORT : " + str(port), flush=True) 
    app.run(debug=True, host='0.0.0.0', port=port)
