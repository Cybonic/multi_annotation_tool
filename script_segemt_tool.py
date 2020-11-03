# img_viewer.py
'''

'''
import PySimpleGUI as sg
import os.path
import yaml
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
import util.segment_util as seg_util 
import util
import util.util_tools as utils

fig = Figure()


IMG_HIGH = 480
IMG_WIDTH = 720

IMG_DOWN_SCALE_PERCENT = 40

class segment_obj:
    def __init__(self,label,xpixels,ypixels):
        self._label = label
        self._xpixel = xpixels
        self._ypixel = ypixels
    
    def get_idx(self):
        return(self._xpixel, self._ypixel)

    def get_label(self):
        return(self._label)

    def conv_to_str(self):

        x_str = ' '.join([str(v) for v in self._xpixel])
        y_str = ' '.join([str(v) for v in self._ypixel])

        str_segm = self._label + ':' + x_str + ':' + y_str

        return(str_segm)

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
        self.pixel_bag = [[],[]] 
        self.temp_pixel_bag = [[],[]]
        self.elem_list = []
        self.selectedlabel = []
        self.add_to_temp_obj_bag([])
        self.label_list = []
        self.mode = self.set_mode('bbox')
        self.unqlabel_list = []
        
        self.label_list_file = "riva_classes.yaml"
        root = os.getcwd()

        self.define_paths(root)


    def define_paths(self,root_path):
        
        self.root = root_path
        self.segment_path = os.path.join(root_path,'segment_labels')
        self.bb_path = os.path.join(root_path,'bbox_labels')
        self.resized_path = os.path.join(root_path,'image')

        utils.create_folder(self.segment_path)
        utils.create_folder(self.bb_path)
        utils.create_folder(self.resized_path)

            
    def get_mode(self):
        return(self.mode)

    def set_mode(self,mode):

        if mode  in ['bbox','segment']:
            self.mode = mode
            return(self.mode)
        else: 
            print("[WARNING] Mode does not exist!")
            return(None)
        
    def plot_empty_canvas(self):
        self.plot_canvas([],[])
        #self._window["-FILE LIST-"].update([])
        self._window["-ELEM LIST-"].update([])

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
        self.add_to_temp_obj_bag(bbox)
        # Compute bounding box pixels 
        x_pixels,y_pixels = imgh.generate_bbox_pixels(x_org,y_org,w,h)
        # Clear the previous boudning box pixels from the temp bag
        self.clear_temp_pixel_bag()
        # Add the new pixels to temp bag
        self.add_to_temp_pixel_bag(x_pixels,y_pixels)
        # Get all bounding box pixels from the current frame
        xp,yp = self.get_pixels()
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

        self.add_to_temp_pixel_bag(x_pixels,y_pixels)

        segment = segment_obj([],x_pixels,y_pixels)

        self.add_to_temp_obj_bag(segment)
        
        x_pixels,y_pixels = self.get_temp_pixels()
        self.plot_canvas(x_pixels,y_pixels)

  
    def plot_canvas(self,xp,yp):

        img = self._image_handler.get_curr_img()
        
        if (img.size == 0): # <- change here
            print("WARNING: No image found")
            return(None)

        img[yp,xp, 0] = 255
        img[yp,xp, 1] = 0
        img[yp,xp, 2] = 0

        imgbytes = imgh.conv_to_bytes(img)

        self._window["-IMAGE-"].update(data=imgbytes)

    def clear_temp_obj_bag(self):
        self.temp_obj_list = []

    def clear_temp_pixel_bag(self):
        self.temp_pixel_bag = [[],[]]
        
    def clear_temp(self):
        self.clear_temp_pixel_bag()
        self.clear_temp_obj_bag()
        self.first_bb_flag = False
        #self.selectedlabel = []

    def clear_pixel_bag(self):
        self.pixel_bag = [[],[]]

    def clear_obj_bag(self):
        self.elem_list = []

    def clear_elem(self):
        self.clear_pixel_bag()
        self.clear_obj_bag()
        self.label_list = []
        # self.clear_temp()

    def clear_all(self):
        self.clear_elem()
        self.clear_temp()
        #self.unqlabel_list = []

    def add_to_pixel_bag(self,xidx,yidx):

        self.pixel_bag[0] = np.concatenate((self.pixel_bag[0],xidx))
        self.pixel_bag[1] = np.concatenate((self.pixel_bag[1],yidx))

    def add_to_temp_pixel_bag(self,xidx,yidx):

        self.temp_pixel_bag[0] = np.concatenate((self.temp_pixel_bag[0],xidx))
        self.temp_pixel_bag[1] = np.concatenate((self.temp_pixel_bag[1],yidx))

    def add_to_temp_obj_bag(self,obj):
        self.temp_obj_list = obj

    def add_to_elem_list(self,bbox):
        self.elem_list.append(bbox)
        # print(self.unqlabel_list.index(bbox._label))
        # self.label_list.append(self.unqlabel_list[self.unqlabel_list.index(bbox._label)])
        return(self.label_list)

    def add_label_to_uniq_bag(self,label):
        list_length = len(self.unqlabel_list)
        self.unqlabel_list[label] = list_length + 1 
        return(list(self.unqlabel_list.keys()))

    def get_temp_obj_bag(self):
        return(self.temp_obj_list)
 
    def get_elem_list(self):
        return(self.elem_list)
    
    def get_pixels(self):
        
        xp,yp = np.array(self.pixel_bag,dtype = int)
        return(xp,yp)
        
    def get_temp_pixels(self):
        xp,yp = np.array(self.temp_pixel_bag,dtype = int)
        return(xp,yp)

    def get_unqlabels(self):
        return(self.unqlabel_list)

    def save_temp_to_elem(self,obj):

        # Add the current bounding box to permanent list
        self.add_to_elem_list(obj)
        # Get the current bbox pixels 
        xp,yp = self.get_temp_pixels()
        # Update frame pixels with the new bbox pixels 
        self.add_to_pixel_bag(xp,yp)

        # return(label_list)

    def save_elem_to_file(self):
        
        
        if self.mode == 'bbox':
            path = self.bb_path
        elif(self.mode == 'segment'): 
            path = self.segment_path

        if os.path.exists(path) == False:
            print("[ERROR] File does not exist")
            return()
        
        file_name = self._image_handler.get_curr_file_name()

        file_path = os.path.join(path,file_name)

        elem_list = self.get_elem_list()
        
        if self.mode == 'segment':
            # Convert element list to single image
            # load image characteristics 
            width, height = self._image_handler.get_im_dim()
            # segm_imge = imgh.create_img_tamplate(height,width,1)
            segment_img = seg_util.convert_segm_objs_to_img(height,width,elem_list)
            seg_img_file_name = file_path + '.png'
            cv2.imwrite( seg_img_file_name , segment_img)
        
        else:

            box_file_name = file_path + '.txt'
            f = open(box_file_name ,'w')
            for elem in elem_list:
                f.write(elem.conv_to_str() + '\n')
            f.close()

    def save_labels_to_file(self,labels):
        '''
        Save labels and indexes to a yaml file

        '''
        # Get file and root paths
        filename = self.label_list_file
        path = self.root
        # Build final file path
        file_path = os.path.join(path,filename)
        # Open file handler
        f = open(file_path,'w')
        # Convertion  of the labels to yaml format 
        doc = {"labels":labels}
        # Save the labels to yaml file
        yaml.dump(doc, f)
        f.close()

    def read_labels_from_file(self,file_path):
        '''
        
        Read ground truth labels from yaml file
        If no file exists, an empty list is returned
        
        Input:
         - file_path: file path to read labels from

        Output:
         - list of ground truth labels

        '''
        try: 
        # Open file handler 
            f = open(file_path,'r')
            dict_label_list = yaml.load(f, Loader=yaml.FullLoader)
            label_list = dict_label_list['labels']
        except:
            print("[WARN] Label file does not exist!")
            print("[INFO] Labels will be initialized empty!")
            label_list = dict([])
        
        return(label_list)

    def load_unqlabels(self,labels):
        self.unqlabel_list = labels

    def load_root_path(self,path):
        self.root = path
        
    def load_kernel_value(self,value):
        
        self._kernel_value = value

    def on_move(self,event):
    
        print('Pointer moved to {0}'.format(
            (event.x, event.y)))

    
    def save_img(self):
        '''
        Save the resized image 

        save_img()

        '''
        # Get the resized image
        img = self._image_handler.get_resized_img()
        # Get all the name 
        file_name = self._image_handler.get_curr_file_name()
        # Build the full name 
        file_path = os.path.join(self.resized_path ,file_name + '.png')
        # Write the resize image to a file
        imgh.write_to_file(img,file_path)


    def loop(self):
        
        while True:

            # print('The current pointer position is {0}'.format(mouse.position))
            event, values = self._window.read()
        
            if event == "Exit" or event == sg.WIN_CLOSED:
                break

            # Folder name was filled in, make a list of files in the folder
            if event == "-FOLDER-":

                folder = values["-FOLDER-"]

                # Get root path
                parent_folder = os.path.dirname(folder)  
                print("[INFO] Root image path: " + parent_folder)
                # Load root path

                self.define_paths(parent_folder)
                
                label_yaml_file = os.path.join(parent_folder,self.label_list_file)

                uniq_label_list = self.read_labels_from_file(label_yaml_file)
                self.load_unqlabels(uniq_label_list)
                label_plot = list(uniq_label_list.keys())

                try:
                    self._window["-FILE LIST-"].update(label_plot)
                except:
                    pass

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
                
                # self.unqlabel_list.append(label_name)
                plot_label_list = self.add_label_to_uniq_bag(label_name)
                
                try:
                    self._window["-FILE LIST-"].update(plot_label_list)
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
                #self.clear_pixel_bag()
                #self.clear_obj_bag()
                self.clear_all()
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
                self.set_mode('bbox')
                self.clear_all()
                self.plot_empty_canvas()

            elif event == "-RADIO2-":
            # Selection of segmentation tool
                self._window["-RADIO1-"].update(False)
                self._bbox_tool_flag = False
                self._segment_tool_flag = True
                #self.canvas.unbind("<Button-1>")
                self.canvas.bind('<B1-Motion>',self.left_click_segment)
                self.set_mode('segment')

                self.clear_all()
                self.plot_empty_canvas()
            
            elif  event == "-SAVE OBJ-":
                
                #print("[DEBUG] I'm SAVE obj")
                temp_bag = self.get_temp_obj_bag()
                label = self.selectedlabel
                unq_label = self.get_unqlabels()

                if label != [] and temp_bag != []:
                    
                    elem = temp_bag

                    if self.mode == 'bbox':
                        elem._label = label
                        label_str = label
                    else:
                        elem._label = unq_label[label]
                        label_str = utils.get_key(self.unqlabel_list,elem._label)
                        
                    self.save_temp_to_elem(elem)
                        
                    self.clear_temp()
                    
                    self.label_list.append(label_str)

                    self._window["-ELEM LIST-"].update(self.label_list)

            elif  event == "-DEL OBJ-":

                self.clear_temp()
                xp,yp = self.get_pixels()
                self.plot_canvas(xp,yp)
            
            elif event == "-DEL-":

                self.clear_elem()
                self.clear_temp()

                self._window["-ELEM LIST-"].update([])
                xp,yp = self.get_pixels()
                self.plot_canvas(xp,yp)

            elif event == "-SAVE-":
                # Save annotation data
                # Save unique label names 

                self.save_elem_to_file()
                self.save_img()

                label_list = self.get_unqlabels()
                self.save_labels_to_file(label_list)
                
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
        sg.Button('SAVE OBJ',enable_events=True, key="-SAVE OBJ-"),
        sg.Button('DEL OBJ',enable_events=True, key="-DEL OBJ-")
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
    [sg.FolderBrowse('Source'), sg.In(size=(40, 1), enable_events=True, key="-FOLDER-")],
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
    


    