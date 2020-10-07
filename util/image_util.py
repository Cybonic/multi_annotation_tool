import cv2
import numpy as np
import os


class image_handler:
    def __init__(self,taget_hight,target_with,scalepercent):
        self._imglist = []
        self._imgitr = 0
        self._scalepercent = scalepercent
        self._hight = taget_hight
        self._width = target_with
        self._label_list = []
        
    def appendLabel(self,labelname):
        self._label_list.append(labelname)
        return(self._label_list)

    def load_img_list(self,img_list,folder):
        self._file_list = img_list
        self._imglist = [os.path.join(folder, f) for f in self._file_list]
       
        return(len(self._imglist))

    def get_img_list(self):
        return(self._imglist)

    def img_down_scale(self,img,scalepercent):
        # scale_percent = IMG_DOWN_SCALE_PERCENT # percent of original size
        width = int(img.shape[1] * scalepercent / 100)
        height = int(img.shape[0] * scalepercent / 100)

        dim = (width, height)
        
        # resize image
        resized = cv2.resize(img, dim, interpolation = cv2.INTER_AREA)
        return(resized)
    
    def get_img(self,itr):
        '''
        
        Load image to memory.

        reajust imga scale to fit into the screen frame. 
        For that:
            ratios between target size/image size for both hight and width 
            are computed and the smallest is used for downscaling.

        '''
        imgfile = self._imglist[itr]
        img = cv2.imread(imgfile)

        hight,width = img.shape[0],img.shape[1]

        rh = self._width/width
        rw = self._hight/hight

        ratio = np.array([rh,rw])
        idx = np.argmin(ratio)
        percent = ratio[idx]*100

        resized_img = self.img_down_scale(img,percent)
        #imgbytes = cv2.imencode(".png", resized)[1].tobytes()
        
        self.image_t = resized_img
        return(resized_img)

    def get_curr_img(self):
        img = self.get_img(self._imgitr)
        return(img)

    def get_next_img(self):
        self._imgitr += 1
        img = self.get_img(self._imgitr)
        imgbytes = conv_to_bytes(img)
        return(imgbytes)
    
    def get_prev_img(self):
        self._imgitr -= 1
        img = self.get_img(self._imgitr)
        imgbytes = conv_to_bytes(img)
        return(imgbytes)

    def get_curr_file_name(self):
        return(self._file_list[self._imgitr].split('.')[0])
        #names = file_path.split()
        #names

def conv_to_bytes(img):

    return(cv2.imencode(".png", img)[1].tobytes())


def get_kernel(size):
    #kernel_size = 2
    l = size
    kernel_indx = np.array(range(-l,l+1,1)).reshape((1,-1))

    matrix_size = (2*l)+1
    kernel = np.ones((matrix_size,matrix_size,2),dtype=int)

    #kernel_indx = np.array(range(-5,6,1)).reshape((1,-1))

    for j in range(0,matrix_size):
        vector = kernel[j,:,0].reshape((1,-1))
        kernel[j,:,0]  = np.multiply(vector, kernel_indx)
    for i in range(0,matrix_size):
        vector = kernel[:,i,1].reshape((1,-1))
        kernel[:,i,1]  = np.multiply(vector, kernel_indx)
    
    x = np.array(kernel[:,:,0].flat)
    y = np.array(kernel[:,:,1].flat)

    return(x,y)



def generate_bbox_pixels(x,y,w,h):


    xi = int(x - w/2)
    yi = int(y - h/2)

    xf = int(x + w/2)
    yf = int(y + h/2)

    w_range = np.sign(w)*np.array(range(0,abs(w)),dtype=int)
    h_range =  np.sign(h)*np.array(range(0,abs(h)),dtype=int)

    y_ver = yi + h_range
    x_hor = xi + w_range

    line_vert_left  = (xi*np.ones((len(y_ver)),dtype = int),y_ver)
    line_vert_right = (xf*np.ones((len(y_ver)),dtype = int),y_ver)
    line_hor_buttom = (x_hor,yi*np.ones((len(x_hor)),dtype = int))
    line_hor_top    = (x_hor,yf*np.ones((len(x_hor)),dtype = int))

    x_pixels = np.concatenate((line_vert_left[0],line_vert_right[0],line_hor_buttom[0],line_hor_top[0]))
    y_pixels = np.concatenate((line_vert_left[1],line_vert_right[1],line_hor_buttom[1],line_hor_top[1]))

    return(x_pixels,y_pixels)
    #line_vert_right = (xf*np.ones((len(y_ver)),dtype = int),y_ver)
    #x = ones((len(vertical)))

    # w_range = np.array(range(0,w))
    # h_range = np.array(range(0,h))

    # vertical = x +
