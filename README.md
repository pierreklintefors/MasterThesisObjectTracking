# MasterThesisObjectTracking

Code for master thesis project in Cognitive Science

Trackers from the Opencv library were evaluated in a non-stationary camera with a robotic arm that moves the object. The experiment can be replicated with 6 Dynamixel Ax12 servo motors and a computer with Ubuntu as operative system.

## Clone the repository to desired folder with git
```
cd *desired directory*

git clone https://github.com/pierreklintefors/MasterThesisObjectTracking.git

cd MasterThesisObjectTracking
```

### It's recomended to create a virtual environment after cloning the repository.
```
python3 -m venv env
```
### Activate environment
```
source env/bin/activate
```
### Install packages listed in requirements.txt
```
python3 -m pip install -r requirements.txt
```
Requires additionally 
Dynamixel control library

https://github.com/cckieu/dxl_control

### Download the caffemodel in order to use GOTURN tracker
https://www.dropbox.com/sh/77frbrkmf9ojfm6/AACgY7-wSfj-LIyYcOgUSZ0Ua?dl=0&preview=goturn.caffemodel

## To run tracker experiment with OpenCV trackers
Before testing the tracker, positions for the robot arm that moves the object need to be recorded using the record_positions.py. Run the script and move the motors to desired positions, press 'a' on the keyboard to record every position. The positions will be saved to a .txt file named positions.txt that will be used in subsequent script.

###Running test
The test can be run with the visual_servoing.py. To access the dynamixel motors root privileges (sudo for Ubuntu) is required
´´´
´´´


## To set up yolov4 tracker (intructions from the original repo: https://github.com/theAIGuysCode/yolov4-deepsort#downloading-official-yolov4-pre-trained-weights)
### Create environement with conda 
```
# Tensorflow CPU
conda env create -f conda-cpu.yml
conda activate yolov4-cpu

# Tensorflow GPU
conda env create -f conda-gpu.yml
conda activate yolov4-gpu
```
### install requirements
```
# TensorFlow CPU
pip install -r requirements.txt

# TensorFlow GPU
pip install -r requirements-gpu.txt

```
### Downloading Official YOLOv4 Pre-trained Weights

Our object tracker uses YOLOv4 to make the object detections, which deep sort then uses to track. There exists an official pre-trained YOLOv4 object detector model that is able to detect 80 classes. For easy demo purposes we will use the pre-trained weights for our tracker. Download pre-trained yolov4.weights file: https://drive.google.com/open?id=1cewMfusmPjYWbrnuJRuKhPMwRe_b9PaT

Copy and paste yolov4.weights from your downloads folder into the 'data' folder of this repository.

If you want to use yolov4-tiny.weights, a smaller model that is faster at running detections but less accurate, download file here: https://github.com/AlexeyAB/darknet/releases/download/darknet_yolo_v4_pre/yolov4-tiny.weights

Running the Tracker with YOLOv4

To implement the object tracking using YOLOv4, first we convert the .weights into the corresponding TensorFlow model which will be saved to a checkpoints folder. Then all we need to do is run the object_tracker.py script to run our object tracker with YOLOv4, DeepSort and TensorFlow.

### Convert darknet weights to tensorflow model
python save_model.py --model yolov4 

### Run yolov4 deep sort object tracker on video
python object_tracker.py --video ./data/video/test.mp4 --output ./outputs/demo.avi --model yolov4

### Run yolov4 deep sort object tracker on webcam (set video flag to 0)
python object_tracker.py --video 0 --output ./outputs/webcam.avi --model yolov4



The output flag allows you to save the resulting video of the object tracker running so that you can view it again later. Video will be saved to the path that you set. (outputs folder is where it will be if you run the above command!)

If you want to run yolov3 set the model flag to --model yolov3, upload the yolov3.weights to the 'data' folder and adjust the weights flag in above commands. (see all the available command line flags and descriptions of them in a below section)
Running the Tracker with YOLOv4-Tiny

The following commands will allow you to run yolov4-tiny model. Yolov4-tiny allows you to obtain a higher speed (FPS) for the tracker at a slight cost to accuracy. Make sure that you have downloaded the tiny weights file and added it to the 'data' folder in order for commands to work!

### save yolov4-tiny model
```
python save_model.py --weights ./data/yolov4-tiny.weights --output ./checkpoints/yolov4-tiny-416 --model yolov4 --tiny
```
### Run yolov4-tiny object tracker (Before running, servomotor sequence for the mover need to be done with record_positions.py
```
python object_tracker.py --weights ./checkpoints/yolov4-tiny-416 --model yolov4 --video ./data/video/test.mp4 --output ./outputs/tiny.avi --tiny
```
