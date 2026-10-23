# coding: utf-8
#import pdb
#pdb.pm()
import requests
from datetime import datetime
from datetime import timezone
from datetime import timedelta
import smtplib
from os.path import basename
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate
import os.path
import pickle
import platform
import sys
import json
# import string

def PickleDump(ip,cookies,username,password):
    with open(".hubitat-env","wb") as outfile:
        pickle.dump(ip,outfile)
        pickle.dump(cookies,outfile)
        pickle.dump(username,outfile)
        pickle.dump(password,outfile)

def PickleLoad():
    if os.path.isfile(".hubitat-env"):
        with open(".hubitat-env","rb") as infile:
            ip = pickle.load(infile)
            cookies = pickle.load(infile)
            username = pickle.load(infile)
            password = pickle.load(infile)
    else:
        ip = input("Hubitat IP address:")
        hkey = input("Hubitat Key Name:")
        hvalue = input("Hubitat Key Value:")
        cookies = {hkey:hvalue}
        username = input("Gmail userame:")
        password = input("Gmail password:")
    return (ip,cookies,username,password)

def PickleLoadNewPassword():
    if os.path.isfile(".hubitat-env"):
        with open(".hubitat-env","rb") as infile:
            ip = pickle.load(infile)
            cookies = pickle.load(infile)
            username = pickle.load(infile)
            password = pickle.load(infile)
            hkey = list(cookies)[0]
            password = input("new GMail password:")
            PickleDump(ip,cookies,username,password)
    else:
        ip = input("Hubitat IP address:")
        hkey = input("Hubitat Key Name:")
        hvalue = input("Hubitat Key Value:")
        cookies = {hkey:hvalue}
        username = input("Gmail userame:")
        password = input("Gmail password:")
    return (ip,cookies,username,password)

def PickleLoadNewKey():
    if os.path.isfile(".hubitat-env"):
        with open(".hubitat-env","rb") as infile:
            ip = pickle.load(infile)
            cookies = pickle.load(infile)
            username = pickle.load(infile)
            password = pickle.load(infile)
            hkey = list(cookies)[0]
            cookies[hkey] = input("new Hubitat Key Value:")
            PickleDump(ip,cookies,username,password)
    else:
        ip = input("Hubitat IP address:")
        hkey = input("Hubitat Key Name:")
        hvalue = input("Hubitat Key Value:")
        cookies = {hkey:hvalue}
        username = input("Gmail userame:")
        password = input("Gmail password:")
    return (ip,cookies,username,password)

#version 3 works!
def send_mail(send_from, send_to, subject, text, files=None, send_cc=None, send_bcc=None, user=None, passwd=None):
    msg = MIMEMultipart()
    msg['From'] = send_from
    msg['To'] = COMMASPACE.join(send_to)
    if send_cc != None:
        msg['CC'] = COMMASPACE.join(send_cc)
    if send_bcc != None:
        msg['BCC'] = COMMASPACE.join(send_bcc)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject

    msg.attach(MIMEText(text))

    for f in files or []:
        with open(f, "rb") as fil:
            part = MIMEApplication(
                fil.read(),
                Name=basename(f)
            )
        # After the file is closed
        part['Content-Disposition'] = 'attachment; filename="%s"' % basename(f)
        msg.attach(part)

    server = smtplib.SMTP('smtp.gmail.com:587')
    server.starttls()
    server.login(user,passwd)
    server.sendmail(send_from, send_to, msg.as_string())
    server.quit()
    
alut = {}    
def chklutime(name,time,mindiff): 
    if name not in alut:
        alut[name] = time
        return True
    ludiff = time-alut[name]
    if ludiff.total_seconds() > mindiff:
        alut[name] = time
        return True
    return False

def mapDevice2RoomName(id):
    devmap = None
    
    if devmap is None:
        try:
            with open(".hubitat-devmap") as f:
                devmap = json.load(f)
        except Exception:
            devmap = {}

    device = devmap.get(id)
    if device:
        if device['room'] is None:
            return("House - "+device['name'])
        else:
            return(device['room']+' - '+device['name'])
    else:
        return('House - Unknown')


def main():
    print("Hubitat Log Emailer")

    (ip,cookies,username,password) = PickleLoad()
    print(ip,cookies,username,password)
    url = "http://"+ip+"/logs/past/json"
    print(url)

    r = requests.get(url, cookies=cookies)

    print(r.status_code)
    print(r.headers)

    t = datetime.now().astimezone()

    if os.path.isfile(".hubitat-logtime"):
        with open(".hubitat-logtime","r") as infile:
            timestamp = infile.read()
            pt = datetime.fromtimestamp(float(timestamp)).astimezone()
    else:
        pt = t - timedelta(hours=12)

    print(pt,t)

    elist = []
    enote = []
    eintrusion = None
    lt = ct = datetime.now().astimezone()
    for e in r.content[2:-2].decode("utf-8").split('","'):
        edt,level,content = e.split('\\t')
        edate, etime = edt.split()
        ehour,emin,esec = etime.split(":")
        etype,eid,ename,etext = content.split('|')
        edt = edt.lstrip("\\u0000")
        lt = datetime.strptime(edt+"000","%Y-%m-%d %H:%M:%S.%f").astimezone()
        if lt > pt:
            date = lt.strftime("%Y-%m-%d %H:%M:%S.%f")
            etext=etext.replace("\\u00b0"," deg.")
            elist.append([date,level,etype,eid,ename,etext])
            if etype == 'app': 
                enote.append(edate+' '+etime+' (APP - '+eid+') - '+etext)
                if eid == '1' and "Intrusion" in etext:
                    eintrusion = etext
            elif etype == 'dev':
                enote.append(edate+' '+etime+' ('+mapDevice2RoomName(eid)+') - '+etext)
            else:
                enote.append(edate+' '+etime+' '+ename+' '+etext)
            
    mtext = ""
    lline = ""
    with open("hubitat.txt","w") as outfile:
        for aline in enote:
            if aline != lline:
                print(aline)
                outfile.write(aline+"\n")
                mtext += aline+"\n"
                lline = aline
        if platform.system() == "Linux":
            with open('/proc/uptime', 'r') as f:
                mtext += "uptime: "+f.readline().split()[0]+"\n"
        outfile.write("\n")
        mtext += "\n- Attached Hubitat Past Log File\n"
        for e in elist:
            date,level,etype,eid,ename,etext = e
            oline = "{0} {1} {2} {3}\t{4} -\t{5}".format(date,level,etype,eid,ename,etext)
            print(oline)
            outfile.write(oline+"\n")

    print(lt)

    with open(".hubitat-logtime","w") as outfile:
        outfile.write(str(lt.timestamp()))

    fromaddr = 'mike.lisanke@gmail.com'
    toaddr  = 'mike.lisanke+RPiTV@gmail.com'
    cc = ['mike.lisanke+rpicc1@gmail.com','mike.lisanke+rpicc2@gmail.com']
    bcc = ['mike.lisanke+rpibcc1@gmail.com']
    if eintrusion:
        subject = "Hubitat Past Logs at "+eintrusion+" from: "+platform.node()
    else:
        subject = "Hubitat Past Logs at "+lt.strftime("%c")+" from: "+platform.node()

    send_mail(fromaddr,[toaddr],subject,mtext,files=["hubitat.txt"],send_cc=cc,send_bcc=bcc,user=username,passwd=password)

if __name__=="__main__":
        if len(sys.argv) > 1:
            if "newkey" == sys.argv[1]:
                PickleLoadNewKey()
            elif "newpsw" == sys.argv[1]:
                PickleLoadNewPassword()
        main()