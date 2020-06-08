import sys
import os
os.chdir('../pythia')
os.environ["CUDA_VISIBLE_DEVICES"]="1"
sys.path.append('content/pythia')
sys.path.append('content/vqa-maskrcnn-benchmark')
from pythia.common.sample import Sample, SampleList
from pythia.common.registry import registry
from pythia.models.pythia import Pythia
from pythia.utils.configuration import ConfigNode
from pythia.tasks.processors import VocabProcessor, CaptionProcessor
from pythia.models.butd import BUTD
from maskrcnn_benchmark.utils.model_serialization import load_state_dict
from maskrcnn_benchmark.structures.image_list import to_image_list
from maskrcnn_benchmark.modeling.detector import build_detection_model
from maskrcnn_benchmark.layers import nms
from maskrcnn_benchmark.config import cfg
from io import BytesIO
from ipywidgets import widgets, Layout
from IPython.display import display, HTML, clear_output
from PIL import Image
import torchvision.transforms as transforms
import torchvision.models as models
import pandas as pd
import torch.nn.functional as F
import gc
import numpy as np
import requests
import torch
import cv2
import yaml
from redis import Redis
import time

cli = Redis("localhost")

class PythiaDemo:
  TARGET_IMAGE_SIZE = [448, 448]
  CHANNEL_MEAN = [0.485, 0.456, 0.406]
  CHANNEL_STD = [0.229, 0.224, 0.225]
  
  def __init__(self):
    self._init_processors()
    self.pythia_model = self._build_pythia_model()
    self.detection_model = self._build_detection_model()
    
  def _init_processors(self):
    with open("content/model_data/butd.yaml") as f:
      config = yaml.load(f)
    
    config = ConfigNode(config)
    # Remove warning
    config.training_parameters.evalai_inference = True
    registry.register("config", config)
    
    self.config = config
    
    captioning_config = config.task_attributes.captioning.dataset_attributes.coco
    text_processor_config = captioning_config.processors.text_processor
    caption_processor_config = captioning_config.processors.caption_processor
    
    text_processor_config.params.vocab.vocab_file = "content/model_data/vocabulary_captioning_thresh5.txt"
    caption_processor_config.params.vocab.vocab_file = "content/model_data/vocabulary_captioning_thresh5.txt"
    self.text_processor = VocabProcessor(text_processor_config.params)
    self.caption_processor = CaptionProcessor(caption_processor_config.params)

    registry.register("coco_text_processor", self.text_processor)
    registry.register("coco_caption_processor", self.caption_processor)
    
  def _build_pythia_model(self):
    state_dict = torch.load('content/model_data/butd.pth')
    model_config = self.config.model_attributes.butd
    model_config.model_data_dir = "content/"
    model = BUTD(model_config)
    model.build()
    model.init_losses_and_metrics()
    
    if list(state_dict.keys())[0].startswith('module') and \
       not hasattr(model, 'module'):
      state_dict = self._multi_gpu_state_to_single(state_dict)
          
    model.load_state_dict(state_dict)
    model.to("cuda")
    model.eval()
    
    return model
  
  def _multi_gpu_state_to_single(self, state_dict):
    new_sd = {}
    for k, v in state_dict.items():
        if not k.startswith('module.'):
            raise TypeError("Not a multiple GPU state of dict")
        k1 = k[7:]
        new_sd[k1] = v
    return new_sd
  
  def predict(self, url):
    with torch.no_grad():
      detectron_features = self.get_detectron_features(url)

      sample = Sample()
      sample.dataset_name = "coco"
      sample.dataset_type = "test"
      sample.image_feature_0 = detectron_features
      sample.answers = torch.zeros((5, 10), dtype=torch.long)

      sample_list = SampleList([sample])
      sample_list = sample_list.to("cuda")

      tokens = self.pythia_model(sample_list)["captions"]
    
    gc.collect()
    torch.cuda.empty_cache()
    
    return tokens
    
  
  def _build_detection_model(self):

      cfg.merge_from_file('content/model_data/detectron_model.yaml')
      cfg.freeze()

      model = build_detection_model(cfg)
      checkpoint = torch.load('content/model_data/detectron_model.pth', 
                              map_location=torch.device("cpu"))

      load_state_dict(model, checkpoint.pop("model"))

      model.to("cuda")
      model.eval()
      return model
  
  def get_actual_image(self, image_path):
      if image_path.startswith('http'):
          path = requests.get(image_path, stream=True).raw
      else:
          path = image_path
      
      return path

  def _image_transform(self, image_path):
      path = self.get_actual_image(image_path)

      img = Image.open(path)
      im = np.array(img).astype(np.float32)
      im = im[:, :, ::-1]
      im -= np.array([102.9801, 115.9465, 122.7717])
      im_shape = im.shape
      im_size_min = np.min(im_shape[0:2])
      im_size_max = np.max(im_shape[0:2])
      im_scale = float(800) / float(im_size_min)
      # Prevent the biggest axis from being more than max_size
      if np.round(im_scale * im_size_max) > 1333:
           im_scale = float(1333) / float(im_size_max)
      im = cv2.resize(
           im,
           None,
           None,
           fx=im_scale,
           fy=im_scale,
           interpolation=cv2.INTER_LINEAR
       )
      img = torch.from_numpy(im).permute(2, 0, 1)
      return img, im_scale


  def _process_feature_extraction(self, output,
                                 im_scales,
                                 feat_name='fc6',
                                 conf_thresh=0.2):
      batch_size = len(output[0]["proposals"])
      n_boxes_per_image = [len(_) for _ in output[0]["proposals"]]
      score_list = output[0]["scores"].split(n_boxes_per_image)
      score_list = [torch.nn.functional.softmax(x, -1) for x in score_list]
      feats = output[0][feat_name].split(n_boxes_per_image)
      cur_device = score_list[0].device

      feat_list = []

      for i in range(batch_size):
          dets = output[0]["proposals"][i].bbox / im_scales[i]
          scores = score_list[i]

          max_conf = torch.zeros((scores.shape[0])).to(cur_device)

          for cls_ind in range(1, scores.shape[1]):
              cls_scores = scores[:, cls_ind]
              keep = nms(dets, cls_scores, 0.5)
              max_conf[keep] = torch.where(cls_scores[keep] > max_conf[keep],
                                           cls_scores[keep],
                                           max_conf[keep])

          keep_boxes = torch.argsort(max_conf, descending=True)[:100]
          feat_list.append(feats[i][keep_boxes])
      return feat_list

  def masked_unk_softmax(self, x, dim, mask_idx):
      x1 = F.softmax(x, dim=dim)
      x1[:, mask_idx] = 0
      x1_sum = torch.sum(x1, dim=1, keepdim=True)
      y = x1 / x1_sum
      return y
    
  def get_detectron_features(self, image_path):
      im, im_scale = self._image_transform(image_path)
      img_tensor, im_scales = [im], [im_scale]
      current_img_list = to_image_list(img_tensor, size_divisible=32)
      current_img_list = current_img_list.to('cuda')
      with torch.no_grad():
          output = self.detection_model(current_img_list)
      feat_list = self._process_feature_extraction(output, im_scales, 
                                                  'fc6', 0.2)
      return feat_list[0]

demo = PythiaDemo()

#image_text = "http://images.cocodataset.org/train2017/000000505539.jpg"
cli.set("readpy", 0)
init = int(cli.get("readpy").decode('utf-8'))
prev = init
while(True):
    init = int(cli.get("readpy").decode('utf-8'))
    if init != prev:
        print(init, prev)
        start = time.time()
        image_text = "send.jpg"
        clear_output()
        image_path = demo.get_actual_image(image_text)
        image = Image.open(image_path)

        tokens = demo.predict(image_text)
        answer = demo.caption_processor(tokens.tolist()[0])["caption"]
        print(answer, time.time() - start)
    prev = init
