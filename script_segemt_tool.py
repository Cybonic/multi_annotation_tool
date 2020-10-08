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

class segment_obj:
    def __init__(self,label,xpixels,ypixels):
        self._label = label
        self._xpixel = xpixels
        self._ypixel = ypixels
    
    def conv_to_str(self):

        x_str = ' '.join([str(v) for v in self._xpixel])
        y_str = ' '.join([str(v) for v in self._ypixel])

        str_segm = self._label + ':'

class bbox_object:
    def __init__(self,x,y,w,h,label):
        self._x = x
        self._y = y
        self._label = label
        self._w = w
        self._h = h
    
    def conv_to_str(self):

        str_bb = self._label + " " + str(self._x) + " " +  str(self._y) + " " + str(self._y) + " " + str(self._h) + " " + str(self._w)
        return(str_bb)
                  

class bounding_box:
    def __init__(self):
        self.upper_left_corner = (0,0)
        self.bottom_right_corner = (0,0)
        # self.finished_bb_flag = 0
        #self.first_bb_flag = False
        self.h = 0
        self.w = 0
        self.label = ''

    def set_first_corner(self,x,y):
        self.upper_left_corner = (x,y)
        

    def set_last_corner(self,x,y):
        self.bottom_right_corner = (x,y)
        #self.first_bb_flag = False
        
    def comp_bbox(self,ci,cf):
        '''
        Compute bounding box parameters after obtaining upper and bottom corners

        '''
        xi,yi = ci
        xf,yf = cf

        self.h = yf - yi
        self.w = xf - xi

        self.h_dirct = np.sign(self.h)
        self.w_dirct = np.sign(self.w)

        if self.w == 0:
            self.w +=1
        if self.h == 0:
            self.h +=1

        self.y_orig = int(yi + self.h/2)
        self.x_orig = int(xi + self.w/2)

        # self.first_bb_flag = False

        print("h: " +str(self.h) + " w: " + str(self.w))
        print("x: " + str(self.x_orig) + " y: " + str(self.y_orig))

        return(self.x_orig,self.y_orig,self.w,self.h)

    def set_label(self,label):
        self.label = label
    
class segment_gui:
    def __init__(self,window,img_hight,img_width,img_down_scale,destin_path):
        self._window = window
        self._image_handler = imgh.image_handler(img_hight,img_width,img_down_scale)

        self._bb_tool = bounding_box()
        self._bbox_tool_flag =True
        self._segment_tool_flag = False
        self.first_bb_flag = False

        canvas_elem = window['-IMAGE-']
        self.canvas = canvas_elem.Widget
        
        self.canvas.bind('<B1-Motion>',self.left_click_bb)
        self._kernel_value = 2
        self.pixel_idx_to_plot = [[],[]] 
        self.one_frame_pixels_idx = [[],[]]
        self.bbox_list = []
        self.selectedlabel = []
        self.add_to_temp_bbox_bag([])
        self.label_list = []

        root = os.getcwd()
        self.segment_path = os.path.join(root,destin_path,'segment_labels')
        self.bb_path = os.path.join(root,destin_path,'bbox_labels')

        try:
            os.makedirs(self.segment_path)
        except OSError:
            print ("Creation of the directory %s failed" % self.segment_path)
        else:
            print ("Successfully created the directory %s " % self.segment_path)

        try:
            os.makedirs(self.bb_path)
        except OSError:
            print ("Creation of the directory %s failed" % self.bb_path)
        else:
            print ("Successfully created the directory %s " % self.bb_path)


    def pointer_pixels(self,x,y,point_size):

        kernel_x,kernel_y = imgh.get_kernel(point_size)

        kernel_x_idx = kernel_x + x
        kernel_y_idx = kernel_y + y
        return(kernel_x_idx,kernel_y_idx)

        
    def left_click_bb(self,event):
        '''
        Define first bounding box corner
        
        '''
        x,y = event.x,event.y

        if self.first_bb_flag == False:
            self.first_bb_flag = True
            self._bb_tool.set_first_corner(x,y)
            self.pi = (x,y)
            #self.plot_pointer_kernel(x,y,2)
            return

        # Final corner
        pf = (x,y)
        # compute bounding box
        x_org,y_org,w,h = self._bb_tool.comp_bbox(self.pi,pf)
        bbox = bbox_object(x_org,y_org,w,h,[])
        # Add to temporary list
        self.add_to_temp_bbox_bag(bbox)
        # Compute bounding box pixels 
        x_pixels,y_pixels = imgh.generate_bbox_pixels(x_org,y_org,w,h)
        # Clear the previous boudning box pixels from the temp bag
        self.clear_temp_pixel_bag()
        # Add the new pixels to temp bag
        self.add_pixels_to_temp_bag(x_pixels,y_pixels)
        # Get all bounding box pixels from the current frame
        xp,yp = self.get_frame_pixels()
        # Merge all pixels for plotting
        ypixels = np.concatenate((y_pixels,yp))
        xpixels = np.concatenate((x_pixels,xp))
        # refresh frame       
        self.plot_canvas(xpixels,ypixels)
    
    def left_click_segment(self,event):

        x,y = event.x,event.y
        self.right_click_pose = (event.x,event.y)

        kernel_size = int(self._window["-SLIDER-"].TKScale.get())

        self.load_kernel_value(kernel_size)

        x_pixels,y_pixels = self.pointer_pixels(x,y,kernel_size)

        self.add_pixels_to_temp_bag(x_pixels,y_pixels)
        
        x_pixels,y_pixels = self.get_temp_pixels()
        self.plot_canvas(x_pixels,y_pixels)
    

    def reset_bbox_settings(self):
        
        self.bbox_list = []
        self.label_list = []
        self.reset_temp()

    def get_pixels(self):
        if np.array(self.pixel_idx_to_plot).size > 0:
            xp,yp = np.array(self.pixel_idx_to_plot,dtype = int)
            return(xp,yp)
        else: 
            return([],[])

    def get_temp_pixels(self):
        xp,yp = np.array(self.one_frame_pixels_idx,dtype = int)
        return(xp,yp)
    
    def get_frame_pixels(self):
        xp,yp = np.array(self.pixel_idx_to_plot,dtype = int)
        return(xp,yp)

    

    def plot_canvas(self,xp,yp):

        img = self._image_handler.get_curr_img()
        
        img[yp,xp, 0] = 255
        img[yp,xp, 1] = 0
        img[yp,xp, 2] = 0

        imgbytes = imgh.conv_to_bytes(img)

        self._window["-IMAGE-"].update(data=imgbytes)

    def clear_temp_pixel_bag(self):
        self.one_frame_pixels_idx = [[],[]]
        
    def reset_temp(self):
        self.clear_temp_pixel_bag()
        self.clear_temp_bbox_bag()
        self.first_bb_flag = False

    def clear_pixel_bag(self):
        self.pixel_idx_to_plot = [[],[]]


    def add_to_pixel_bag(self,xidx,yidx):

        self.pixel_idx_to_plot[0] = np.concatenate((self.pixel_idx_to_plot[0],xidx))
        self.pixel_idx_to_plot[1] = np.concatenate((self.pixel_idx_to_plot[1],yidx))

    def add_pixels_to_temp_bag(self,xidx,yidx):

        self.one_frame_pixels_idx[0] = np.concatenate((self.one_frame_pixels_idx[0],xidx))
        self.one_frame_pixels_idx[1] = np.concatenate((self.one_frame_pixels_idx[1],yidx))

        #self.one_frame_pixels_idx[0] = xidx.reshape((1,-1))
        #self.one_frame_pixels_idx[1] = yidx.reshape((1,-1))
    def get_temp_bbox_bag(self):
        return(self.select_bbox)

    def clear_temp_bbox_bag(self):
        self.select_bbox = []

    def add_to_temp_bbox_bag(self,bbox):
        self.select_bbox = bbox

    def add_to_bbox_list(self,bbox):
        self.bbox_list.append(bbox)
        self.label_list.append(bbox._label)
        return(self.label_list)
    
    def del_bbox(self):
        self.clear_pixel_bag()
        self.reset_bbox_settings()
    

    def get_bbox_list(self):
        return(self.bbox_list)
    
    def save_bbox(self,bbox):

        # Add the current bounding box to permanent list
        label_list = self.add_to_bbox_list(bbox)
        # Get the current bbox pixels 
        xp,yp = self.get_temp_pixels()
        # Update frame pixels with the new bbox pixels 
        self.add_to_pixel_bag(xp,yp)

        return(label_list)

    def save_bbox_to_file(self):
        file_name = self._image_handler.get_curr_file_name()
        file_path = os.path.join(self.bb_path,file_name+ '.txt')

        f = open(file_path,'w')
        bbox_list = self.get_bbox_list()
        for bbox in bbox_list:
            f.write(bbox.conv_to_str() + '\n')
        f.close()

    def load_kernel_value(self,value):
        
        self._kernel_value = value

    def on_move(self,event):
    
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
                    f
                    for f in file_list
                    if os.path.isfile(os.path.join(folder, f))
                ]

                self._image_handler.load_img_list(imagelist,folder)

                imgbytes = self._image_handler.get_next_img()

                self._window["-IMAGE-"].update(data=imgbytes)

            elif event == "-OK-":

                label_name = values["-LABEL-"]
                label_list = self._image_handler.appendLabel(label_name)
                
                try:
                    self._window["-FILE LIST-"].update(label_list)
                except:
                    pass

            elif event == "-FILE LIST-":  
                # A file was chosen from the listbox

                self.selectedlabel = values["-FILE LIST-"][0]

                try:
                    self._window["-TOUT-"].update(self.selectedlabel)
                except:
                    pass
            
            elif event == "-NEXT-":
                # NEXT button was pressed: show next image
                self.clear_pixel_bag()
                self.reset_bbox_settings()
                self._window["-ELEM LIST-"].update([])

                imgbytes = self._image_handler.get_next_img() # Get next image (as byte format) in line 
                self._window["-IMAGE-"].update(data=imgbytes) # Upload image to GUI
            
            elif event == "-PREV-":
                self.clear_pixel_bag()
                # PREVIOUS button was pressed: show the previous image again
                imgbytes = self._image_handler.get_prev_img()
                self._window["-IMAGE-"].update(data=imgbytes)
            
            elif event == "-RADIO1-":
            # Selection bounding box tool
                self._window["-RADIO2-"].update(False)
                self._bbox_tool_flag = True
                self._segment_tool_flag = False
                
                self.canvas.bind('<B1-Motion>',self.left_click_bb)

            elif event == "-RADIO2-":
            # Selection of segmentation tool
                self._window["-RADIO1-"].update(False)
                self._bbox_tool_flag = False
                self._segment_tool_flag = True
                #self.canvas.unbind("<Button-1>")
                self.canvas.bind('<B1-Motion>',self.left_click_segment)
            
            elif  event == "-SAVE ELEMT-":
                
                temp_bag = self.get_temp_bbox_bag()
                label = self.selectedlabel

                if label != [] and temp_bag != []:
                    bbox = self.select_bbox
                    bbox._label = label
                    label_list = self.save_bbox(bbox)
                    self.reset_temp()
                    self._window["-ELEM LIST-"].update(label_list)

            elif  event == "-DEL ELEMT-":

                self.reset_temp()
                xp,yp = self.get_pixels()
                self.plot_canvas(xp,yp)
            
            elif event == "-DEL-":
                self.del_bbox()
                self._window["-ELEM LIST-"].update([])
                xp,yp = self.get_pixels()
                self.plot_canvas(xp,yp)

            elif event == "-SAVE-":
                self.save_bbox_to_file()
                
        self._window.close()

# First the window layout in 2 columns

file_list_column = [
    [
        sg.Radio('Bounding Box', "radio" ,key = "-RADIO1-",enable_events=True,default=True)
    ],
    [
     sg.Radio('Segmentation',"radio",key = "-RADIO2-",enable_events=True)
    ],
    [
        sg.Text("Kernel"),
        sg.Slider(range=(0,50),default_value=2,size=(12,20),orientation='horizontal',font=('Helvetica', 10),key='-SLIDER-'),
    ],
    [
        sg.Text("Label"),
        sg.In(size=(10, 1), enable_events=True, key="-LABEL-"),
        sg.Button('Ok',enable_events=True, key="-OK-"),
    ],
    [
        sg.Listbox(values=[], enable_events=True, size=(20, 10), key="-FILE LIST-")
    ],
    [
        sg.Button('SAVE ELEMT',enable_events=True, key="-SAVE ELEMT-"),
        sg.Button('DEL ELEMT',enable_events=True, key="-DEL ELEMT-")
    ],
    [
        sg.Text("Elemtents")
    ],
    [
        sg.Listbox(values=[], enable_events=True, size=(20, 10), key="-ELEM LIST-")
    ],
    [
        sg.Button('SAVE',enable_events=True, key="-SAVE-"),
        sg.Button('DEL',enable_events=True, key="-DEL-"),
    ],
    
]

# For now will only show the name of the file that was chosen
image_viewer_column = [
    [sg.FolderBrowse(),sg.In(size=(40, 1), enable_events=True, key="-FOLDER-")],
    [sg.Text("Choose an image from list on left:")],
    [sg.Text(size=(40, 1), key="-TOUT-")],
    [sg.Image(size=(720, 480),key="-IMAGE-")],
    [sg.Button('PREV',enable_events=True, key="-PREV-"),
     sg.Button('NEXT',enable_events=True, key="-NEXT-"),
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
                        IMG_DOWN_SCALE_PERCENT,
                        'labels'
                        )

    gui.loop()
    


    