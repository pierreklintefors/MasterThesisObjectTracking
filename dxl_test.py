from dxl_control.Ax12 import Ax12
import threading
import time



# connecting
Ax12.open_port()
Ax12.set_baudrate()



def user_input():
    """ Check to see if user wants to continue """
    ans = input('Continue? : y/n ')
    if ans == 'n':
        return False
    else:
        return True




def sequence_input(motor):
    current_pos = motor.get_position()
    tor_limit = motor.get_torque_limit()
    print(tor_limit)
    user_input = input("Enter a sequence of position to servomotor (current position is {0}): " .format(current_pos))
    print('\n')
    seq = user_input.split()
    return seq

def moving(motor_object):
    while motor_object.is_moving:
        break


def choose_motor (motor = "1"):
    ans = input("Default motor is 1, to change press 'y' ")
    if ans == 'y':
        motor = input("Which motor should move ")
    return motor

def change_speed(speed = 100):
    ans = input("Default speed is 100, to change press 'y' ")
    if ans == 'y':
        speed = int(input("Input new rotation speed: "))
    return speed

bool_test = True
while bool_test:
    motor = choose_motor()
    motor_object = Ax12(int(motor))
    input_speed = change_speed()
    motor_object.set_moving_speed(input_speed)
    seq = sequence_input(motor_object)
    for mov in seq:
        motor_object.set_position(int(mov))
        if motor_object.is_moving:
            time.sleep(1.3)
    bool_test = user_input()








# disconnect
Ax12.close_port()
