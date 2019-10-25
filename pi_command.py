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

def dir_generate(dir_name):
    """
    :param dir_name: input complete path of the desired directory
    :return: None
    """
    dir_name = str(dir_name)
    if not os.path.exists(dir_name):
        try:
            os.mkdir(dir_name)
        finally:
            pass


def port_check(gps_on):
    """
    :param gps_on: when started it is False
    :return: when gps started correctly, return True, if error return 3, which will shut down the program
    """
    serialPort = serial.Serial()
    serialPort.baudrate = 4800
    serialPort.bytesize = serial.EIGHTBITS
    serialPort.parity = serial.PARITY_NONE
    serialPort.timeout = 2
    exist_port = None
    for x in range(0, 5):
        portnum = '/dev/ttyUSB{}'.format(x)
        serialPort.port = portnum
        try:
            serialPort.open()
            serialPort.close()
            exist_port = portnum
        except serial.SerialException:
            pass
        finally:
            pass
    if exist_port:
        return exist_port
    else:
        print ('close other programs using gps or check if the gps is correctly connected')
        gps_on.value = 3
        os._exit(0)

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

def fake_gps(location, status, frame_num, take_pic ):
    import random
    foto_location = (0,0)
    foto_frame = frame_num[0]
    local_pic = False
    i = 0
    status.value = 1
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

def min2decimal(in_data):
    """
    transform lon,lat from 00'00" to decimal
    :param in_data: lon / lat
    :return: in decimal poiints
    """
    try:
        latgps = float(in_data)
        latdeg = int(latgps / 100)
        latmin = latgps - latdeg * 100
        lat = latdeg + (latmin / 60)
    except ValueError:
        print('gps value error')
        lat = 0

    return lat


def gps_information(port):
    lon, lat = 0,0
    while lon == 0 or lat == 0:
        try:
            line = port.readline()
            data = line.split(b',')
            data = [x.decode("utf-8") for x in data]
            if data[0] == '$GPRMC':
                if data[2] == "A":
                    lat = min2decimal(data[3])
                    lon = min2decimal(data[5])
                else:
                    print(data[2:6])
            elif data[0] == '$GPGGA':
                if data[6] == '1':
                    lon = min2decimal(data[4])
                    lat = min2decimal(data[2])
                else:
                    print(data[2:7])
            time.sleep(1)
        except UnicodeDecodeError:
            print('decode error')
        finally:
            pass

    with open('/home/pi/RR/location.csv', 'w') as gps:
        gps.write('Lat,Lon\n')
        gps.write('{},{}'.format(lat, lon))

    return lon, lat


def gps_main(location, gps_status, weg_num, frame_num, camera_command, take_pic, distance):
    """

    :param location:
    :param gps_status:
    :param frame_num:
    :param take_pic:
    :return:
    """
    print('GPS thread start')
    try:
        # Set port
        serialPort = serial.Serial()
        serialPort.port = port_check(gps_status)  # Check the available ports, return the valid one
        serialPort.baudrate = 4800
        serialPort.bytesize = serial.EIGHTBITS
        serialPort.parity = serial.PARITY_NONE
        serialPort.timeout = 2
        serialPort.open()
        print('GPS opened successfully')
        local_pic = False
        foto_location = (0,0)
        i = 1
        gps_status.value = 1
        lon, lat = gps_information(serialPort)
        gps_status.value = 2
        auto = False
        current_weg_num = weg_num.value
        while True:
            lon, lat = gps_information(serialPort)
            current_location = (lon, lat)
            location[:] = [lon,lat]

            print('command' , camera_command.value)
            if camera_command.value == 11:
                auto = True
                camera_command.value = 1
            elif camera_command.value == 12:
                auto = False
                camera_command.value = 1
            elif camera_command.value == 3:
                print('take manual')
                local_pic = True
                camera_command.value = 1
            elif camera_command.value == 99:
                break

            if auto:# and gps_dis(current_location, foto_location) > distance.value:
                #print(gps_dis(current_location, foto_location))
                print('auto take pic')
                local_pic = True

            if camera_command.value != 1 or take_pic.value == 3:# or current_location == foto_location:
                local_pic = False
                print('continue')
                continue

            if current_weg_num != weg_num.value:
                i = 1
                current_weg_num = weg_num.value

            if local_pic:
                local_pic = False
                take_pic.value = 3
                now = datetime.datetime.now()
                date = '{},{},{},{}'.format(now.day, now.month, now.year, now.time())
                (color_frame_num, depth_frame_num) = frame_num[:]
                if color_frame_num == 0:
                    (color_frame_num, depth_frame_num) = frame_num[:]
                logmsg = '{},{},{},{},{},{}\n'.format(i, color_frame_num, depth_frame_num, lon, lat, date)
                print('Foto {} gemacht um {:.03},{:.04}, weg num: {}'.format(i, lon, lat, weg_num.value))
                with open('/home/pi/RR/foto_log/{:02d}{:02d}_{:03d}.txt'.format(now.month, now.day, weg_num.value), 'a') as log:
                    log.write(logmsg)
                i += 1
                foto_location = (lon, lat)


        serialPort.close()
        gps_status.value = 0

    except serial.SerialException:
        print ('Error opening GPS')
        gps_status.value = 3

    finally:
        print('GPS finish')


def bag_num():
    """
    Generate the number of record file MMDD001
    :return:
    """
    num = 1
    now = datetime.datetime.now()

    try:
        while True:
            file_name = '{:02d}{:02d}_{:03d}'.format(now.month, now.day, num)
            bag_name = '/home/pi/RR/bag/{}.bag'.format(file_name)
            exist = os.path.isfile(bag_name)
            if exist:
                num+=1
            else:
                break
        return num
    finally:
        pass


class RScam:
    def __init__(self):
        folder_list = ('/home/pi/RR/bag', '/home/pi/RR/foto_log')
        for folder in folder_list:
            dir_generate(folder)
        self.num = mp.Value('i', bag_num())
        jpg = cv2.imread('/home/pi/RR/jpg.jpeg')
        self.img = cv2.imencode('.jpg', jpg)[1].tobytes()
        self.location = mp.Array('d', [0.0, 0.0])
        self.frame_num = mp.Array('i', [0, 0])
        self.camera_command = mp.Value('i', 0)
        self.take_pic = mp.Value('i', 0)
        self.gps_status = mp.Value('i', 0)
        self.distance = mp.Value('i', 15)

    def camera_loop(self):
        while self.camera_command.value != 99:
            print('camera loop', self.camera_command.value)
            if self.gps_status.value == 1:
                self.num.value = bag_num()
                print("camera loop:", self.num.value)
                self.run_cam()

            elif self.gps_status == 3:
                break
            else:
                time.sleep(1)

        while True:
            if self.gps_status.value == 0:
                self.camera_command.value = 0
                break

    def run_cam(self):
        try:
            now = datetime.datetime.now()
            file_name = '{:02d}{:02d}_{:03d}'.format(now.month, now.day, self.num.value)
            bag_name = '/home/pi/RR/bag/{}.bag'.format(file_name)
            print('start camera with ', bag_name)
            pipeline = rs.pipeline()
            config = rs.config()
            config.enable_stream(rs.stream.depth, 1280, 720, rs.format.z16, 15)
            config.enable_stream(rs.stream.color, 1920, 1080, rs.format.rgb8, 15)
            config.enable_record_to_file(bag_name)
            profile = pipeline.start(config)

            device = profile.get_device()  # get record device
            recorder = device.as_recorder()
            recorder.pause()
            self.camera_command.value = 1
            self.take_pic.value = 1

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
                if self.take_pic.value == 3:
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
                    self.take_pic.value = 1
                    print("pic taken")

                if self.camera_command.value in (2, 99):
                    self.take_pic.value = 1
                    break

            pipeline.stop()
        finally:
            print('camera stopped')

    def gps_on(self):
        gps_process = mp.Process(target=gps_main, args=(self.location, self.gps_status, self.num, self.frame_num,
                                                        self.camera_command, self.take_pic, self.distance))
        gps_process.start()

    def get_gps(self):
        return (self.location[:])


