# Copyright 2024 antillia.com Toshiyuki Arai
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

# 2024/01/28 
# create_base_dataset.py
# 2024/02/20 Modified to call normalize in create_image_files function.

import os
import sys
import shutil
import cv2

import glob
import numpy as np
import math
import nibabel as nib
import traceback

# Read file
"""
scan = nib.load('/path/to/stackOfimages.nii.gz')
# Get raw data
scan = scan.get_fdata()
print(scan.shape)
(num, width, height)

"""
# See : https://github.com/neheller/kits19/blob/master/starter_code/visualize.py

H = 512
W = 512

# This function has been taken from visualize.py
# https://github.com/neheller/kits19/blob/master/starter_code/visualize.py
#
def class_to_color(segmentation, kidney_color, tumor_color, tumor_only=True):
    # initialize output to zeros
    shp = segmentation.shape
    seg_color = np.zeros((shp[0], shp[1], 3), dtype=np.float32)

    # set output to appropriate color at each location
    # 2023/08/10 antillia.com
    if tumor_only:
      # Set a kidney mask color to be black 
      kidney_color = [0, 0, 0]
    seg_color[np.equal(segmentation, 1)] = kidney_color
    seg_color[np.equal(segmentation, 2)] = tumor_color
    return seg_color
  
"""
def get_mask_boundingbox( mask):
    gray = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)

    ret, bin_img = cv2.threshold(gray, 20, 255, cv2.THRESH_BINARY)

    contours, hierarchy = cv2.findContours(
       bin_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    #contours = list(filter(lambda x: cv2.contourArea(x) > 100, contours))
    points = np.array(contours[0])
    #print(points)
    x, y, w, h = cv2.boundingRect(points)
    rect = (x, y, w, h)
    return rect
"""

class ImageMaskDatasetGenerator:

  def __init__(self, images_dir, labels_dir, output_images_dir, output_masks_dir):
    self.images_dir = images_dir
    self.labels_dir = labels_dir
    self.output_images_dir = output_images_dir
    self.output_masks_dir  = output_masks_dir
   
  def create_mask_files(self, img_file, name, output_dir, index):
    print("--- niigz {}".format(img_file))
    img = nib.load(img_file)
    
    data = img.get_fdata()
    print("---create_mask_files data shape {} ".format(data.shape))
    shape = data.shape
    if len(shape) == 4:
      data = data.reshape((shape[0], shape[1], shape[2]))
      #data = data.reshape((shape[0], shape[2], shape[1]))
    print("--- data.shape {}".format(data.shape))
    num_images = data.shape[1] 
    print("--- num_images {}".format(num_images))

    num = 0
  
    for i in range(num_images):
      #img = data[:, :, i]
      img = data[:,i,:]

      #img = class_to_color(img, KIDNEY_COLOR, TUMOR_COLOR) 
      img = np.array(img)*255.0      
      img = img.astype("uint8") 

      filename = str(index + i) + "_" + name + ".jpg"
      if np.any(img > 0):
        filepath = os.path.join(output_dir, filename)
        image = cv2.resize(img, (W, H))
        image = cv2.rotate(image,cv2.ROTATE_90_COUNTERCLOCKWISE)
        cv2.imwrite(filepath, image)
        print("Saved {}".format(filepath))
        num += 1
    return num
  
  def normalize(self, image):
    min = np.min(image)/255.0
    max = np.max(image)/255.0
    scale = (max - min)
    image = (image - min) / scale
    image = image.astype('uint8') 
    return image   

  def create_image_files(self, image_file, name, output_masks_dir, output_images_dir, index):
   
    img = nib.load(image_file)

    data = img.get_fdata()
    print("---create_image_files data shape {} ".format(data.shape))
    print("--- shape {}".format(data.shape))
    shape = data.shape
  
    if len(shape) == 4:
      data = data.reshape((shape[0], shape[1], shape[2]))
      #data = data.reshape((shape[0], shape[2], shape[1]))

    num_images = data.shape[1] # 
    print("--- num_images {}".format(num_images))
    num = 0
 
    for i in range(num_images):
      #img = data[:, :, i]
      img = data[:,i,:,]
      
      #img = img.astype("uint8")
      # 2024/02/20  
      img = self.normalize(img)

      filename = str(index + i) + "_" + name + ".jpg"

      mask_filepath = os.path.join(output_masks_dir, filename)
      if os.path.exists(mask_filepath):
        filepath = os.path.join(output_images_dir, filename)
        image = cv2.resize(img, (W, H))
        image = cv2.rotate(image,cv2.ROTATE_90_COUNTERCLOCKWISE)
 
        cv2.imwrite(filepath, image)
        print("Saved {}".format(filepath))
        num += 1
    return num
  

  def generate(self):

    image_files = glob.glob(self.images_dir + "/*.img")
    index = 10000

    for image_file in image_files:
        basename  = os.path.basename(image_file)
        name      = basename.split(".")[0]
        img_name  = basename.split(".")[0]
        mask_name = img_name + "_Hipp_Labels.img"
        mask_file = os.path.join(self.labels_dir, mask_name)
        print("---image file {}".format(image_file))

        print("---mask file {}".format(mask_file))
        
        # 1 create mask files at first. 
        num_masks  = self.create_mask_files(mask_file,   name, self.output_masks_dir,  index)
        # 2 create image files if mask files exist.
        num_images = self.create_image_files(image_file, name, self.output_masks_dir, 
                                             self.output_images_dir, index)
        print(" num_images: {}  num_masks: {}".format(num_images, num_masks))


if __name__ == "__main__":
  try:
    images_dir        = "./Train"
    labels_dir        = "./Train/Labels"
    output_images_dir = "./Hippocampus-master/train/images/"
    output_masks_dir  = "./Hippocampus-master/train/masks/"

    if os.path.exists(output_images_dir):
      shutil.rmtree(output_images_dir)
    if not os.path.exists(output_images_dir):
      os.makedirs(output_images_dir)

    if os.path.exists(output_masks_dir):
      shutil.rmtree(output_masks_dir)
    if not os.path.exists(output_masks_dir):
      os.makedirs(output_masks_dir)

    # Create jpg image and mask files from nii.gz files under data_dir.

    generator = ImageMaskDatasetGenerator(images_dir, labels_dir, 
                                          output_images_dir, output_masks_dir)
    generator.generate()


  except:
    traceback.print_exc()


