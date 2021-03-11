# MasterThesisObjectTracking

Code for master thesis project in Cognitive Science

Trackers from the Opencv library were evaluated in a non-stationary camera using Dynamixel 12ax motors

### It's recomended to create a virtual environment after cloning the repository.
python3 -m venv env

### Activate environment
source env/bin/activate

### Install packages listed in requirements.txt

python3 -m pip install -r requirements.txt

Requires additionally 
Dynamixel control library

https://github.com/cckieu/dxl_control

### Download the caffemodel in order to use GOTURN tracker
https://www.dropbox.com/sh/77frbrkmf9ojfm6/AACgY7-wSfj-LIyYcOgUSZ0Ua?dl=0&preview=goturn.caffemodel
