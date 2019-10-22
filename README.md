# Remote-Realsense
creating a webapp controlling raspberry pi4 with D435 camera

# Structure
A Flask webapp for tablets to use

A script to setup two sockets connecting the webapp

the connection is two sockets for image from script to webapp

and command from webapp to script

** the reason is Flask and pyrealsense both need to run in main thread


Flask app:
the method GET will give:
start/restart/photo/quit, auto mode on/off

the structure is same as my repository https://github.com/soarwing52/RealsensePython

just transferring to wireless control from tablet


