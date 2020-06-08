import subprocess
import time
from multiprocessing import Process
from redis import Redis
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from datetime import date

cli = Redis('localhost')
cred = credentials.Certificate("fire-sdk.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://fire-30e38.firebaseio.com/'
})

start = time.time()
cli.set('read', int(cli.get('read').decode('utf-8')) + 1)
while(True):
    if int(cli.get('confirm').decode('utf-8')) == 3:
        ref = db.reference("scan")
        ref2 = db.reference("date-time")
        ref3 = db.reference("log")
        ref4 = db.reference("confirm")
        t = ref2.get()
        print("TIME:", t)
        exe = str(cli.get('exe').decode('utf-8'))
        ref.set({"object":exe, "time":t})
        ref3.push({"object":exe, "time":t})
        ref4.set(1)
        print("fire scan")
        print(exe)
        cli.set('confirm', 0)
        end = time.time()
        print("Total", end - start)
        break