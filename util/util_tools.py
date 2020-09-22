import os 
from os import listdir



def get_files(folder_path):
    files = [os.path.join(folder_path,f) for f in listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    return(files)