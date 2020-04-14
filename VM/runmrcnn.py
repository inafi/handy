import os
os.environ["CUDA_VISIBLE_DEVICES"]="2"
import sys
import random
import math
import numpy as np
import skimage.io
import matplotlib
import matplotlib.pyplot as plt
ROOT_DIR = os.path.abspath("../mrcnn/")
sys.path.append(ROOT_DIR)  
sys.path.append(os.path.join(ROOT_DIR, "samples/coco/"))  
from mrcnn import utils
import mrcnn.model as modellib
from mrcnn import visualize
import coco
import cv2
from redis import Redis
import time

cli = Redis('localhost')

try:
	os.chdir(os.path.join(os.getcwd(), 'samples'))
	print(os.getcwd())
except:
	pass

#get_ipython().run_line_magic('matplotlib', 'inline')
MODEL_DIR = os.path.join(ROOT_DIR, "logs")
COCO_MODEL_PATH = os.path.join(ROOT_DIR, "mask_rcnn_coco.h5")

if not os.path.exists(COCO_MODEL_PATH):
    utils.download_trained_weights(COCO_MODEL_PATH)

class InferenceConfig(coco.CocoConfig):
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

def format_output(r):
    output = []
    for i in range(len(r['class_ids'])):
        box = r['rois'][i].tolist()
        box = [box[1], box[0], box[3] - box[1], box[2] - box[0]]
        output.append([class_names[r['class_ids'][i]], int(r['scores'][i] * 100), box])
    #Converts array to string
    s = ""
    for i in range(len(output)):
        s += output[i][0] + " " + str(output[i][1]) + " "
        for k in range(4):
            s += str(output[i][2][k]) + " "
        s += " "
    return s

init = 0
prev = 0

while(True):
    init = int(cli.get('read'))
    if init != prev:
        start = time.time()
        image = skimage.io.imread('../send.jpg')
        r = model.detect([image], verbose=1)[0]
        s = format_output(r) + str(time.time() - start)
        cli.set('writemrcnn', s) #join converts s from array to string
        cint = int(cli.get('confirm'))
        cint += 1
        cli.set('confirm', cint)
        print("mrcnn:", time.time() - start)
    prev = init

#visualize.display_instances(image, r['rois'], r['masks'], r['class_ids'], class_names, r['scores'])

