import os 
from os import listdir



def get_files(folder_path):
    files = [os.path.join(folder_path,f) for f in listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    return(files)


def get_key(my_dict,val): 
    for key, value in my_dict.items(): 
         if val == value: 
             return key 

def create_folder(name):
        
    try:
        os.makedirs(name)
    except OSError:
        print ("Creation of the directory %s failed" % name)
    else:
        print ("Successfully created the directory %s " % name)
