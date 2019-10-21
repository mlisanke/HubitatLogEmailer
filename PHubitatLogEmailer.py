# coding: utf-8
#import pdb
#pdb.pm()
import requests
from datetime import datetime
from datetime import timedelta
import smtplib
from os.path import basename
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate
import os.path
import pickle

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

def main():
    print("Hubitat Log Emailer")

    (ip,cookies,username,password) = PickleLoad()
    print(ip,cookies,username,password)
    url = "http://"+ip+"/logs/past/json"
    print(url)

    r = requests.get(url, cookies=cookies)

    print(r.status_code)
    print(r.headers)
 #   print(r.content)

    t = datetime.now()

    if os.path.isfile(".hubitat-logtime"):
        with open(".hubitat-logtime","r") as infile:
            timestamp = infile.read()
            pt = datetime.fromtimestamp(float(timestamp))
    else:
        pt = t - timedelta(hours=12)

    print(pt,t)

    list = []
    ct = datetime.now()
    offset = datetime.fromtimestamp(ct.timestamp()) - datetime.utcfromtimestamp(ct.timestamp())
    for e in r.content[2:-2].decode("utf-8").split('","'):
        date,level,content = e.split('\\t')
        etype,eid,ename,etext = content.split('|')
        ut = datetime.strptime(date+"000","%Y-%m-%d %H:%M:%S.%f")
        lt = ut+offset
        if lt > pt:
            date = lt.strftime("%Y-%m-%d %H:%M:%S.%f")
            list.append([date,level,etype,eid,ename,etext])
#    print(list)

    with open("hubitat.txt","w") as outfile:
        for e in list:
            date,level,etype,eid,ename,etext = e
            etext=etext.replace("\\u00b0"," deg.")
            oline = "{0} {1} {2} {3}\t{4} -\t{5}".format(date,level,etype,eid,ename,etext)
            print(oline)
            outfile.write(oline+"\n")

    lt = datetime.strptime(list[-1][0],"%Y-%m-%d %H:%M:%S.%f")
    print(lt)

    with open(".hubitat-logtime","w") as outfile:
        outfile.write(str(lt.timestamp()))

    fromaddr = 'mike.lisanke@gmail.com'
    toaddr  = 'mike.lisanke+RPiTV@gmail.com'
    cc = ['mike.lisanke+rpicc1@gmail.com','mike.lisanke+rpicc2@gmail.com']
    bcc = ['mike.lisanke+rpibcc1@gmail.com']
    subject = "Hubitat Past Logs at "+lt.strftime("%c")

    send_mail(fromaddr,[toaddr],subject,"Attached Hubitat Past Log File",files=["hubitat.txt"],send_cc=cc,send_bcc=bcc,user=username,passwd=password)

if __name__=="__main__":
        main()