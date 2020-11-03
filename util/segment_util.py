
import numpy as np


def convert_segm_objs_to_img(h,w,obj_list):

    data = np.zeros((h, w, 1), dtype=np.uint8)

    for objs in obj_list:
        x,y   = objs.get_idx()
        label = objs.get_label()
        data[y,x,0] = label
    return(data)
        
