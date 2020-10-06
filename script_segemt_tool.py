# img_viewer.py
'''





'''
import PySimpleGUI as sg
import os.path
from PIL import Image
import cv2
import numpy as np
from mpld3 import plugins
# import win32api
# import win32con
from pynput import mouse
import wx
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from PIL import Image, ImageTk

from util import image_util as imgh
import util 

fig = Figure()


IMG_HIGH = 480
IMG_WIDTH = 720

IMG_DOWN_SCALE_PERCENT = 40
class segment_gui:
    def __init__(self,window,img_hight,img_width,img_down_scale):
        self._window = window
        self._image_handler = imgh.image_handler(img_hight,img_width,img_down_scale)

        canvas_elem = window['-IMAGE-']
        canvas = canvas_elem.Widget
        canvas.bind('<Motion>',self.on_move)
        canvas.bind('<Button-1>',self.left_click_segment)
        self._kernel_value = 2

    def left_click_segment(self,event):
        # 
        x,y = event.x,event.y
        self.right_click_pose = (event.x,event.y)
        #self.event_generate('<Button-3>', x=event.x, y=event.y)
        #return 'break'
        img = self._image_handler.get_curr_img()

        kernel_x,kernel_y = imgh.get_kernel(self._kernel_value)

        kernel_x_idx = kernel_x + x
        kernel_y_idx = kernel_y + y
       
        img[kernel_y_idx,kernel_x_idx, 0] = 255
        img[ kernel_y_idx,kernel_x_idx, 1] = 0
        img[ kernel_y_idx,kernel_x_idx, 2] = 0
 
        imgbytes = imgh.conv_to_bytes(img)
      
        self._window["-IMAGE-"].update(data=imgbytes)

    def load_kernel_value(self,value):
        self._kernel_value = value

    def on_move(self,event):
    
        # cv2.waitKey(1)
        print('Pointer moved to {0}'.format(
            (event.x, event.y)))

    def click_event(self,event, x, y, flags, param):
        if event == cv2.EVENT_MOUSEMOVE and event == cv2.EVENT_LBUTTONDOWN:
            print(x,",",y)
        

    def loop(self):
        
        while True:

            # print('The current pointer position is {0}'.format(mouse.position))
            event, values = self._window.read()
        
            if event == "Exit" or event == sg.WIN_CLOSED:
                break

            # Folder name was filled in, make a list of files in the folder
            if event == "-FOLDER-":

                folder = values["-FOLDER-"]

                try:
                    # Get list of files in folder
                    file_list = os.listdir(folder)
                except:
                    file_list = []

                imagelist = [
                    os.path.join(folder, f)
                    for f in file_list
                    if os.path.isfile(os.path.join(folder, f))
                ]

                self._image_handler.load_img_list(imagelist)

                imgbytes = self._image_handler.get_next_img()

                self._window["-IMAGE-"].update(data=imgbytes)

            elif event == "-KERNELOK-":
                kernel_value_str = values["-KERNEL-"]

                if kernel_value_str == '':
                    kernel_value=2
                else:
                    kernel_value = int(kernel_value_str)

                self.load_kernel_value(kernel_value)

            elif event == "-OK-":

                label_name = values["-LABEL-"]
                label_list = self._image_handler.appendLabel(label_name)
                
                try:
                    self._window["-FILE LIST-"].update(label_list)
                except:
                    pass

            elif event == "-FILE LIST-":  # A file was chosen from the listbox

                selectedlabel = values["-FILE LIST-"][0]

                try:
                    self._window["-TOUT-"].update(selectedlabel)
                except:
                    pass
            
            elif event == "-NEXT-":
                # NEXT button was pressed: show next image

                imgbytes = self._image_handler.get_next_img() # Get next image (as byte format) in line 
                self._window["-IMAGE-"].update(data=imgbytes) # Upload image to GUI
            
            elif event == "-PREV-":
                # PREVIOUS button was pressed: show the previous image again
                imgbytes = self._image_handler.get_prev_img()
                self._window["-IMAGE-"].update(data=imgbytes)
        
        self._window.close()

# First the window layout in 2 columns

file_list_column = [
    [
        sg.Text("Kernel"),
        sg.In(size=(9, 1), enable_events=True, key="-KERNEL-"),
        sg.Button('Ok',enable_events=True, key="-KERNELOK-"),
    ],
    [
        sg.Text("Label"),
        sg.In(size=(10, 1), enable_events=True, key="-LABEL-"),
        sg.Button('Ok',enable_events=True, key="-OK-"),
    ],
    [
        sg.Listbox(
            values=[], enable_events=True, size=(20, 10), key="-FILE LIST-"
        )
    ],
]

# For now will only show the name of the file that was chosen
image_viewer_column = [
    [sg.FolderBrowse(),sg.In(size=(40, 1), enable_events=True, key="-FOLDER-")],
    [sg.Text("Choose an image from list on left:")],
    [sg.Text(size=(40, 1), key="-TOUT-")],
    [sg.Image(size=(720, 480),key="-IMAGE-")],
    [sg.Button('NEXT',enable_events=True, key="-NEXT-"),
     sg.Button('PREV',enable_events=True, key="-PREV-"),
     sg.Button('Zoom In',enable_events=True, key="-ZOOMIN-"),
     sg.Button('Zoom Out',enable_events=True, key="-ZOOMOUT-")],
]


# ----- Full layout -----
layout = [
    [
        sg.Column(image_viewer_column),
        sg.VSeperator(),
        sg.Column(file_list_column),
    ]
]


if __name__ == "__main__":
  

    window = sg.Window("Image Segmentation Tool", layout).Finalize()

    gui = segment_gui(  window,
                        IMG_HIGH,
                        IMG_WIDTH,
                        IMG_DOWN_SCALE_PERCENT
                        )

    gui.loop()
    


    