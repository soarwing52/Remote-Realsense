import multiprocessing as mp
import pyrealsense2 as rs
import numpy as np
import cv2
import serial
import datetime
import time
import os, sys
from math import sin, cos, sqrt, atan2, radians


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
    win = ['COM{}'.format(x) for x in range(10)]
    linux = ['/dev/ttbUSB{}'.format(x) for x in range(5)]
    for x in (win + linux):
        serialPort.port = x
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


def min2decimal(in_data):
    """
    transform lon,lat from 00'00" to decimal
    :param in_data: lon / lat
    :return: in decimal poiints
    """
    latgps = float(in_data)
    latdeg = int(latgps / 100)
    latmin = latgps - latdeg * 100
    lat = latdeg + (latmin / 60)
    return lat


def gps_information(port):
    lon, lat = 0, 0
    while lon == 0 or lat == 0:
        line = port.readline()
        data = line.split(b',')
        data = [x.decode("UTF-8") for x in data]
        if data[0] == '$GPRMC':
            if data[2] == "A":
                lat = min2decimal(data[3])
                lon = min2decimal(data[5])
        elif data[0] == '$GPGGA':
            if data[6] == '1':
                lon = min2decimal(data[4])
                lat = min2decimal(data[2])
        time.sleep(1)

    with open('location.csv', 'w') as gps:
        gps.write('Lat,Lon\n')
        gps.write('{},{}'.format(lat, lon))

    return lon, lat


def GPS(Location,gps_on):
    """
    the main function of starting the GPS
    :param Location: mp.Array
    :param gps_on: mp.Value
    :return:
    """
    print('GPS thread start')
    # Set port
    serialPort = serial.Serial()
    serialPort.port = port_check(gps_on) # Check the available ports, return the valid one
    serialPort.baudrate = 4800
    serialPort.bytesize = serial.EIGHTBITS
    serialPort.parity = serial.PARITY_NONE
    serialPort.timeout = 2
    serialPort.open()
    print ('GPS opened successfully')
    gps_on.value = 1
    lon, lat = 0, 0
    try:
        while gps_on.value != 0:
            lon, lat = gps_information(serialPort)
            Location[:] = [lon, lat]
            with open('location.csv', 'w') as gps:
                gps.write('Lat,Lon\n')
                gps.write('{},{}'.format(lat,lon))
        #print(lon, lat)

    except serial.SerialException:
        print ('Error opening GPS')
        gps_on.value = 3
    finally:
        serialPort.close()
        print('GPS finish')


def Camera(child_conn, take_pic, frame_num, camera_status, bag):
    """
    Main camera running
    :param child_conn: source of image, sending to openCV
    :param take_pic: mp.Value, receive True will take one picture, and send back False when done
    :param frame_num: mp.Array, frame number of the picture taken
    :param camera_status: mp.Value, the status of camera
    :param bag: the number of the current recorded file
    :return:
    """
    print('camera start')
    try:
        bag_name = './bag/{}.bag'.format(bag)
        pipeline = rs.pipeline()
        config = rs.config()
        config.enable_stream(rs.stream.depth, 1280, 720, rs.format.z16, 15)
        config.enable_stream(rs.stream.color, 1920, 1080, rs.format.rgb8, 15)
        config.enable_record_to_file(bag_name)
        profile = pipeline.start(config)

        device = profile.get_device() # get record device
        recorder = device.as_recorder()
        recorder.pause() # and pause it

        # set frame queue size to max
        sensor = profile.get_device().query_sensors()
        for x in sensor:
            x.set_option(rs.option.frames_queue_size, 32)
        # set auto exposure but process data first
        color_sensor = profile.get_device().query_sensors()[1]
        color_sensor.set_option(rs.option.auto_exposure_priority, True)
        while camera_status.value != 99:
            frames = pipeline.wait_for_frames()
            child_conn.send(frames)

            if take_pic.value == 1:
                recorder.resume()
                frames = pipeline.wait_for_frames()
                depth_frame = frames.get_depth_frame()
                color_frame = frames.get_color_frame()
                var = rs.frame.get_frame_number(color_frame)
                vard = rs.frame.get_frame_number(depth_frame)
                frame_num[:] = [var, vard]
                time.sleep(0.05)
                recorder.pause()
                take_pic.value = 0

        child_conn.close()
        pipeline.stop()

    except RuntimeError:
        print ('run')

    finally:
        print('pipeline closed')
        camera_status.value = 98


def bag_num():
    """
    Generate the number of record file MMDD001
    :return:
    """
    num = 1
    now = datetime.datetime.now()
    time.sleep(1)

    try:
        while True:
            file_name = '{:02d}{:02d}_{:03d}'.format(now.month, now.day, num)
            bag_name = './bag/{}.bag'.format(file_name)
            exist = os.path.isfile(bag_name)
            if exist:
                num += 1
            else:
                print ('current filename:{}'.format(file_name))
                break
        return file_name
    finally:
        pass


class RScam:
    def __init__(self):
        # Create Folders for Data

        if sys.platform == "linux":
            self.root_dir = '/home/pi/RR/'
        else:
            self.root_dir = './'

        folder_list = ('bag', 'foto_log')

        for folder in folder_list:
            dir_generate(self.root_dir + folder)
        # Create Variables between Processes
        self.Location = mp.Array('d',[0,0])
        self.Frame_num = mp.Array('i',[0,0])

        self.take_pic = mp.Value('i',0)
        self.camera_command = mp.Value('i',0)
        self.gps_status = mp.Value('i',0)

        jpg = cv2.imread('jpg.jpeg')
        self.img = cv2.imencode('.jpg', jpg)[1].tobytes()

    def start_gps(self):
        # Start GPS process
        gps_process = Process(target=GPS, args=(self.Location,self.gps_status,))
        gps_process.start()

    def main_loop(self):
        while self.camera_command.value != 99:
            if self.gps_status.value == 3:
                break
            elif self.gps_status == 1:
                time.sleep(1)
            else:
                parent_conn, child_conn = Pipe()
                bag = bag_num()
                cam_proccess = mp.Process(target=Camera,
                                          args=(child_conn, self.take_pic, self.Frame_num, self.camera_command, bag))
                cam_proccess.start()
                self.command_receiver(parent_conn, bag)

        self.gps_status.value = 0


    def command_receiver(self, parent_conn, bag):
        auto = False
        i = 1
        foto_location = (0, 0)
        foto_frame = self.Frame_num[0]
        while self.camera_command.value != 98:
            (lon, lat) = self.Location[:]
            current_location = (lon, lat)
            present = datetime.datetime.now()
            date = '{},{},{},{}'.format(present.day, present.month, present.year, present.time())
            local_take_pic = False

            frames = parent_conn.recv()
            depth_frame = frames.get_depth_frame()
            color_frame = frames.get_color_frame()
            depth_color_frame = rs.colorizer().colorize(depth_frame)
            depth_image = np.asanyarray(depth_color_frame.get_data())
            color_image = np.asanyarray(color_frame.get_data())
            depth_colormap_resize = cv2.resize(depth_image, (150, 150))
            color_cvt = cv2.cvtColor(color_image, cv2.COLOR_RGB2BGR)
            color_cvt_2 = cv2.resize(color_cvt, (150, 150))
            images = np.vstack((color_cvt_2, depth_colormap_resize))
            self.img = cv2.imencode('.jpg', images)[1].tobytes()

            if self.take_pic.value == 1 or current_location == foto_location:
                continue

            cmd = self.camera_command.value
            if cmd == 11:
                auto = True
                self.camera_command.value = 1
            elif cmd == 12:
                auto = False
                self.camera_command.value = 1
            elif cmd == 3:
                print('take manual')
                local_take_pic = True
                self.camera_command.value = 1

            if auto is True:
                if gps_dis(current_location, foto_location) > 15:
                    local_take_pic = True

            if local_take_pic:
                self.take_pic.value = 1
                time.sleep(0.1)
                (color_frame_num, depth_frame_num) = self.Frame_num[:]
                logmsg = '{},{},{},{},{},{}\n'.format(i, color_frame_num, depth_frame_num, lon, lat, date)
                print('Foto {} gemacht um {:.03},{:.04}'.format(i,lon,lat))
                with open('{}foto_log/{}.txt'.format(self.root_dir, bag), 'a') as logfile:
                    logfile.write(logmsg)
                with open('{}foto_location.csv'.format(self.root_dir), 'a') as record:
                    record.write(logmsg)
                foto_location = (lon, lat)
                i += 1

if __name__ == '__main__':
    pass