import hashlib
from .meta import *

from flask import jsonify
from datetime import datetime
'''
Function that hashes element with salt and return the element hashed
'''

def hashItem(item):
    hashSalt = "SALT"
    newItem = "{0}${1}".format(hashSalt, item)
    hashedItem = hashlib.sha256(newItem.encode()).hexdigest()

    return hashedItem, hashSalt


def checkInput(item, email, price):
    if email == True:
        characters = ['/', '!', '"', "'", '?', '{', '}', '[', ']', ',', '=', '-', '+', '*', '&', 'OR', '#', '~', ':', ';', '£', '$', '%', '^', '>', '<']
    elif price == True:
        characters = ['/', '"', '?', '{', '}', '[', ']', '=', '+', '*', '&', 'OR', '#', '~', '£', '$', '%', '^', '>', '<']
    else:
        characters = ['/', '!', '"', "'", '?', '{', '}', '[', ']', ',', '=', '-', '_', '+', '*', '&', 'OR', '#', '~', ':', ';', '£', '$', '%', '^', '>', '<', '.', '@']
    
    message = True
    for character in characters:
        if character in item:
            message = False
            break
        else:
            continue

    return message

def getCurrent():
    if (flask.session.get("admin")):
        return str(flask.session.get("admin"))
    return str(flask.session.get("user"))

def getCurrentIp(request):
    return request.remote_addr()

def logAnalytics(ip, route):
    now = datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    f = open("C:/Users/Josh_2/Desktop/6005_CW/6005-CW-Teplate/analytics/{0}.txt".format(ip), 'a')
    f.close()
    f = open("C:/Users/Josh_2/Desktop/6005_CW/6005-CW-Teplate/analytics/{0}.txt".format(ip), 'r+')
    content = f.read()
    f.seek(0, 0)
    f.write("=========================================\n\n   Connection from: '{0}'\n   to '{1}'\n   {2}\n   method: '{3}'\n\n=========================================\n\n".format(ip, route, dt_string, flask.request.method).rstrip('\r\n') + '\n' + content)
    f.close()

def getRole(id):
    sql = "SELECT * FROM user WHERE id='{0}'".format(id)
    query = query_db(sql, one=True)
    return query['role']