import numpy as np
from dxl_control.Ax12 import Ax12
import time
import cv2
from servo_motors import *
from timer_seconds import SecondCounter

#Initiliaze motors
pan_motor = Ax12(1)
tilt_motor = Ax12(2)

#Open port
Ax12.open_port()
Ax12.set_baudrate()

#set starting pos 
pan_motor.set_position(500)
tilt_motor.set_position(200)

time.sleep(2)

#Starts video capturing
cap = cv2.VideoCapture(0)

main_count = SecondCounter()


#Color range for detecting object
carrot_low = np.array([0, 75, 255])
carrot_high = np.array ([27, 205, 255])

cup_low = np.array([12, 76, 229])
cup_high = np.array([75, 238, 255])

green_low = np.array([45 , 100, 50] )
green_high = np.array([75, 255, 255])

#Margin
roi = 20
margin = 50

object_move_pos_strings = []
object_move_pos = []

object_speed = 100

still_moving = True

#Retreive object pos from .txt file.
with open("positions.txt", 'r') as object_pos_file:
    for line in object_pos_file:
        pos = str.split(line)
        object_move_pos_strings.append(pos)
    object_pos_file.close()


 #Convert positions to integers
for element in object_move_pos_strings:
    ints = [int(item) for item in element]
    object_move_pos.append(ints)



#Boolean that turns true when object has finished to move
end_trial = False

next_object_pos = 0

move_trigger = 0

def draw_contours(low_bound, high_bound, image):
    detection = False
    bbox = 0
    hsv_img = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    curr_mask = cv2.inRange(hsv_img, low_bound, high_bound)
    hsv_img[curr_mask > 0] = ([75,255,255])

    cv2.imshow("mask", curr_mask)



    img2, contours, hierarchy =  cv2.findContours(curr_mask,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)



    for cnt in contours:
        area= cv2.contourArea(cnt)
        if area > 800:
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

main_count.start()
while True:
    sucess, frame = cap.read()
    detected , bbox = draw_contours(cup_low, cup_high, frame)
    camera_center = [int(frame.shape[1] / 2), int(frame.shape[0] / 2)]

     #Checks if where still moving positions for the object
    if next_object_pos < len(object_move_pos):
        print(f'objec_move_pos length = {len(object_move_pos)}')
        still_moving = True
    else:
        print("Object moving sequence is finished")
        if still_moving:
            move_finished_time = main_count.peek()
        still_moving = False

    if still_moving:
        move_object_motors(object_move_pos[next_object_pos], speed= object_speed)


    #Mark center of image
    cv2.circle(frame,(camera_center[0], camera_center[1]), 2, (255,0, 250), thickness= 2)

    if detected:
        #Mark center of object
        object_center = goalPosition(bbox)
        cv2.circle(frame,(object_center[0], object_center[1]), 1 , (0,255,0), thickness=1)
        distance, in_roi = calculateDistance(camera_center, object_center)
        print(distance)
        moveMotors(distance[0], distance[1], pan_motor, tilt_motor, roi, margin = margin)

     #moving interval in seconds
    moving_interval = 3
    if still_moving:
        if main_count.peek() > 1 and main_count.peek() < 3:
            move_trigger = main_count.peek()
            next_object_pos =1
        if main_count.peek() > move_trigger:
            move_trigger += moving_interval
            next_object_pos += 1
    else:
        print("Object move coreography is finished")
        if main_count.peek() > move_finished_time + 2:
            end_trial = True

    cv2.imshow("frame", frame)

    

    

    key = cv2.waitKey(10)
    if key == 27 or end_trial:
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


#To get optimal internal state a gradient descent on variational free energy is done





main_count.finish()
Ax12.close_port()
cap.release()
cv2.destroyAllWindows()
