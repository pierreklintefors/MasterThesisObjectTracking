import numpy as np
from dxl_control.Ax12 import Ax12
import time
import cv2

#Initiliaze motors
pan_motor = Ax12(1)
tilt_motor = Ax12(2)

#Open port
Ax12.open_port()
Ax12.set_baudrate()

#Starts video capturing
cap = cv2.VideoCapture(0)


#Color range for detecting object
orange_low = np.array([0, 75, 255])
orange_high = np.array ([27, 205, 255])

green_low = np.array([45 , 100, 50] )
green_high = np.array([75, 255, 255])

roi = 20

def draw_contours(low_bound, high_bound, image):
    detection = False
    bbox = 0
    hsv_img = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    curr_mask = cv2.inRange(hsv_img, low_bound, high_bound)
    hsv_img[curr_mask > 0] = ([75,255,200])

    cv2.imshow("mask", curr_mask)



    img2, contours, hierarchy =  cv2.findContours(curr_mask,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)



    for cnt in contours:
        area= cv2.contourArea(cnt)
        if area > 500:
            (x, y, w, h) = cv2.boundingRect(cnt)
            cv2.rectangle(image, (x,y), (x+w, y+h), (0, 255, 0 ))
            bbox = [x, y, w, h]
            detection = True
    return detection, bbox



# Function that returns center of bbox
def goalPosition(bbox):
    x, y, w, h = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])
    center_x = int(x + w / 2)
    center_y = int(y + h / 2)
    center = [center_x, center_y]
    return center


# Function that caluculates distance between center of frame and center of ROI
def calculateDistance(cam_center, track_center):
    ROI = False
    x_diff = cam_center[0] - track_center[0]
    y_diff = cam_center[1] - track_center[1]
    difference = [x_diff, y_diff]
    if abs(x_diff) <= roi and abs(y_diff) <= roi:
        ROI = True
    return difference, ROI

while True:
    sucess, frame = cap.read()


    detected , bbox = draw_contours(orange_low, orange_high, frame)

    camera_center = [int(frame.shape[1] / 2), int(frame.shape[0] / 2)]


    #Mark center of image
    cv2.circle(frame,(camera_center[0], camera_center[1]), 2, (255,0, 250), thickness= 2)

    if detected:
        #Mark center of object
        object_center = goalPosition(bbox)
        cv2.circle(frame,(object_center[0], object_center[1]), 1 , (0,255,0), thickness=1)

    cv2.imshow("frame", frame)

    key = cv2.waitKey(10)
    if key == 27:
        break







def get_internal_state(pan, tilt):
    pan_pos = pan.get_position()
    tilt_pos = tilt.get_position()
    internal_state = np.array([pan_pos, tilt_pos])
    return internal_state

##
q_s = np.random.normal()

def partial_derivative():
    pass

internal_state = get_internal_state(pan_motor, tilt_motor)

#To get optimal internal state a gradient descent on variational free energy is done




