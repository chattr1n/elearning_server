from flask import Flask, render_template, redirect, send_from_directory, session, request
from functools import wraps
from datetime import datetime, timedelta
import os
import hashlib
import logging
import base64
from flask_pymongo import PyMongo
import ssl
from bson.objectid import ObjectId

from gevent import server
from gevent.server import _tcp_listener
from gevent import pywsgi
from multiprocessing import Process, current_process, cpu_count

import json

app = Flask(__name__, instance_path = os.getcwd())

# app.secret_key = 'ROODEEISTHEBEST'
app.secret_key = '4b93b608174e49f7'
app.config['SESSION_TYPE'] = 'filesystem'    

timeout_in_minute = 60

mongos = {}
connectionstrings = {}

with open('settings.json') as input:
    connectionstrings = (json.load(input))
    for key, value in connectionstrings.items():
        mongos[key] = PyMongo(app, connectionstrings[key])

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

################################################################################
# debugging
################################################################################

this_is_debugging = True

################################################################################
# encryption
################################################################################

def encrypt(clear):
    key = app.secret_key
    enc = []
    for i in range(len(clear)):
        key_c = key[i % len(key)]
        enc_c = chr((ord(clear[i]) + ord(key_c)) % 256)
        enc.append(enc_c)
    return base64.urlsafe_b64encode("".join(enc).encode()).decode()
    
def decrypt(enc):
    key = app.secret_key
    dec = []
    enc = base64.urlsafe_b64decode(enc).decode()
    for i in range(len(enc)):
        key_c = key[i % len(key)]
        dec_c = chr((256 + ord(enc[i]) - ord(key_c)) % 256)
        dec.append(dec_c)
    return "".join(dec)      
    
def md5_checker(clear, enc):   
    text = app.secret_key + clear
    if enc == hashlib.md5(text.encode('utf-8')).hexdigest():
        return True    
    return False
    
################################################################################
# helper
################################################################################    

def getinfo(ID):
    [orgkey, courseid, userid, enc] = ID.split('|')
    clear = courseid + '|' +  userid    
    
    if not md5_checker(clear, enc):        
        return [None, None, None, None, None, None]

    mongo = mongos[orgkey]

    coursecode = ''
    for result in mongo.db['elearning'].find({'_id': courseid}):
        coursecode = result['code']        
        if coursecode != '':
            break
        
    if coursecode == '':
        return [None, None, None, None, None, None]

    # print([courseid, userid, clear, enc, coursecode])        
    return  [orgkey, courseid, userid, clear, enc, coursecode]
        
def get_dt_in_str(addtime):
    dt = datetime.now() + timedelta(minutes=addtime)
    return encrypt(dt.strftime('%Y%m%d%H%M%S'))
    
def time_has_passed(str):    
    dt1 = datetime.strptime(decrypt(str), '%Y%m%d%H%M%S')
    dt2 = datetime.now()    
    return dt1 < dt2 # true if time has passed
    
def save_score(userid, courseid, score, orgkey):

    mongo = mongos[orgkey]

    if mongo.db["users"].find({"_id": userid, "elearning.courseid": courseid}).count() > 0:
    	
        mongo.db["users"].update( 
        	{  
        		"_id": userid, 
        		"elearning.courseid": courseid
        	},
        	{ "$set": { "elearning.$.status": str(score), "elearning.$.completed_date": datetime.now()} }
        )
        
    else:
        mongo.db["users"].update( 
        	{  
        		"_id": userid
        	},
        	{ "$push": { "elearning" : {"courseid": courseid,"status": str(score), "completed_date": datetime.now()}} }
        )

def get_user_name(userid, orgkey):
    mongo = mongos[orgkey]
    name = ''
    for result in mongo.db['users'].find({'_id': userid}, {'userProfile':1}):
        name = result['userProfile']['name'] + ' '  + result['userProfile']['surname']
    return name
    
################################################################################
# routing
################################################################################

@app.route('/')
def index():
    return render_template('index.html')
    
@app.before_request
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=timeout_in_minute)    

def special_requirement(f):
    @wraps(f)
    def wrap(*arg, **kwargs):
        try:            
            userid = session['userid'] if 'userid' in session else ''
            if userid is not None and userid != '':                 
                return f(*arg, **kwargs)
            else:
                return 'Error. code=001. Unathorized access.'
        except Exception as e:            
            return 'Error. code=002. Unathorized access.'  
    return wrap
        
@app.route('/course/<expired>/<path:filename>')
@special_requirement
def protected(expired, filename, orgkey):
    
    if filename.split('/')[1] in ('story.html', 'story_flash.html', 'story_html5.html'):        
        ID = request.args.get('ID')
        [orgkey, courseid, userid, clear, enc, coursecode] = getinfo(ID)
        if userid is None:
            return 'Error. code=003. Bad session.'
            
    try:        
        path = os.path.join(app.instance_path, 'protected')        
        if not time_has_passed(expired):
            return send_from_directory(path,filename)    
        else:
            return 'Error. code=004. Session Expired.'
    except Exception as e:
        return 'Error. code=005. Cannot get files.'
           
@app.route('/elearning/<ID>')
def elearning(ID):
    [orgkey, courseid, userid, clear, enc, coursecode] = getinfo(ID)
    
    if userid is None:
        return 'Error. code=006. Unathorized access.'
        
    session['userid'] = userid
    return redirect('/course/' + get_dt_in_str(30) + '/' + coursecode + '/story.html?ID=' + ID)
                
@app.route('/score/<ID>', methods=['GET', 'POST'])
def score(ID):
        
    if request.method == "GET":
        return 'Error. code=005. Unathorized access.'
            
    score = request.form['score']        
    [orgkey, courseid, userid, clear, enc, coursecode] = getinfo(ID)
    save_score(userid, courseid, score, orgkey)
    
    return render_template('score.html', user=get_user_name(userid, orgkey), coursecode=coursecode, score=score)
  
################################################################################
# serve
################################################################################          

def serve_forever(listener):
    pywsgi.WSGIServer(listener, application=app, log=None).serve_forever()
    
if __name__ == '__main__':

    if this_is_debugging == True:
        app.run(host="0.0.0.0", port=8080, debug=this_is_debugging)
    else:
        number_of_processes = 3
        listener = _tcp_listener(('', 8084))

        for i in range(number_of_processes):
            print ("starting process" + str(i))
            Process(target=serve_forever, args=(listener,)).start()
    
        serve_forever(listener)