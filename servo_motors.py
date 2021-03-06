from dxl_control.Ax12 import Ax12
import threading
import time


def moveCamMotors(panning, tilt, movement):
    movement_X = movement[0]
    movement_Y = movement[1]
    if movement_X > 2:
        panning.set_position(panning.get_position() + movement_X)
    if movement_Y > 2:
        tilt.set_position(panning.get_position() + movement_Y)


# Function to move motors toward their goal position
def moveMotors(diff_x, diff_y, panning, tiliting, roi, margin):
    camera_panning_motor = panning
    camera_tilt_motor = tiliting
    one_degree = int(1023/300)
    ROI = roi
    close_roi = ROI/2
    big_margin = margin*1.5
    big_movement_X = int(abs(diff_x/20))
    big_movement_Y = int(abs(diff_y/20))
    med_movement_X = int(one_degree*1.5)
    med_movement_Y = int(one_degree*1.5)
    tiny_momvement = 1

    if diff_x > big_margin:
        camera_panning_motor.set_position(camera_panning_motor.get_position() + big_movement_X + 1)
    elif diff_x > margin:
        camera_panning_motor.set_position(camera_panning_motor.get_position() + med_movement_X + 1)
        if diff_x < ROI:
            camera_panning_motor.set_position(camera_panning_motor.get_position() + one_degree + 1)
            if diff_x < close_roi:
                camera_panning_motor.set_position(camera_panning_motor.get_position() + tiny_momvement + 1)
    elif diff_x > ROI:
            camera_panning_motor.set_position(camera_panning_motor.get_position() + one_degree + 1)
            if diff_x < ROI:
                camera_panning_motor.set_position(camera_panning_motor.get_position() + one_degree + 1)
    elif diff_x < 0 - big_margin:
        camera_panning_motor.set_position(camera_panning_motor.get_position() - big_movement_X)
    elif diff_x < 0 - margin:
        camera_panning_motor.set_position(camera_panning_motor.get_position() - med_movement_X)
        if diff_x > 0 - ROI:
            camera_panning_motor.set_position(camera_panning_motor.get_position() - one_degree)
            if diff_x > 0 - close_roi:
                camera_panning_motor.set_position(camera_panning_motor.get_position() - tiny_momvement)
    elif diff_x < 0 - ROI:
            camera_panning_motor.set_position(camera_panning_motor.get_position() - one_degree)
    else:
        camera_panning_motor.set_position(camera_panning_motor.get_position())

    if diff_y > big_margin:
        camera_tilt_motor.set_position(camera_tilt_motor.get_position() + big_movement_Y +2)
    elif diff_y > margin:
        camera_tilt_motor.set_position(camera_tilt_motor.get_position() + med_movement_Y +2)
        if diff_y < ROI:
            camera_tilt_motor.set_position(camera_tilt_motor.get_position() + one_degree +1)
            if diff_y < close_roi:
                camera_tilt_motor.set_position(camera_tilt_motor.get_position() + tiny_momvement +1 )
    elif diff_y > ROI:
            camera_tilt_motor.set_position(camera_tilt_motor.get_position() + one_degree +1 )
            if diff_y < close_roi:
                camera_tilt_motor.set_position(camera_tilt_motor.get_position() + tiny_momvement+ 1)
    elif diff_y < 0-big_margin:
        camera_tilt_motor.set_position(camera_tilt_motor.get_position() - big_movement_Y)
    elif diff_y < 0-margin:
        camera_tilt_motor.set_position(camera_tilt_motor.get_position() - med_movement_Y)
        if diff_y > 0-ROI:
            camera_tilt_motor.set_position(camera_tilt_motor.get_position() - one_degree)
            if diff_y > 0-close_roi:
                camera_tilt_motor.set_position(camera_tilt_motor.get_position() - tiny_momvement)
    elif diff_y < 0-ROI:
            camera_tilt_motor.set_position(camera_tilt_motor.get_position() - one_degree)
            if diff_y > 0-close_roi:
                camera_tilt_motor.set_position(camera_tilt_motor.get_position() - tiny_momvement)
    else:
        camera_tilt_motor.set_position(camera_tilt_motor.get_position())


def move_object_motors(pos = [0,0,0, 0], speed = 100):
    motors = [3,4,5,6]
    for i in motors:
        Ax12(i).set_moving_speed(speed)
    move = True


    if move:
        Ax12(3).set_position(pos[0])
        Ax12(4).set_position(pos[1])
        Ax12(5).set_position(pos[2])
        Ax12(6).set_position(pos[3])

