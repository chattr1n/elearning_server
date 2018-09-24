from flask import Flask, render_template, redirect, send_from_directory, session, request
from functools import wraps
from datetime import datetime, timedelta
import os
import hashlib
import logging
import base64
from pymongo import MongoClient
import ssl
from bson.objectid import ObjectId
from gevent.pywsgi import WSGIServer

app = Flask(__name__, instance_path = os.getcwd())

# app.secret_key = 'ROODEEISTHEBEST'
app.secret_key = '4b93b608174e49f7'
app.config['SESSION_TYPE'] = 'filesystem'    

timeout_in_minute = 10

client = MongoClient('mongodb://devuser:%7ETesting0001@aws-ap-southeast-1-portal.0.dblayer.com:15718,aws-ap-southeast-1-portal.2.dblayer.com:15718/gcp01?readPreference=primary&ssl=true', ssl_cert_reqs=ssl.CERT_NONE)
db = client['gcp01']    
    
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

################################################################################
# debugging
################################################################################

this_port = 8084 # prod = 8084
this_is_debugging = False

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
    [courseid, userid, enc] = ID.split('|')
    clear = courseid + '|' +  userid    
    
    if not md5_checker(clear, enc):        
        return [None, None, None, None, None]
        
    coursecode = ''
    for result in db['elearning'].find({'_id': courseid}):
        coursecode = result['code']        
        if coursecode != '':
            break
        
    if coursecode == '':
        return [None, None, None, None, None]

    # print([courseid, userid, clear, enc, coursecode])        
    return  [courseid, userid, clear, enc, coursecode]
        
def get_dt_in_str(addtime):
    dt = datetime.now() + timedelta(minutes=addtime)
    return encrypt(dt.strftime('%Y%m%d%H%M%S'))
    
def time_has_passed(str):    
    dt1 = datetime.strptime(decrypt(str), '%Y%m%d%H%M%S')
    dt2 = datetime.now()    
    return dt1 < dt2 # true if time has passed
    
def save_score(userid, courseid, score):
    if db["users"].find({"_id": userid, "elearning.courseid": courseid}).count() > 0:
    	
        db["users"].update( 
        	{  
        		"_id": userid, 
        		"elearning.courseid": courseid
        	},
        	{ "$set": { "elearning.$.status": str(score), "elearning.$.completed_date": datetime.now()} }
        )
        
    else:
        db["users"].update( 
        	{  
        		"_id": userid
        	},
        	{ "$push": { "elearning" : {"courseid": courseid,"status": str(score), "completed_date": datetime.now()}} }
        )

def get_user_name(userid):
    name = ''
    for result in db['users'].find({'_id': userid}, {'userProfile':1}):
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
def protected(expired, filename):    
    
    if filename.split('/')[1] in ('story.html', 'story_flash.html', 'story_html5.html'):        
        ID = request.args.get('ID')
        [courseid, userid, clear, enc, coursecode] = getinfo(ID)        
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
    [courseid, userid, clear, enc, coursecode] = getinfo(ID)
    
    if userid is None:
        return 'Error. code=006. Unathorized access.'
        
    session['userid'] = userid
    return redirect('/course/' + get_dt_in_str(30) + '/' + coursecode + '/story.html?ID=' + ID)
                
@app.route('/score/<ID>', methods=['GET', 'POST'])                 
def score(ID):    
        
    if request.method == "GET":
        return 'Error. code=005. Unathorized access.'
            
    score = request.form['score']        
    [courseid, userid, clear, enc, coursecode] = getinfo(ID)
    save_score(userid, courseid, score)
    
    return render_template('score.html', user=get_user_name(userid), coursecode=coursecode, score=score)    
                 
if __name__ == '__main__':      
    
    if this_is_debugging == True:
        app.run(host="0.0.0.0", port=this_port, debug=this_is_debugging)
    else:    
        http_server = WSGIServer(('', this_port), application=app, log=None)
        http_server.serve_forever()            
        
