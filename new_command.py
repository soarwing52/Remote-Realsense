import multiprocessing as mp
import pyrealsense2 as rs
import numpy as np
import cv2
import serial
import datetime
import time
import os
from math import sin, cos, sqrt, atan2, radians
from getch import pause_exit


def gps_dis(location_1,location_2):
    """
    this is the calculation of the distance between two long/lat locations
    input tuple/list
    :param location_1: [Lon, Lat]
    :param location_2: [Lon, Lat]
    :return: distance in meter
    """
    R = 6373.0

    lat1 = radians(location_1[1])
    lon1 = radians(location_1[0])
    lat2 = radians(location_2[1])
    lon2 = radians(location_2[0])

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c
    distance = distance*1000
    #print("Result:", distance)
    return distance

def fake_gps(location, frame_num, take_pic ):
    import random
    foto_location = (0,0)
    foto_frame = frame_num[0]
    local_pic = False
    i = 0
    while True:
        lon, lat = random.random(), random.random()
        current_location = [lon, lat]
        location[:] = [lon, lat]

        if take_pic.value == 1:
            continue

        if gps_dis(current_location, foto_location) > 15:
            print('auto take pic')
            local_pic = True

        if local_pic:
            take_pic.value = 1
            (color_frame_num, depth_frame_num) = frame_num[:]
            logmsg = '{},{},{},{},{}\n'.format(i, color_frame_num, depth_frame_num, lon, lat)
            print('Foto {} gemacht um {:.03},{:.04}'.format(i, lon, lat))
            print(logmsg)
            i += 1

        time.sleep(3)

class RScam:
    def __init__(self):
        self.num = '123'

        self.cam = 1
        jpg = cv2.imread('jpg.jpeg')
        self.img = cv2.imencode('.jpg', jpg)[1].tobytes()
        self.location = mp.Array('d', [0, 0])
        self.frame_num = mp.Array('i', [0, 0])
        self.camera_mode = mp.Value('i', 0)
        self.take_pic = mp.Value('i', 0)

    def run_cam(self):
        try:
            print('start camera')
            bag_name = '{}.bag'.format(self.num)
            pipeline = rs.pipeline()
            config = rs.config()
            config.enable_stream(rs.stream.depth, 1280, 720, rs.format.z16, 15)
            config.enable_stream(rs.stream.color, 1920, 1080, rs.format.rgb8, 15)
            config.enable_record_to_file(bag_name)
            profile = pipeline.start(config)

            device = profile.get_device()  # get record device
            recorder = device.as_recorder()
            recorder.pause()

            while True:
                frames = pipeline.wait_for_frames()

                depth_frame = frames.get_depth_frame()
                color_frame = frames.get_color_frame()
                depth_color_frame = rs.colorizer().colorize(depth_frame)
                depth_image = np.asanyarray(depth_color_frame.get_data())
                color_image = np.asanyarray(color_frame.get_data())
                depth_colormap_resize = cv2.resize(depth_image, (150, 150))
                color_cvt = cv2.cvtColor(color_image, cv2.COLOR_RGB2BGR)
                color_cvt_2 = cv2.resize(color_cvt, (150, 150))
                images = np.hstack((color_cvt_2, depth_colormap_resize))

                self.img = cv2.imencode('.jpg', images)[1].tobytes()
                if self.take_pic.value == 1:
                    print('take pic')
                    recorder.resume()
                    frames = pipeline.wait_for_frames()
                    depth_frame = frames.get_depth_frame()
                    color_frame = frames.get_color_frame()
                    var = rs.frame.get_frame_number(color_frame)
                    vard = rs.frame.get_frame_number(depth_frame)
                    self.frame_num[:] = [var, vard]
                    time.sleep(0.5)
                    recorder.pause()
                    self.take_pic.value = 0
                    print("pic taken")

                if self.cam == 0:
                    break

            pipeline.stop()
        finally:
            print('camera stopped')

    def gps_on(self):
        gps_process = mp.Process(target=fake_gps, args=(self.location, self.frame_num, self.take_pic))
        gps_process.start()

    def get_gps(self):
        print(self.location[:])
