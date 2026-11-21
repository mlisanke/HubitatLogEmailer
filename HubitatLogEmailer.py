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
import os
import platform
import sys
import json
import re

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

    with smtplib.SMTP('smtp.gmail.com:587',timeout=30) as server:
        server.starttls()
        server.login(user,passwd)
        server.sendmail(send_from, send_to, msg.as_string())
        server.quit()
    
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

def mapApp2Name(id):
    appmap = None

    if appmap is None:
        appmap = {}
        try:
            with open(".hubitat-appmap", 'r') as f:
                for line in f:
                    aid, aname = line.rstrip("\n").split(",") 
                    appmap[aid] = {"id": aid, "name": aname }
        except Exception:
            return "Unknown App"

    app = appmap.get(id)
    if app is None:
        return "Unknown App"

    return app["name"]

def main():
    print("Hubitat Log Emailer")

    session = os.getenv("HUBITAT_SESSION_COOKIE")
    ip = os.getenv("HUBITAT_IP")
    cookies=({"HUBSESSION":session})
    username = os.getenv("MAILADDR")
    password = os.getenv("MAILPSW")
    fromaddr = os.getenv("MAILFA")
    toaddr = os.getenv("MAILTA")
    
    print(ip,cookies,username,password,fromaddr,toaddr)

    url = "http://"+ip+"/logs/past/json"
    print(url)

    try:       
        r = requests.get(url, cookies=cookies, timeout=(30,300))
        r.raise_for_status()

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
            etype,eid,ename,etext = content.split('|')
            edt = edt.lstrip("\\u0000")
            lt = datetime.strptime(edt+"000","%Y-%m-%d %H:%M:%S.%f").astimezone()
            if lt > pt:
                etext=etext.replace("\\u00b0"," deg.")
                elist.append([edt,level,etype,eid,ename,etext])
                if etype == 'app': 
                    source = ' App:'+eid.zfill(3)+' '+mapApp2Name(eid)+' ----- '
                    enote.append(edt+source+etext)
                    if eid == '1' and "Intrusion" in etext:
                        eintrusion = etext
                elif etype == 'dev':
                    source = ' Dev:'+eid.zfill(3)+' '+mapDevice2RoomName(eid)+' ----- '
                    enote.append(edt+source+etext)
                else:
                    enote.append(edt+' '+ename+' ----- '+etext)
        print(lt)

        with open(".hubitat-logtime","w") as outfile:
            outfile.write(str(lt.timestamp()))
            
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
                oline = "{0} {1} {2} {3} {4} - {5}".format(date,level,etype,eid,ename,etext)
                print(oline)
                outfile.write(oline+"\n")

        if eintrusion:
            subject = "Hubitat Past Logs at "+eintrusion+" from: "+platform.node()
        else:
            subject = "Hubitat Past Logs at "+lt.strftime("%c")+" from: "+platform.node()

        send_mail(fromaddr,[toaddr],subject,mtext,files=["hubitat.txt"],user=username,passwd=password)

    except Exception as err:
        print(f"[{datetime.now().astimezone()}] Error in Hubitat logger: {err}")
        sys.exit(1)

if __name__=="__main__":
        main()