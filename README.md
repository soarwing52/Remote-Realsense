# Remote-Realsense
creating a webapp controlling raspberry pi4 with D435 camera doing road survey

# Structure
A Flask webapp for tablets to use

and command from webapp to script

** the reason is Flask and pyrealsense both need to run in main thread


Flask app:
the method GET will give:
start/restart/photo/quit, auto mode on/off

the structure is same as my repository https://github.com/soarwing52/RealsensePython

just transferring to wireless control from tablet

When start: the app will start Process GPS, and then thread command reciever, and Process Camera

restart will only restart new thread of command and Process Camera

Foto will can take manual photo

switching on/off auto mode will define if it takes a photo every 15 meters

the droplist can define the distance for frequency

the app link:
http://ai2.appinventor.mit.edu/?galleryId=6709518832107520

Youtube Video:
[![Watch the video](https://github.com/soarwing52/Remote-Realsense/blob/master/img/iphone.JPG)](https://www.youtube.com/watch?v=Hu9xVWWAcd8)
