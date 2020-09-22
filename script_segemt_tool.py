# img_viewer.py

import PySimpleGUI as sg
import os.path
from PIL import Image
import cv2

# First the window layout in 2 columns

file_list_column = [
    [
        sg.Text("Label"),
        sg.In(size=(10, 1), enable_events=True, key="-FOLDER-"),
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
    [sg.Button('NEXT',enable_events=True, key="-NEXT-")],
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
  
    window = sg.Window("Image Segmentation Tool", layout)

    label_list = []
    while True:
        event, values = window.read()
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
            # window["-FILE LIST-"].update(fnames)
            img = cv2.imread(imagelist[0])
            imgbytes = cv2.imencode(".png", img)[1].tobytes()
            window["-IMAGE-"].update(data=imgbytes)

        elif event == "-OK-":
            label_name = values["-FOLDER-"]

            label_list.append(label_name)
            try:
                window["-FILE LIST-"].update(label_list)
            except:
                pass

        elif event == "-FILE LIST-":  # A file was chosen from the listbox

            selectedlabel = values["-FILE LIST-"][0]

            try:
                window["-TOUT-"].update(selectedlabel)
                imagename = 'sample/0.jpg'
                window["-IMAGE-"].update(filename=filename)
            except:
                pass
        elif event == "-NEXT-":
            path = values["-NEXT-"]


    window.close()