# python3
import tkinter as tk
from tkinter.ttk import *
from tkinter import *
import requests
from login import extrauser
import numpy as np
import cv2 as cv
from PIL import Image, ImageTk
video = cv.VideoCapture(0, cv.CAP_DSHOW)


video.set(cv.CAP_PROP_FRAME_WIDTH, 300)
video.set(cv.CAP_PROP_FRAME_HEIGHT, 300)

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

    url = "http://192.168.1.36:5000"
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


def do_canny(frame):
    gray = cv.cvtColor(frame, cv.COLOR_RGB2GRAY)
    blur = cv.GaussianBlur(gray, (5, 5), 0)
    canny = cv.Canny(blur, 50, 150)
    return canny

def do_segment(frame):
    height = frame.shape[0]
    polygons = np.array([[(0, height), (800, height), (380, 290)]])
    mask = np.zeros_like(frame)
    cv.fillPoly(mask, polygons, 255)
    segment = cv.bitwise_and(frame, mask)
    return segment

def calculate_lines(frame, lines):
    left = []
    right = []
    
    for line in lines:
        x1, y1, x2, y2 = line.reshape(4)
        parameters = np.polyfit((x1, x2), (y1, y2), 1)
        slope = parameters[0]
        y_intercept = parameters[1]
        
        if slope < 0:
            left.append((slope, y_intercept))
        else:
            right.append((slope, y_intercept))
    
    left_avg = np.average(left, axis=0)
    right_avg = np.average(right, axis=0)
    
    left_line = calculate_coordinates(frame, left_avg)
    right_line = calculate_coordinates(frame, right_avg)
    
    return np.array([left_line, right_line])

def calculate_coordinates(frame, parameters):
    slope, intercept = parameters
    y1 = frame.shape[0]
    y2 = int(y1 - 150)
    x1 = int((y1 - intercept) / slope)
    x2 = int((y2 - intercept) / slope)
    return np.array([x1, y1, x2, y2])

def visualize_lines(frame, lines, reduction_length=50):
    lines_visualize = np.zeros_like(frame)
    
    if lines is not None and len(lines) == 2:
        for line in lines:
            x1, y1, x2, y2 = line
            slope = (y2 - y1) / (x2 - x1) if x2 - x1 != 0 else 0
            intercept = y1 - slope * x1
            shortened_x1 = int(x1 + reduction_length)
            shortened_y1 = int(slope * shortened_x1 + intercept)
            shortened_x2 = int(x2 - reduction_length)
            shortened_y2 = int(slope * shortened_x2 + intercept)
            cv.line(lines_visualize, (shortened_x1, shortened_y1), (shortened_x2, shortened_y2), (0, 255, 0), 5)

        mid_x = (shortened_x1 + shortened_x2) // 2
        mid_y = (shortened_y1 + shortened_y2) // 2

        center_line_length = frame.shape[1] // 2 - mid_x
        cv.line(lines_visualize, (mid_x, mid_y), (mid_x + center_line_length, mid_y), (0, 0, 255), 5)

    return lines_visualize


def extend_line(line, extension_length):
    x1, y1, x2, y2 = line
    # Calculate the slope and intercept of the line
    slope = (y2 - y1) / (x2 - x1)
    intercept = y1 - slope * x1
    # Extend the line by adding/subtracting the extension_length
    extended_x1 = int(x1 - extension_length)
    extended_y1 = int(slope * extended_x1 + intercept)
    extended_x2 = int(x2 + extension_length)
    extended_y2 = int(slope * extended_x2 + intercept)
    return extended_x1, extended_y1, extended_x2, extended_y2


# Create the main Tkinter window


# Create a label widget to display the video feed
label_widget = tk.Label(fen)
label_widget.grid(row=1)

# Create a frame for the video feed
left = tk.Frame(fen, bg="grey", width=200, height=200)
left.pack_propagate(False)
tk.Label(left, text="Line Detection", fg="white", bg="black", anchor="center", justify="center").pack()
left.grid(column=0, row=0, pady=5, padx=10, sticky="n")

# Create a label widget to display the video feed inside the left frame
video_label = tk.Label(left)
video_label.pack()

# The video feed is read in as a VideoCapture object
video_path = r"C:\Users\Ethan\Sprint6\234FinalGUI\input.mp4"
cap = cv.VideoCapture(video_path)


def update_video_feed():
    ret, frame = cap.read()
    if ret:
        canny = do_canny(frame)
        segment = do_segment(canny)
        hough = cv.HoughLinesP(segment, 2, np.pi / 180, 100, np.array([]), minLineLength=100, maxLineGap=50)

        if hough is not None and len(hough) > 0:
            # Averages multiple detected lines from hough into one line for left border of lane and one line for right border of lane
            lines = calculate_lines(frame, hough)
            # Visualizes the lines
            lines_visualize = visualize_lines(frame, lines)
            # Overlays lines on frame by taking their weighted sums and adding an arbitrary scalar value of 1 as the gamma argument
            output = cv.addWeighted(frame, 0.9, lines_visualize, 1, 1)
            # Convert OpenCV image to PIL format
            opencv_image = cv.cvtColor(output, cv.COLOR_BGR2RGBA)
            pil_image = Image.fromarray(opencv_image)
            # Convert PIL image to PhotoImage format
            photo_image = ImageTk.PhotoImage(image=pil_image)
            # Update the label widget with the new image
            video_label.photo_image = photo_image
            video_label.configure(image=photo_image)
        else:
            print("No lines detected. Showing Canny edge detection only.")

        # Schedule the next update after 10 milliseconds
        fen.after(10, update_video_feed)

update_video_feed()

    # Frames are read by intervals of 10 milliseconds. The program breaks out of the while

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

def open_cam():
    _, frame = video.read()
    opencv_image = cv.cvtColor(frame, cv.COLOR_BGR2RGBA)
    captured_image = Image.fromarray(opencv_image)
    photo_image = ImageTk.PhotoImage(image=captured_image)
    label_widget.photo_image = photo_image
    label_widget.configure(image=photo_image)
    label_widget.after(10, open_cam)

open_cam()

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
