from flask import Flask, render_template, redirect, send_from_directory, session, request
from functools import wraps
from datetime import timedelta
import os
import base64
import logging

from gevent.pywsgi import WSGIServer

app = Flask(__name__, instance_path = os.getcwd())
app.secret_key = 'ROODEEISTHEBEST'
app.config['SESSION_TYPE'] = 'filesystem'    
    
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

################################################################################
# debugging
################################################################################

this_port = 8084
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
    
################################################################################
# routing
################################################################################

@app.route('/')
def index():
    return render_template('index.html')
    
@app.before_request
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=30)    

def special_requirement(f):
    @wraps(f)
    def wrap(*arg, **kwargs):
        try:            
            userid = session['userid'] if 'userid' in session else ''
            #if decrypt(userid) is not None:                
            return f(*arg, **kwargs)
            #else:
            #    return 'Error. code=001. Unathorized access.'
        except Exception as e:            
            return 'Error. code=002. Error is ' + str(e)
            
        session['userid'] = ''         
    return wrap
        
@app.route('/course/<path:filename>')
@special_requirement
def protected(filename):    
    try:
        path = os.path.join(app.instance_path, 'protected')
        return send_from_directory(path,filename)    
    except Exception as e:
        return 'Error. code=003. Could not find your course.'   
        
@app.route('/elearning', methods=['GET', 'POST'])
def elearning():   
    
    if request.method == "GET":
        return 'Error. code=004. Unathorized access.'
        
    userid = request.form['UserId']    
    userid = encrypt(userid)    
    session['userid'] = userid
    
    courseid = request.form['CourseID']    
    ID = encrypt(courseid + '|' + userid)   
        
    return redirect('/course/' + courseid + '/story.html?ID=' + ID)
                
@app.route('/score/<ID>', methods=['GET', 'POST'])                 
def score(ID):    
    if request.method == "GET":
        return 'Error. code=005. Unathorized access.'
        
    score = request.form['score']        
    [courseid, userid] = decrypt(ID).split('|')        
    userid = decrypt(userid)        
    return render_template('score.html', userid=userid, courseid=courseid, score=score)    
                 
if __name__ == '__main__':      
    
    if this_is_debugging == True:
        app.run(host="0.0.0.0", port=this_port, debug=this_is_debugging)
    else:    
        http_server = WSGIServer(('', this_port), application=app, log=None)
        http_server.serve_forever()            
        
