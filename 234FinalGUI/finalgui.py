# python3
import tkinter as tk
from tkinter.ttk import *
from tkinter import *
import requests
from login import extrauser

import cv2
from PIL import Image, ImageTk
video = cv2.VideoCapture(0, cv2.CAP_DSHOW)

video.set(cv2.CAP_PROP_FRAME_WIDTH, 300)
video.set(cv2.CAP_PROP_FRAME_HEIGHT, 300)

from datetime import datetime

fen = tk.Tk()

def update_log_text():
    with open(f"{extrauser}.txt", "r") as file:
        log_content = file.read()
        log_text.config(state=tk.NORMAL)
        log_text.delete("1.0", tk.END)
        log_text.insert(tk.END, log_content)
        log_text.config(state=tk.DISABLED)
        log_text.yview(tk.END)  # scroll down to end!


def movement(direction):
    time = datetime.now()
    current_hour = time.strftime("%H")
    hourint = int(current_hour) - 5
    if hourint < 0:
        hourint = 24 + hourint
    current_time = time.strftime(f"%Y-%m-%d {hourint}:%M:%S %Z%z")

    with open(f'{extrauser}.txt', 'at') as f:
        f.write(f"{extrauser} pressed {direction} at " + current_time + "\n")

    url = "http://192.168.1.25:5000"
    requests.post(url, json={'command': direction})
    
    update_log_text()


def logout():
    fen.destroy()
    time = datetime.now()
    current_hour = time.strftime("%H")
    hourint = int(current_hour) - 5
    if hourint < 0:
        hourint = 24 + hourint
    current_time = time.strftime(f"%Y-%m-%d {hourint}:%M:%S %Z%z")

    with open(f'{extrauser}.txt', 'at') as f:
        f.write(f"{extrauser} has logged out at " + current_time + "\n")

    update_log_text()


# TOP LEFT
left = tk.Frame(fen, bg="grey", width=200, height=200)
left.pack_propagate(False)
tk.Label(left, text="Line  Detection", fg="white", bg="black", anchor="center", justify="center").pack()
left.grid(column=0, row=0, pady=5, padx=10, sticky="n")
sep = Separator(fen, orient="vertical")
sep.grid(column=1, row=0, sticky="ns")

# line
sty = Style(fen)
sty.configure("TSeparator", background="black")

# TOP RIGHT

right = tk.Frame(fen, width=200, height=200, bg="grey")
right.pack_propagate(False)
tk.Label(right, text="Movement Controls", fg="white", bg="black").pack()
right.grid(column=2, row=0, pady=5, padx=10, sticky="n")

forwardbutton = Button(right, text="↑", width=7, command=lambda: movement("forward"))
forwardbutton.grid(row=0, column=2, pady=(30, 3), padx=10, columnspan=2)

leftbutton = Button(right, text="←", width=3, command=lambda: movement("left"))
leftbutton.grid(row=1, column=1, pady=3)

stopbutton = Button(right, text="◉", width=3, command=lambda: movement("stop"))
stopbutton.grid(row=1, column=2, pady=3)

demobutton = Button(right, text="▶", width=3, command=lambda: movement("demo"))
demobutton.grid(row=1, column=3, pady=3)

rightbutton = Button(right, text="→", width=3, command=lambda: movement("right"))
rightbutton.grid(row=1, column=4, pady=3)

backbutton = Button(right, text="↓", width=7, command=lambda: movement("backward"))
backbutton.grid(row=2, column=2, pady=3, columnspan=2)

logoutbutton = Button(right, text="Logout", width=5, command=lambda: logout())
logoutbutton.grid(row=3, column=2, pady=(20, 16), columnspan=2)

# Bottom Left

bleft = tk.Frame(fen, bg="grey", width=200, height=200)

bleft.pack_propagate(False)
tk.Label(bleft, text="Raw Video", fg="white", bg="black", anchor="center", justify="center").pack()
bleft.grid(column=0, row=1, pady=5, padx=10, sticky="n")
sep = Separator(fen, orient="vertical")
sep.grid(column=1, row=1, sticky="ns")

label_widget = Label(bleft)
label_widget.pack()

def open_camera():
    _, frame = video.read()
    opencv_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
    captured_image = Image.fromarray(opencv_image)
    photo_image = ImageTk.PhotoImage(image=captured_image)
    label_widget.photo_image = photo_image
    label_widget.configure(image=photo_image)
    label_widget.after(10, open_camera)

open_camera()

# BOTTOM RIGHT
bright = tk.Frame(fen, bg="grey", width=200, height=200)
bright.pack_propagate(False)
tk.Label(bright, text="Log", fg="white", bg="black").pack()

log_text = tk.Text(bright, fg="white", bg="black", height=10, width=30, wrap=tk.WORD, state=tk.DISABLED)
log_text.grid(column=0, row=2, pady=22, padx=10, sticky="n", rowspan=2)

scrollbar = tk.Scrollbar(bright, command=log_text.yview)

log_text.config(yscrollcommand=scrollbar.set)

bright.grid(column=2, row=1, pady=5, padx=10, sticky="n")

update_log_text()

fen.mainloop()
