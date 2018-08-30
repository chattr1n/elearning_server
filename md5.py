'''
from hashlib import md5

def make_md5(s, encoding='utf-8'):
    return md5(s.encode(encoding)).hexdigest()
    
print(make_md5('ROODEEISTHEBESTNick'))
'''
import hashlib

courseid = '5b82d1f544f5b030f89a1731'
userid = 'epCFQqF2XcaPgwRi8'

clear = courseid + '|' + userid

enc = '4b93b608174e49f7' + clear

print(clear + '|' + hashlib.md5(enc.encode('utf-8')).hexdigest())


http://elearning-chattr1n.c9users.io/elearning/5b82d1f544f5b030f89a1731|epCFQqF2XcaPgwRi8|82ba666ce502b277ab0e6d4ff58e797e
        