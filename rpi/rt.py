import time
import os
from multiprocessing import Process
from redis import Redis
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from firebase import *
import RPi.GPIO as GPIO

cred = credentials.Certificate("fire-sdk.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://fire-30e38.firebaseio.com/'
})

ref = db.reference()
ref.update({"status/start":1})

 