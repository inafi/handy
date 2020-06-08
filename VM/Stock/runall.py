import os
import subprocess
import time
from multiprocessing import Process
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from redis import Redis
import pexpect
import wget
import datetime
from firebase_admin import storage
import shutil
import urllib.request

cli = Redis('localhost')

cred = credentials.Certificate("fire-sdk.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://fire-30e38.firebaseio.com/'
})

def v3():
    #run on gpu 0
    child = pexpect.spawn('./darknetgch detector test cfg/coco.data cfg/yolov3.cfg yolov3.weights -i 1')

    def getoutput(num):
        if num == 1:
            child.expect('Enter Image Path:')
            child.sendline('../send.jpg')
            child.expect('Enter Image Path:')
        else:
            child.sendline('../send.jpg')
            child.expect('Enter Image Path:')
        return child.before

    init = 0
    prev = 0

    while(True):
        init = int(cli.get('read').decode('utf-8'))
        if init != prev:
            start = time.time()
            s = getoutput(init)
            cli.set('writev3', s)
            cint = int(cli.get('confirm').decode('utf-8'))
            cint += 1
            cli.set('confirm', cint)
            print('v3 time:', time.time() - start)
        prev = init

def oid():
    child = pexpect.spawn('./darknetgch detector test cfg/yolo.data cfg/oid.cfg yolov3-oid.weights -thresh 0.13 -i 1')

    def getoutput(num):
        if num == 1:
            child.expect('Enter Image Path:')
            child.sendline('../send.jpg')
            child.expect('Enter Image Path:')
        else:
            child.sendline('../send.jpg')
            child.expect('Enter Image Path:')
        return child.before

    init = 0
    prev = 0

    while(True):
        init = int(cli.get('read').decode('utf-8'))
        if init != prev:
            start = time.time()
            s = getoutput(init)
            cli.set('writeoid', s)
            cint = int(cli.get('confirm').decode('utf-8'))
            cint += 1
            cli.set('confirm', cint)
            print('oid time:', time.time() - start)
        prev = init

def v9():
    child = pexpect.spawn('./darknetgch detector test cfg/combine9k.data cfg/yolo9000.cfg yolo9000.weights -i 1')

    def getoutput(num):
        if num == 1:
            child.expect('Enter Image Path:')
            child.sendline('../send.jpg')
            child.expect('Enter Image Path:')
        else:
            child.sendline('../send.jpg')
            child.expect('Enter Image Path:')
        return child.before

    init = 0
    prev = 0

    while(True):
        init = int(cli.get('read').decode('utf-8'))
        if init != prev:
            start = time.time()
            s = getoutput(init)
            cli.set('write9000', s)
            cint = int(cli.get('confirm').decode('utf-8'))
            cint += 1
            cli.set('confirm', cint)
            print("9000:", time.time()-start)
        prev = init

def pythia():
    os.system("python runpythia.py")

def caption():
    os.system("python runcaption.py")

def exe():
    os.system("python exec.py")

def mrcnn():
    os.system("python3 runmrcnn.py")

def text():
    os.system("python exet.py")

def search():
    os.system("python exes.py")

def check():
    prev = 0
    init = 0
    while(True):
        init = int(cli.get('confirm').decode('utf-8'))
        if init == 4:
            print("exe ran")
            exe()
        prev = init

def once():
    done = 0
    cred = credentials.Certificate("fire-sdk.json")
    app2 = firebase_admin.initialize_app(cred, {'storageBucket': 'fire-30e38.appspot.com'}, name='storage2')
    while(True):
        ref = db.reference("status/mode")
        con = db.reference("status/confirm")
        start = db.reference("status/start")
        if(int(ref.get()) == 0 and int(con.get()) == 0):
            done = 0
        stat = int(ref.get())
        if(int(start.get()) > 0 and done == 0):
            try:
                os.remove("send.jpg")
            except:
                pass
            bucket = storage.bucket(app=app2)
            blob = bucket.blob("sent.jpg")
            url = blob.generate_signed_url(datetime.timedelta(seconds=300), method='GET')
            #fname = wget.download(url)
            #shutil.move("sent.jpg", "../send.jpg")
            urllib.request.urlretrieve(url, '../send.jpg')
            start = time.time()
            cli.set('read', int(cli.get('read').decode('utf-8')) + 1)
            while(True):
                if int(cli.get('confirm').decode('utf-8')) == 5:
                    ref = db.reference("scan")
                    ref2 = db.reference("date-time")
                    ref3 = db.reference("log")
                    log2ref = db.reference("log2")
                    stat = db.reference("status")
                    t = ref2.get()
                    print("TIME:", t)
                    exe = str(cli.get('exe').decode('utf-8'))
                    array = str(cli.get('array').decode('utf-8'))
                    ref.set({"object":exe, "time":t, "array":array})
                    ref3.push({"object":exe, "time":t, "array": array})
                    log2ref.push({"object":exe, "time":t, "array":array})
                    stat.update({"confirm": 1})
                    print("fire scan")
                    print(exe)
                    cli.set('confirm', 0)
                    end = time.time()
                    print("Total", end - start)
                    done = 1
                    break

def reset():
    cli.set('confirm', 0)
    cli.set('read', 0)
    cli.set('writev3', '')
    cli.set('writeoid', '')
    cli.set('write9000', '')
    cli.set('writemrcnn', '')
    cli.set('writepythia', '')
    cli.set('exe', '')
    cli.set('array', '[]')

if __name__ == '__main__':
    reset()
    p1 = Process(target=v9)
    p1.start()
    p2 = Process(target=oid)
    p2.start()
    p3 = Process(target=v3)
    p3.start()
    p4 = Process(target=mrcnn)
    p4.start()
    p5 = Process(target=text)
    p5.start()
    p6 = Process(target=search)
    p6.start()
    p7 = Process(target=once)
    p7.start()
#    p8 = Process(target=pythia)
#    p8.start()
#    p9 = Process(target=caption)
#    p9.start()
    check()
