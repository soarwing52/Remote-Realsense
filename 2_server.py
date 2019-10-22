import socket
import multiprocessing as mp
import pickle
import struct
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
    for x in range(1, 10):
        portnum = 'COM{}'.format(x)
        serialPort.port = 'COM{}'.format(x)
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


def GPS(Location,gps_on, Frame_num):
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
    lon, lat = 0, 0
    try:
        while True:
            line = serialPort.readline()
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



            if lon ==0 or lat == 0:
                time.sleep(1)
            else:
                #print ('gps ready, current location:{},{}'.format(lon,lat))
                gps_on.value = True
                Location[:] = [lon,lat]
                with open('location.csv', 'w') as gps:
                    gps.write('Lat,Lon\n')
                    gps.write('{},{}'.format(lat,lon))

    except serial.SerialException:
        print ('Error opening GPS')
        gps_on.value = 3
    finally:
        serialPort.close()
        print('GPS finish')

def log_writer(bag, Frame_num, Location, take_pic, command, pause):
    '''

    :param bag:
    :param Frame_num:
    :param Location:
    :param take_pic:
    :param command:
    :param camera_on: camera value: 0:initial, 1:on, 2:repeat, 3:quit
    :param camera_repeat:
    :return:
    '''
    print(bag)
    lib = {'0': '', '1': 'start', '2': 'restart', '9': 'quit', '4': 'take pic', '5': 'auto', '6': 'pause', }

    i = 1
    foto_location = (0, 0)
    foto_frame = Frame_num[0]
    while command.value < 9:
        status = pause.value
        (lon, lat) = Location[:]
        current_location = (lon, lat)
        present = datetime.datetime.now()
        date = '{},{},{},{}'.format(present.day, present.month, present.year, present.time())
        local_take_pic = False

        if take_pic.value == 1:
            continue

        if status == 0 and gps_dis(current_location, foto_location) > 15:
            local_take_pic = True

        command_in_dict = lib[str(command.value)]
        if command.value != 0:
            print('command:', command.value, command_in_dict)
        if command_in_dict == 'take pic':
            local_take_pic = True
        elif command_in_dict == 'auto':
            pause.value = 0
            time.sleep(1)
            command.value = 0
        elif command_in_dict == 'pause':
            pause.value = 1
            time.sleep(1)
            command.value = 0
        elif command_in_dict == 'restart':
            print ('Camera restart')
            break

        if current_location == foto_location:
            local_take_pic = False

        if local_take_pic:
            take_pic.value = 1
            time.sleep(0.1)
            (color_frame_num, depth_frame_num) = Frame_num[:]
            logmsg = '{},{},{},{},{},{}\n'.format(i, color_frame_num, depth_frame_num, lon, lat, date)
            print('Foto {} gemacht um {:.03},{:.04}'.format(i, lon, lat))
            with open('./foto_log/{}.txt'.format(bag), 'a') as logfile:
                logfile.write(logmsg)
            with open('foto_location.csv', 'a') as record:
                record.write(logmsg)
            foto_location = (lon, lat)
            i += 1
    print('log writer ended')


def Camera(bag, child_conn, command, Frame_num, take_pic):
    """
    Main camera running
    :param child_conn: source of image, sending to openCV
    :param take_pic: mp.Value, receive True will take one picture, and send back False when done
    :param Frame_num: mp.Array, frame number of the picture taken
    :param camera_on: mp.Value, the status of camera
    :param bag: the number of the current recorded file
    :return:
    camera value: 0:initial, 1:on, 2:repeat, 3:quit
    """
    print('camera start')
    bag_name = './bag/{}.bag'.format(bag)
    try:
        pipeline = rs.pipeline()
        config = rs.config()
        config.enable_stream(rs.stream.depth, 1280, 720, rs.format.z16, 15)
        config.enable_stream(rs.stream.color, 1920, 1080, rs.format.rgb8, 15)
        config.enable_record_to_file(bag_name)
        profile = pipeline.start(config)

        device = profile.get_device()  # get record device
        recorder = device.as_recorder()
        recorder.pause()  # and pause it

        sensor = profile.get_device().query_sensors()
        for x in sensor:
            x.set_option(rs.option.frames_queue_size, 32)
        # set auto exposure but process data first
        color_sensor = profile.get_device().query_sensors()[1]
        color_sensor.set_option(rs.option.auto_exposure_priority, True)
        for x in range(20):
            pipeline.wait_for_frames()
        while command.value < 9:
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
            cv2.namedWindow('Server', cv2.WINDOW_AUTOSIZE)
            cv2.imshow('Server', images)
            key = cv2.waitKeyEx(1)
            
            if command.value in (9, 2):  # 9 for quit, 2 for restart
                print(command.value, 'camera quit or restart')
                break
            
            child_conn.send((color_image, depth_image))
            if take_pic.value == 1:
                recorder.resume()
                frames = pipeline.wait_for_frames()
                depth_frame = frames.get_depth_frame()
                color_frame = frames.get_color_frame()
                var = rs.frame.get_frame_number(color_frame)
                vard = rs.frame.get_frame_number(depth_frame)
                Frame_num[:] = [var, vard]
                time.sleep(0.05)
                recorder.pause()
                # switch back to none
                command.value = 0
                take_pic.value = 0
            
        pipeline.stop()
    except RuntimeError:
        print('camera runtime error')
    finally:
        print('pipeline closed')
        if command.value == 9:
            command.value = 99


def image_server(host, port, parent_conn, command, pause):  # sending image
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)
        s.bind((host, port))
        s.listen(5)
        print('image listening')
        (conn, addr) = s.accept()
        print('image connected')
        lib = {'0': '', '1': 'start', '2': 'restart', '9': 'quit', '4': 'take pic', '5': 'auto', '6': 'pause', }

        while command.value != 99:
            status = pause.value
            
            color_image, depth_image = parent_conn.recv()
            depth_colormap_resize = cv2.resize(depth_image, (150, 150))
            color_cvt = cv2.cvtColor(color_image, cv2.COLOR_RGB2BGR)
            color_cvt_2 = cv2.resize(color_cvt, (150, 150))
            images = np.hstack((color_cvt_2, depth_colormap_resize))

            if status == 1:
                cv2.rectangle(images, (20,60), (270,100), (0, 0, 255), -1)
                font = cv2.FONT_HERSHEY_SIMPLEX
                bottomLeftCornerOfText = (60,100)
                fontScale = 2
                fontColor = (0, 0, 0)
                lineType = 4
                cv2.putText(images, 'Pause', bottomLeftCornerOfText, font, fontScale, fontColor, lineType)
            
            result, reply = cv2.imencode('.jpg', images)
            reply = reply.tobytes()
            reply = pickle.dumps(reply, 0)
            # print('reply: ', reply)
            size = len(reply)
            conn.sendall(struct.pack(">L", size) + reply)
            #print('sent {}'.format(size))
        

            
        print('image server end')
        conn.close()
    except ConnectionResetError:
        print('reset')
    except EOFError:
        print('EOF')
    finally:
        print('image server ended')




def command_server(host,port,command):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)
        s.bind((host, port))
        s.listen(10)
        print('command listening')
        conn, addr = s.accept()
        print('command connected')
        while command.value != 99:
            data = conn.recv(1)
            if data != b'':
                command.value = int(data)
                print('data:', data)
            elif data == b'9':
                print('command end')
                break
        conn.close()

    finally:
        print('command server ended')
        #command.value = 9



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
                num+=1
            else:
                print ('current filename:{}'.format(file_name))
                break
        return file_name
    finally:
        pass


def fake_gps(Location, gps_on,):
    import random
    while True:
        lon, lat = random.random(), random.random()
        gps_on.value = True
        Location[:] = [lon, lat]
        time.sleep(2)


def main():
    # Create Folders for Data
    folder_list = ('bag','foto_log')
    for folder in folder_list:
        dir_generate(folder)
    # Create Variables between Processes
    location = mp.Array('d',[0,0])
    frame_num = mp.Array('i',[0,0])


    gps_on = mp.Value('i',False)
    # Start GPS process
    gps_process = mp.Process(target=fake_gps, args=(location, gps_on,))
    gps_process.start()

    while gps_on.value == 0:
        time.sleep(1)
    print('gps is ready')

    take_pic = mp.Value('i', 0)
    command = mp.Value('i', 0)
    pause = mp.Value('i',0)
    parent , child = mp.Pipe()

    host = '127.0.0.1'
    port = 12347
    P1 = mp.Process(target=image_server, args=(host, port, parent, command, pause))
    P2 = mp.Process(target=command_server, args=(host, 12345, command,))
    P1.start()
    P2.start()
    while command.value !=1:
        time.sleep(1)
        if command.value == 9:
            break
    print('connections made')
    while command.value < 9:
        command.value = 0
        if gps_on.value == 3:
            pause_exit()
            break
        bag = bag_num()
        img_process = mp.Process(target=log_writer, args=(bag, frame_num, location, take_pic, command, pause))
        img_process.start()
        Camera(bag, child, command, frame_num, take_pic,)
    print(command.value, 'main end')
    parent.close()
    gps_process.terminate()
    P1.terminate()
    P2.terminate()
    img_process.terminate()
    print('all closed')


if __name__ == '__main__':
    main()