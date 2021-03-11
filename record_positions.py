from dxl_control.Ax12 import *
import keyboard
import os


if os.path.exists('positions.txt'):
    os.remove('positions.txt') #this deletes the file


Ax12.open_port()
Ax12.set_baudrate()

pan = Ax12(3)
tilt1 = Ax12(4)
tilt2 = Ax12(5)



try:

    while True:
        pan.disable_torque()
        tilt1.disable_torque()
        tilt2.disable_torque()

        keyboard.wait("a")
        positions = [pan.get_position(), tilt1.get_position(), tilt1.get_position()]

        txt_file = open("positions.txt", "a")
        txt_file.write("object_move_pos = [{}, {}, {}]\n ".format(str(positions[0]), str(positions[1]), str(positions[2])))




except KeyboardInterrupt:

    print("Pressed Ctrl-C to terminate while statement")

    pass

Ax12.close_port()
