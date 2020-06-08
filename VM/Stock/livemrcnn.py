import os
import sys
import cv2
import time
import imutils
import numpy as np
from multiprocessing import Process
ROOT_DIR = os.path.abspath("../mrcnn/")
sys.path.append(ROOT_DIR)  
sys.path.append(os.path.join(ROOT_DIR, "samples/coco/"))
import mrcnn.model as modellib
from mrcnn import utils, visualize
from imutils.video import WebcamVideoStream
import random
from samples.coco.coco import CocoConfig

MODEL_DIR = os.path.join(ROOT_DIR, "logs")
COCO_MODEL_PATH = os.path.join(ROOT_DIR, "mask_rcnn_coco.h5")

class InferenceConfig(CocoConfig):
    GPU_COUNT = 1
    IMAGES_PER_GPU = 1

config = InferenceConfig()
config.display()
model = modellib.MaskRCNN(mode="inference", model_dir=MODEL_DIR, config=config)
model.load_weights(COCO_MODEL_PATH, by_name=True)

class_names = ['BG', 'person', 'bicycle', 'car', 'motorcycle', 'airplane',
               'bus', 'train', 'truck', 'boat', 'traffic light',
               'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird',
               'cat', 'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear',
               'zebra', 'giraffe', 'backpack', 'umbrella', 'handbag', 'tie',
               'suitcase', 'frisbee', 'skis', 'snowboard', 'ball',
               'kite', 'sports devices', 'baseball glove', 'skateboard',
               'surfboard', 'tennis racket', 'bottle', 'glass', 'cup',
               'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple',
               'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza',
               'donut', 'cake', 'chair', 'couch', 'plant', 'bed',
               'table', 'toilet', 'display', 'laptop', 'mouse', 'remote',
               'keyboard', 'phone', 'microwave', 'oven', 'toaster',
               'sink', 'refrigerator', 'book', 'clock', 'vase', 'scissors',
               'doll', 'hair drier', 'toothbrush']

vs = cv2.VideoCapture('http://173.79.225.103:8080/video?dummy=param.mjpg')
vs.set(cv2.CAP_PROP_BUFFERSIZE, 1)

frame = 0

def format_output(r):
    output = []
    for i in range(len(r['class_ids'])):
        box = r['rois'][i].tolist()
        box = [box[1], box[0], box[3] - box[1], box[2] - box[0]]
        output.append([class_names[r['class_ids'][i]], int(r['scores'][i] * 100), box])
    return output

def getoutput():
    while(True):
        if frame != 0:
            results = model.detect([frame])
            r = results[0]
            print(format_output(r))

def getframes():
    while True:
        global frame
        grabbed, frame = vs.read()
        if not grabbed:
            break
        s = frame
        print(s.shape[0], s.shape[1])

if __name__ == '__main__':
    p1 = Process(target=getframes)
    p1.start()
    p2 = Process(target=getoutput)
    p2.start()
