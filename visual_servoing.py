import cv2 as cv
from dxl_control.Ax12 import *
import timer_seconds as timer_sec
import numpy as np
from servo_motors import *
import csv


print(cv.__version__)
# Create class instance of second counter
main_count = timer_sec.SecondCounter()

# Create class instance of second counter when tracker is in ROI
roi_count = timer_sec.Counter_tread()

#Counters fro sec in roi
roi_seconds = 0
returned_roi_seconds = 0

#Booleans for counting time in roi
in_roi = False
been_in_roi = False
first_entry = True
start_count = True
left_roi = False

#Time stope and start for time in roi
roi_seconds_start = 0
roi_seconds_stop = 0


object_move_pos_strings = []
object_move_pos = []

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

roi = 30
margin = 60

object_speed = 100

trackerTypes = ['BOOSTING', 'MIL', 'KCF', 'TLD', 'MEDIANFLOW', 'GOTURN', 'MOSSE', 'CSRT']


def createTrackerByName(trackerType):
    # Create a tracker based on tracker name
    increased_margin = False
    if trackerType == trackerTypes[0]:
        tracker = cv.TrackerBoosting_create()
    elif trackerType == trackerTypes[1]:
        tracker = cv.TrackerMIL_create()
        increased_margin = True
    elif trackerType == trackerTypes[2]:
        tracker = cv.TrackerKCF_create()
    elif trackerType == trackerTypes[3]:
        tracker = cv.TrackerTLD_create()
    elif trackerType == trackerTypes[4]:
        tracker = cv.TrackerMedianFlow_create()
    elif trackerType == trackerTypes[5]:
        tracker = cv.TrackerGOTURN_create()
        increased_margin = True
    elif trackerType == trackerTypes[6]:
        tracker = cv.TrackerMOSSE_create()
    elif trackerType == trackerTypes[7]:
        tracker = cv.TrackerCSRT_create()
        increased_margin = True
    else:
        tracker = None
        print('Incorrect tracker name')
        print('Available trackers are:')
        for t in trackerTypes:
            print(t)

    return tracker, increased_margin


# connecting
Ax12.open_port()
Ax12.set_baudrate()



# Declaring servomotor for camera
camera_panning_motor = Ax12(1)
camera_tilt_motor = Ax12(2)

# Declaring servomotor for object
object_pan1 = Ax12(3)
object_tilt1 = Ax12(4)
object_tilt2 = Ax12(5)
object_pan2 = Ax12(6)



start_pan = 500  # Higer turns left
start_tilt = 180  # Higher turns down

##Lower speed when camera is is moving to start position
# camera_panning_motor.set_moving_speed(80)
# camera_tilt_motor.set_moving_speed(80)

time.sleep(0.2)

# Set start position for camera
camera_panning_motor.set_position(start_pan)
camera_tilt_motor.set_position(start_tilt)

#Set start position for object
move_object_motors(object_move_pos[0], speed= 500)



print("Starting position for pan is: {0} and tilt: {1} \n".format(camera_panning_motor.get_position(),
                                                                  camera_tilt_motor.get_position()))

# Set torque limit
camera_panning_motor.set_torque_limit(1023)
camera_tilt_motor.set_torque_limit(1023)

# Set speed
camera_panning_motor.set_moving_speed(400)
camera_tilt_motor.set_moving_speed(400)

one_degree = int(camera_panning_motor.get_torque_limit() / 300)

# Give the camera time to stabilize before capturing image
time.sleep(2)

# Capture video and create tracker
cap = cv.VideoCapture(0)

trackerType = "KCF"

tracker, increase_margin = createTrackerByName(trackerType)

# Select region to track from grabbed frame
success, frame = cap.read()
bbox = cv.selectROI("Tracking", frame, False)
tracker.init(frame, bbox)

track_lost = False
refound = 0



# Draw box of ROI functrion
def drawBox(frame, bbox):
    x, y, w, h = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])
    cv.rectangle(frame, (x, y), ((x + w), (y + h)), (255, 0, 255), 3, 1)
    cv.putText(frame, "Tracking", (75, 75), cv.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)


# Function that returns center of ROI
def goalPosition(bbox):
    x, y, w, h = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])
    center_x = int(x + w / 2)
    center_y = int(y + h / 2)
    center = [center_x, center_y]
    return center


# Function that calculates distance between center of frame and center of ROI
def calculateDistance(cam_center, track_center):
    ROI = False
    x_diff = cam_center[0] - track_center[0]
    y_diff = cam_center[1] - track_center[1]
    difference = [x_diff, y_diff]

    if abs(x_diff) <= roi and abs(y_diff) <= roi:
        ROI = True
    return difference, ROI


# define video codec
fourcc = cv.VideoWriter_fourcc(*'mp4v')



#Count for frames
framecount= 0

#Count for iterating in object position list
next_object_pos = 0

import os
import shutil




output_folder = "{}_output".format(trackerType)



output_dir = "{}/{}".format(os.getcwd(), output_folder)

if os.path.exists(output_dir):
    shutil.rmtree(output_dir)
os.makedirs(output_dir)

frames_dir = "{}/frames".format(output_dir)
text_dir = "{}/txt_files".format(output_dir)
video_dir = "{}/video".format(output_dir)
os.makedirs(frames_dir)
os.makedirs(text_dir)
os.makedirs(video_dir)

# Create output
videOutput = cv.VideoWriter("{}/output.mp4".format(video_dir), fourcc, 30, (frame.shape[1], frame.shape[0]))
videoOutput_no_box = cv.VideoWriter("{}/output_no_graphics.mp4".format(video_dir), fourcc, 30, (frame.shape[1], frame.shape[0]))


move_trigger = 0

# start the main count of seconds
main_count.start()
while True:
    timer = cv.getTickCount()
    success, frame = cap.read()
    framecount += 1
    
    #Checks if where still moving positions for the object
    if next_object_pos < len(object_move_pos):
        print(f'object_move_pos length = {len(object_move_pos)}')
        print(f'next pos = {object_move_pos[next_object_pos]}')
        still_moving = True
    else:
        print("Object moving sequence is finished")
        if still_moving:
            move_finished_time = main_count.peek()
        still_moving = False
        

    videoOutput_no_box.write(frame)

    cv.imwrite("{}/frame_{}.jpg".format(frames_dir,framecount), frame)

    if still_moving:
        move_object_motors(object_move_pos[next_object_pos], speed= object_speed)

    tracksuccess, bbox = tracker.update(frame)

    if tracksuccess:
        drawBox(frame, bbox)
        center = goalPosition(bbox)
        cv.circle(frame, (center[0], center[1]), radius=0, color=(255, 0, 255), thickness=10)
        #Generate text file to store for bouding box coordinates
        bbox_file = open("{}/bbox.txt".format(text_dir), "a")
        bbox_file.write("{}, {}, {}, {}\n".format(bbox[0], bbox[1], bbox[2], bbox[3]))
        bbox_file.close()
        if track_lost:
            refound +=1
            track_lost =False
    else:
        cv.putText(frame, "Tracking lost", (75, 75), cv.FONT_HERSHEY_COMPLEX, 1, (0, 0, 255), 2)
        bbox_file = open("{}/bbox.txt".format(text_dir), "a")
        bbox_file.write("0, 0, 0, 0 \n")
        bbox_file.close()
        track_lost = True


    fps = round(cv.getTickFrequency() / (cv.getTickCount() - timer), 2)
    cv.putText(frame, "FPS {0}".format(str(int(fps))), (75, 50), cv.FONT_HERSHEY_COMPLEX, 1, (0, 0, 255), 2)

    camera_center = [int(frame.shape[1] / 2), int(frame.shape[0] / 2)]
    cv.circle(frame, (camera_center[0], camera_center[1]), radius=1, color=(0, 255, 0), thickness=10)


    distance, in_roi = calculateDistance(camera_center, center)

    #Generate text file to store distance difference
    distance_file = open("{}/distance.txt".format(text_dir), "a")
    distance_file.write("{}, {}\n".format(distance[0], distance[1]))
    distance_file.close()

    if tracksuccess:
        last_move_time = main_count.peek()
        last_move_dist = distance
        if increase_margin:
            margin = margin*1.2
         #                               bbox)  # difference in x-cordinates respectively y-cordinates
        #else:
         #  moveMotors(distance[0], distance[1], camera_panning_motor, camera_tilt_motor, roi, margin)  # difference in x-cordinates rescpeticly y-cordinates
        moveMotors(distance[0], distance[1], camera_panning_motor, camera_tilt_motor, roi, margin)
    
    #moving interval in seconds
    moving_interval = 3
    if still_moving:
        if main_count.peek() > 1 and main_count.peek() < 3:
            move_trigger = main_count.peek()
        elif main_count.peek() > move_trigger + 0.02:
            move_trigger += moving_interval
            next_object_pos += 1
    else:
        print("Object move coreography is finished")
        if main_count.peek() > move_finished_time + 2:
            end_trial = True

    ##Sarts timer when the ROI is centered
    if in_roi and tracksuccess:
        if start_count:
            roi_count.start()
            start_count = False
        if first_entry:
            roi_seconds = roi_count.peek()
        if left_roi:
            roi_seconds_start = roi_count.peek()
        been_in_roi = True
        left_roi = False

    ##Stops timer when ROI is not centered and accumulate time in counter
    if been_in_roi and tracksuccess and in_roi is False :
        print("roi_stop: {}".format(roi_seconds_stop))
        if first_entry:
            roi_seconds_stop = 0
        else:
            roi_seconds_stop = roi_count.peek() - roi_seconds_start
        roi_seconds += roi_seconds_stop
        been_in_roi = False
        first_entry = False
        left_roi = True


    print(distance)




    cv.putText(frame, "Sec {0}".format(str(int(main_count.peek()))), (500, 50), cv.FONT_HERSHEY_COMPLEX, 1,
               (0, 255, 255), 2)
    cv.putText(frame, "Sec in ROI {0}".format(str(int(roi_seconds))), (400, 85), cv.FONT_HERSHEY_COMPLEX, 1,
               (254, 0, 255), 2)

    cv.imshow("Frame", frame)

    videOutput.write(frame)


    mean_roi_sec = round((roi_seconds / main_count.peek()) * 100, 2)

    camera_pos = [camera_panning_motor.get_position(), camera_tilt_motor.get_position()]
    object_pos = [object_pan1.get_position(), object_tilt1.get_position(), object_tilt2.get_position(), object_pan2.get_position() ]
    #Create a csv to store results
    with open('{}/output.csv'.format(output_folder), 'a', newline='') as csvfile:
        fieldnames = ['Frame', 'FPS', 'Distance_x', 'Distance_y', 'bbox_xmin', 'bbox_ymin', 'bbox_xmax', 'bbox_ymax',
                      'Prop_roi(%)', 'Time', 'Roi_time', 'Tracking_success', 'Refound_tracking', 'camera_pan',
                      'camera_tilt', 'object_pan1', 'object_tilt1', 'object_tilt2', 'object_pan2']
        csv_writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        #Fill in values in csv file
        if framecount ==1:
            csv_writer.writeheader()
        csv_writer.writerow({'Frame': str(framecount), 'FPS': str(fps) ,'Distance_x': str(distance[0]), 'Distance_y': str(distance[1]),
                             'bbox_xmin': str(bbox[0]), 'bbox_ymin': str(bbox[1]), 'bbox_xmax': str(int(bbox[0] + bbox[2])),
                             'bbox_ymax': str(int(bbox[1] + bbox[3])), 'Prop_roi(%)': str(mean_roi_sec), 'Time': str(round(main_count.peek(), 2)),
                            'Roi_time': str(round(roi_seconds,2)), 'Tracking_success': str(tracksuccess),
                             'Refound_tracking': str(refound), 'camera_pan': str(camera_pos[0]),
                            'camera_tilt':str(camera_pos[1]), 'object_pan1':str(object_pos[0]),
                             'object_tilt1':str(object_pos[1]), 'object_tilt2':str(object_pos[2]),
                             'object_pan2':str(object_pos[3])})





    key = cv.waitKey(10)
    if key == 27 or end_trial:
        print("Ending program")
        break

cap.release()
videOutput.release()
videoOutput_no_box.release()
cv.destroyAllWindows()



# stop the count and get elapsed time
main_seconds = main_count.finish()
roi_count.finish()
print("Program ran for {} seconds".format(round(main_seconds, 2)))

print("Time spent in ROI: {} seconds".format(round(roi_seconds,2 )))

print("Proportion time when ROI was centered: {}%".format(round((roi_seconds / main_seconds) * 100, 2)))
# disconnect
camera_panning_motor.disable_torque()
camera_tilt_motor.disable_torque()
Ax12.close_port()


