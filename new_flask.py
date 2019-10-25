from flask import Flask, render_template, Response, request
from new_command import RScam
import threading

index = """	<h1>Image Stream </h1>
    <img src="{{ url_for('video_feed') }}">"""
app = Flask(__name__)
a = RScam()


@app.route('/')
def index():
    return index

def gen():
    while True:
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + a.img + b'\r\n')

@app.route('/video_feed')
def video():
    return Response(gen(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/cmd/<cmd>')
def command(cmd):
    camera_command_dict = {"": 0, "running": 1, "restart": 2, "shot": 3, "quit": 99,
                           "auto": 11, "pause": 12}
    if cmd == 'start':
        if a.gps_status.value == 0:
            a.gps_on()
            return "starting gps"
        elif a.gps_status.value == 1 and a.camera_command.value == 0:
            t = threading.Thread(target=a.camera_loop)
            t.start()
            return "started camera"
        else:
            print(a.gps_status.value, a.camera_command.value)
            return "start but waiting GPS"
    elif cmd == "gps":
        ans = a.get_gps()
        return ans
    else:
        try:
            a.camera_command.value = camera_command_dict[cmd]
        except KeyError:
            return "{} not allowed".format(cmd)
        finally:
            return cmd



@app.route('/dis/<num>')
def set_dist(num):
    a.pic_distance = int(num)

if __name__ == '__main__':
    try:
        app.run('0.0.0.0')
    except KeyboardInterrupt:
        pass
    finally:
        pass