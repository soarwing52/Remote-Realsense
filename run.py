import multiprocessing as mp
import pyrealsense2 as rs
import datetime, time

def camera(cmd):
    try:
        now = datetime.datetime.now()
        file_name = '{:02d}{:02d}_{:03d}'.format(now.month, now.day, 1)
        bag_name = './bag/{}.bag'.format(file_name)
        print('start camera with ', bag_name)
        pipeline = rs.pipeline()
        config = rs.config()
        config.enable_stream(rs.stream.depth, 1280, 720, rs.format.z16, 15)
        config.enable_stream(rs.stream.color, 1920, 1080, rs.format.rgb8, 15)
        config.enable_record_to_file(bag_name)
        profile = pipeline.start(config)

        while True:
            frames = pipeline.wait_for_frames()

            if cmd.value == 1:
                break

        pipeline.stop()

    finally:
        print('stopped')

if __name__ == '__main__':
    cmd = mp.Value('i', 0)
    p = mp.Process(target=camera, args=(cmd,))
    p.start()
    time.sleep(5)
    cmd.value =1
