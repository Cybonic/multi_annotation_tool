
import os 
from os import listdir
import cv2
from PIL import Image 

import util.util_tools as util
DATASET_PATH = 'sample'

def onMouse(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
       # draw circle here (etc...)
       print('x = %d, y = %d'%(x, y))

# setMouseCallback('WindowName', onMouse')

if __name__ == "__main__":
    
    # Load image 
    dataset = DATASET_PATH
    image_set_files = util.get_files(dataset)

    n_files = len(image_set_files)
    cv2.setMouseCallback('WindowName', onMouse)

    for file_name in image_set_files:
        img = Image.open(file_name)
        img.show()

        
        #img = cv2.imread(file_name)
        #cv2.imshow('im',img) 

    # image_set_files = [f for f in listdir(dataset) if os.path.isfile(os.path.join(dataset, f))]

    # Define Labeling structure 

    # 