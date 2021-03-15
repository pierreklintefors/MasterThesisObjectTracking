import os
# comment out below line to enable tensorflow logging outputs
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
import time
import tensorflow as tf
physical_devices = tf.config.experimental.list_physical_devices('GPU')
if len(physical_devices) > 0:
    tf.config.experimental.set_memory_growth(physical_devices[0], True)
from absl import app, flags, logging
from absl.flags import FLAGS
import core.utils as utils
from core.yolov4 import filter_boxes
from tensorflow.python.saved_model import tag_constants
from core.config import cfg
from PIL import Image
import cv2
import numpy as np
import matplotlib.pyplot as plt
from tensorflow.compat.v1 import ConfigProto
from tensorflow.compat.v1 import InteractiveSession
# deep sort imports
from deep_sort import preprocessing, nn_matching
from deep_sort.detection import Detection
from deep_sort.tracker import Tracker
from tools import generate_detections as gdet

#Dynamixel imports
from dxl_control.Ax12 import *

#servo motors imports
from servo_motors import *

import timer_seconds as timer_sec

import csv


flags.DEFINE_string('framework', 'tf', '(tf, tflite, trt')
flags.DEFINE_string('weights', './checkpoints/yolov4-416',
                    'path to weights file')
flags.DEFINE_integer('size', 416, 'resize images to')
flags.DEFINE_boolean('tiny', False, 'yolo or yolo-tiny')
flags.DEFINE_string('model', 'yolov4', 'yolov3 or yolov4')
flags.DEFINE_string('video', './data/video/test.mp4', 'path to input video or set to 0 for webcam')
flags.DEFINE_string('output', None, 'path to output video')
flags.DEFINE_string('output_format', 'XVID', 'codec used in VideoWriter when saving video to file')
flags.DEFINE_float('iou', 0.45, 'iou threshold')
flags.DEFINE_float('score', 0.50, 'score threshold')
flags.DEFINE_boolean('dont_show', False, 'dont show video output')
flags.DEFINE_boolean('info', False, 'show detailed info of tracked objects')
flags.DEFINE_boolean('count', False, 'count objects being tracked on screen')

def main(_argv):
    # Definition of the parameters
    max_cosine_distance = 0.4
    nn_budget = None
    nms_max_overlap = 1.0
    
    # initialize deep sort
    model_filename = 'model_data/mars-small128.pb'
    encoder = gdet.create_box_encoder(model_filename, batch_size=1)
    # calculate cosine distance metric
    metric = nn_matching.NearestNeighborDistanceMetric("cosine", max_cosine_distance, nn_budget)
    # initialize tracker
    tracker = Tracker(metric)

    # load configuration for object detector
    config = ConfigProto()
    config.gpu_options.allow_growth = True
    session = InteractiveSession(config=config)
    STRIDES, ANCHORS, NUM_CLASS, XYSCALE = utils.load_config(FLAGS)
    input_size = FLAGS.size
    video_path = FLAGS.video

    # load tflite model if flag is set
    if FLAGS.framework == 'tflite':
        interpreter = tf.lite.Interpreter(model_path=FLAGS.weights)
        interpreter.allocate_tensors()
        input_details = interpreter.get_input_details()
        output_details = interpreter.get_output_details()
        print(input_details)
        print(output_details)
    # otherwise load standard tensorflow saved model
    else:
        saved_model_loaded = tf.saved_model.load(FLAGS.weights, tags=[tag_constants.SERVING])
        infer = saved_model_loaded.signatures['serving_default']

    #Dynmixel setup
    # connecting
    Ax12.open_port()
    Ax12.set_baudrate()

    #Declaring servomotor for pan and tilt
    camera_panning_motor = Ax12(1)
    camera_tilt_motor = Ax12(2)

    start_pan = 500
    start_tilt = 180

    # define video codec
    fourcc = cv2.VideoWriter_fourcc(*'XVID')


    bound_box = [0,0,0,0]

    frames_per_second = 0


    time.sleep(0.2)

    #Set start position
    camera_panning_motor.set_position(start_pan)
    camera_tilt_motor.set_position(start_tilt)

    camera_panning_motor.set_torque_limit(1023)
    camera_tilt_motor.set_torque_limit(1023)

    camera_panning_motor.set_moving_speed(1000)
    camera_tilt_motor.set_moving_speed(1000)

    one_degree = int(camera_panning_motor.get_torque_limit()/300)

    # Create class instance of second counter
    main_count = timer_sec.SecondCounter()

    # Create class instance of second counter when tracker is in ROI
    roi_count = timer_sec.Counter_tread()

    roi_seconds = 0

    returned_roi_seconds = 0

    in_roi = False
    been_in_roi = False
    first_entry = True
    start_count = True
    left_roi = False
    roi_seconds_start = 0
    roi_seconds_stop = 0

    last_move_time = 0


    roi = 35
    margin = 70

    tracksuccess = False
    track_lost = False
    refound = 0

    first_detection = True


    #Start position for object mover servos
    object_move_pos = [500, 200, 822, 200]

    object_speed = 100

    #Function that returns center of ROI
    def goalPosition (bbox):
        x, y = int(bbox[0]), int(bbox[1])
        w = int(bbox[2]) - int(bbox[0])  
        h = int(bbox[3]) - int(bbox[1])
        center_x = int(x + w/2)
        center_y = int(y + h/2)
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


    # begin video capture
    try:
        vid = cv2.VideoCapture(int(video_path))
    except:
        vid = cv2.VideoCapture(video_path)

    out = None

    # get video ready to save locally if flag is set
    if FLAGS.output:
        # by default VideoCapture returns float instead of int
        width = int(vid.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(vid.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(vid.get(cv2.CAP_PROP_FPS))
        codec = cv2.VideoWriter_fourcc(*FLAGS.output_format)
        out = cv2.VideoWriter(FLAGS.output, codec, fps, (width, height))


    import os
    import shutil




    output_dir = "{}/outputs".format(os.getcwd())

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
    return_value, frame = vid.read()
    videOutput = cv2.VideoWriter("{}/output.avi".format(video_dir), fourcc, 30, (frame.shape[1], frame.shape[0]))
    videoOutput_no_box = cv2.VideoWriter("{}/output_no_graphics.avi".format(video_dir), fourcc, 30, (frame.shape[1], frame.shape[0]))

    frame_num = 0
    # start the main count of seconds
    main_count.start()
    # while video is running
    while True:
        return_value, frame = vid.read()
        if return_value:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image = Image.fromarray(frame)
        else:
            print('Video has ended or failed, try a different video format!')
            break
        frame_num +=1
        print('Frame #: ', frame_num)
        frame_size = frame.shape[:2]
        image_data = cv2.resize(frame, (input_size, input_size))
        image_data = image_data / 255.
        image_data = image_data[np.newaxis, ...].astype(np.float32)
        start_time = time.time()

        no_graphics = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        videoOutput_no_box.write(no_graphics)

        cv2.imwrite("{}/frame_{}.jpg".format(frames_dir,frame_num), no_graphics)


        #Move object servos
        move_object_motors(object_move_pos, speed= object_speed)

        # run detections on tflite if flag is set
        if FLAGS.framework == 'tflite':
            interpreter.set_tensor(input_details[0]['index'], image_data)
            interpreter.invoke()
            pred = [interpreter.get_tensor(output_details[i]['index']) for i in range(len(output_details))]
            # run detections using yolov3 if flag is set
            if FLAGS.model == 'yolov3' and FLAGS.tiny == True:
                boxes, pred_conf = filter_boxes(pred[1], pred[0], score_threshold=0.25,
                                                input_shape=tf.constant([input_size, input_size]))
            else:
                boxes, pred_conf = filter_boxes(pred[0], pred[1], score_threshold=0.25,
                                                input_shape=tf.constant([input_size, input_size]))
        else:
            batch_data = tf.constant(image_data)
            pred_bbox = infer(batch_data)
            for key, value in pred_bbox.items():
                boxes = value[:, :, 0:4]
                pred_conf = value[:, :, 4:]

        boxes, scores, classes, valid_detections = tf.image.combined_non_max_suppression(
            boxes=tf.reshape(boxes, (tf.shape(boxes)[0], -1, 1, 4)),
            scores=tf.reshape(
                pred_conf, (tf.shape(pred_conf)[0], -1, tf.shape(pred_conf)[-1])),
            max_output_size_per_class=50,
            max_total_size=50,
            iou_threshold=FLAGS.iou,
            score_threshold=FLAGS.score
        )

        # convert data to numpy arrays and slice out unused elements
        num_objects = valid_detections.numpy()[0]
        bboxes = boxes.numpy()[0]
        bboxes = bboxes[0:int(num_objects)]
        scores = scores.numpy()[0]
        scores = scores[0:int(num_objects)]
        classes = classes.numpy()[0]
        classes = classes[0:int(num_objects)]

        # format bounding boxes from normalized ymin, xmin, ymax, xmax ---> xmin, ymin, width, height
        original_h, original_w, _ = frame.shape
        bboxes = utils.format_boxes(bboxes, original_h, original_w)

        # store all predictions in one parameter for simplicity when calling functions
        pred_bbox = [bboxes, scores, classes, num_objects]

        # read in all class names from config
        class_names = utils.read_class_names(cfg.YOLO.CLASSES)

        # by default allow all classes in .names file
        #allowed_classes = list(class_names.values())
        
        # custom allowed classes (uncomment line below to customize tracker for only people)
        allowed_classes = ['cell phone', 'cup']

        # loop through objects and use class index to get class name, allow only classes in allowed_classes list
        names = []
        deleted_indx = []
        for i in range(num_objects):
            class_indx = int(classes[i])
            class_name = class_names[class_indx]
            if class_name not in allowed_classes:
                deleted_indx.append(i)
            else:
                names.append(class_name)
        names = np.array(names)
        count = len(names)
        if FLAGS.count:
            cv2.putText(frame, "Objects being tracked: {}".format(count), (5, 35), cv2.FONT_HERSHEY_COMPLEX_SMALL, 2, (0, 255, 0), 2)
            print("Objects being tracked: {}".format(count))
        # delete detections that are not in allowed_classes
        bboxes = np.delete(bboxes, deleted_indx, axis=0)
        scores = np.delete(scores, deleted_indx, axis=0)

        # encode yolo detections and feed to tracker
        features = encoder(frame, bboxes)
        detections = [Detection(bbox, score, class_name, feature) for bbox, score, class_name, feature in zip(bboxes, scores, names, features)]

        #initialize color map
        cmap = plt.get_cmap('tab20b')
        colors = [cmap(i)[:3] for i in np.linspace(0, 1, 20)]

        # run non-maxima supression
        boxs = np.array([d.tlwh for d in detections])
        scores = np.array([d.confidence for d in detections])
        classes = np.array([d.class_name for d in detections])
        indices = preprocessing.non_max_suppression(boxs, classes, nms_max_overlap, scores)
        detections = [detections[i] for i in indices]       

        # Call the tracker
        tracker.predict()
        tracker.update(detections)

        #Drawing a circle in the center of the frame
        camera_center = [int(frame.shape[1]/2), int(frame.shape[0]/2)]
        cv2.circle(frame, (camera_center[0], camera_center[1]), radius= 1, color= (0, 255, 0), thickness= 10)


        distance = [0,0]
        # update tracks
        for track in tracker.tracks:
            if not track.is_confirmed() or track.time_since_update > 1:
                track_lost = True
                tracksuccess = False
                bound_box = [0, 0, 0, 0]
                continue 
            bbox = track.to_tlbr()
            class_name = track.get_class()



            tracksuccess = True
            track_lost = False

            first_detection = False
            # draw bbox on screen
            color = colors[int(track.track_id) % len(colors)]
            color = [i * 255 for i in color]
            cv2.rectangle(frame, (int(bbox[0]), int(bbox[1])), (int(bbox[2]), int(bbox[3])), color, 2)
            cv2.rectangle(frame, (int(bbox[0]), int(bbox[1]-30)), (int(bbox[0])+(len(class_name)+len(str(track.track_id)))*17, int(bbox[1])), color, -1)
            cv2.putText(frame, class_name + "-" + str(track.track_id),(int(bbox[0]), int(bbox[1]-10)),0, 0.75, (255,255,255),2)
            
            #Calulate center of bounding box and draw circle
            center = goalPosition(bbox)
            cv2.circle(frame, (center[0], center[1]), radius =0, color= color, thickness=10)



            print("Bbox: {0}" .format(bbox))

            #Storing value for the output.csv file
            bound_box = bbox


            distance, in_roi = calculateDistance(camera_center, center)

            moveMotors(distance[0], distance[1], camera_panning_motor, camera_tilt_motor, roi, margin) #difference in x-cordinates rescpeticly y-cordinates

            

        # if enable info flag then print details about each track
            if FLAGS.info:
                print("Tracker ID: {}, Class: {},  BBox Coords (xmin, ymin, xmax, ymax): {}".format(str(track.track_id), class_name, (int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3]))))


        # calculate frames per second of running detections
        fps = 1.0 / (time.time() - start_time)
        print("FPS: %.2f" % fps)

        frames_per_second = fps

        #Fps text
        cv2.putText(frame, "FPS {0}".format(str(int(fps))), (75, 50), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 255), 2)
        result = np.asarray(frame)
        result = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        if main_count.peek() > 1 and main_count.peek() < 3:
            object_move_pos = [500, 300, 850, 200 ]
        if main_count.peek() > 3 and main_count.peek() < 5:
            object_move_pos = [600, 500, 600, 2500]
        if main_count.peek() > 8.5 and main_count.peek() < 8:
            object_speed = 100
            object_move_pos = [700, 450, 500, 200]
        if main_count.peek() > 8.5 and main_count.peek() < 10:
            object_speed = 150
            object_move_pos = [800, 450, 500, 250]
        if main_count.peek() > 8.5 and main_count.peek() < 12:
            object_move_pos = [600, 450, 500, 250]
        if main_count.peek() > 12 and main_count.peek() < 14:
            object_move_pos = [500, 200, 820, 239]

        ##Starts timer when the ROI is centered
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


       




        cv2.putText(result, "Sec {0}".format(str(int(main_count.peek()))), (500, 50), cv2.FONT_HERSHEY_COMPLEX, 1,
                (0, 255, 255), 2)
        cv2.putText(result, "Sec in ROI {0}".format(str(int(roi_seconds))), (400, 85), cv2.FONT_HERSHEY_COMPLEX, 1,
                (254, 0, 255), 2)

        #cv2.imshow("Frame", frame)

        videOutput.write(result)

        mean_roi_sec = round((roi_seconds / main_count.peek()) * 100, 2)

        camera_pos = [camera_panning_motor.get_position(), camera_tilt_motor.get_position()]

        object_pos = [Ax12(3).get_position(),Ax12(4).get_position(),Ax12(5).get_position(),Ax12(6).get_position()]



        #Create a csv to store results
        with open('outputs/output.csv', 'a', newline='') as csvfile:
            fieldnames = ['Frame', 'FPS', 'Distance_x', 'Distance_y', 'bbox_xmin', 'bbox_ymin', 'bbox_xmax', 'bbox_ymax',
                        'Prop_roi(%)', 'Time', 'Roi_time', 'Tracking_success', 'Refound_tracking', 'camera_pan',
                        'camera_tilt', 'object_pan1', 'object_tilt1', 'object_tilt2', 'object_pan2']
            csv_writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            #Fill in values in csv file
            if frame_num ==1:
                csv_writer.writeheader()
            csv_writer.writerow({'Frame': str(frame_num), 'FPS': str(int(frames_per_second)) ,'Distance_x': str(distance[0]), 'Distance_y': str(distance[1]),
                                'bbox_xmin': str(int(bound_box[0])), 'bbox_ymin': str(int(bound_box[1])), 'bbox_xmax': str(int(bound_box[2])),
                                'bbox_ymax': str(int(bound_box[3])), 'Prop_roi(%)': str(mean_roi_sec), 'Time': str(round(main_count.peek(), 2)),
                                'Roi_time': str(round(roi_seconds,2)), 'Tracking_success': str(tracksuccess),
                                'Refound_tracking': str(refound), 'camera_pan': str(camera_pos[0]),
                                'camera_tilt':str(camera_pos[1]), 'object_pan1':str(object_pos[0]),
                                'object_tilt1':str(object_pos[1]), 'object_tilt2':str(object_pos[2]),
                                'object_pan2':str(object_pos[3])})


        
        
        if not FLAGS.dont_show:
            cv2.imshow("Output Video", result)
        
        
        
        # if output flag is set, save video file
        if FLAGS.output:
            out.write(result)
        if cv2.waitKey(1) & 0xFF == ord('q'): break
    cv2.destroyAllWindows()
    videOutput.release()
    videoOutput_no_box.release()
    Ax12.close_port()
    # stop the count and get elapsed time
    main_seconds = main_count.finish()
    roi_count.finish()


if __name__ == '__main__':
    try:
        app.run(main)
    except SystemExit:
        pass
