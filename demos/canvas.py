


import PySimpleGUI as sg
import matplotlib.pyplot as plt

fig, ax = plt.subplots()

figure_x, figure_y, figure_w, figure_h = fig.bbox.bounds
# define the window layout
layout = [[sg.Text('Plot test')],
            [sg.Canvas(size=(figure_w, figure_h), key='canvas')],
            [sg.OK(pad=((figure_w / 2, 0), 3), size=(4, 2))]]

# create the window and show it without the plot
window = sg.Window('Demo Application - Embedding Matplotlib In PySimpleGUI', layout).Finalize()

# add the plot to the window
fig_photo = draw_figure(window['canvas'].TKCanvas, fig)

# show it all again and get buttons
event, values = window.read()