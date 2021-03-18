from dxl_control.Ax12 import *
import os
import cv2
import keyboard

if os.path.exists('positions.txt'):
    os.remove('positions.txt') #this deletes the file


Ax12.open_port()
Ax12.set_baudrate()

pan = Ax12(3)
tilt1 = Ax12(4)
tilt2 = Ax12(5)
pan2 = Ax12(6)

motors = [pan, tilt1, tilt2, pan2]


stored_pos = []


pan.disable_torque()
tilt1.disable_torque()
tilt2.disable_torque()
pan2.disable_torque()

first_line = True

while True:
    keyboard.wait('a')
    positions = [pan.get_position(), tilt1.get_position(), tilt2.get_position(), pan2.get_position()]
    stored_pos.append(positions)
    txt_file = open("positions.txt", "a")
    if first_line:
        txt_file.write("{} {} {} {}".format(str(positions[0]), str(positions[1]), str(positions[2]),str(positions[3])))
        first_line = False
    txt_file.write("\n{} {} {} {}".format(str(positions[0]), str(positions[1]), str(positions[2]),str(positions[3])))
    print("{} {} {} {} ".format(str(positions[0]), str(positions[1]), str(positions[2]),str(positions[3])))

Ax12.close_port()
    
 


