from flask import Flask, render_template, Response
from command_class import RScam
import threading

index = """ <h1>Image Stream </h1>
    <img src="{{ url_for('video_feed') }}">"""
app = Flask(__name__)
a = RScam()


@app.route('/')
def index():
    return "index"

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
            a.start_gps()
            a.restart = True
            t = threading.Thread(target=a.main_loop)
            t.start()
            print("start loop")
            return "started camera"
        elif a.gps_status.value == 2:
            print("wait for signal")
            return "waiting for signal"
        else:
            print(a.gps_status.value, a.camera_command.value)
            return "start but waiting GPS"
    elif cmd == "gps":
        ans = str(a.Location[:])
        print(ans)
        return ans
    else:
        try:
            a.command = cmd
            if cmd == 'quit':
                a.restart = False
        except KeyError:
            return "{} not allowed".format(cmd)
        finally:
            return cmd


@app.route('/auto/<in_text>')
def auto(in_text):
    a.command = in_text
    return in_text


@app.route('/dis/<num>')
def set_dist(num):
    print(num, type(num))
    a.distance = int(num)
    return num


if __name__ == '__main__':
    try:
        app.run('0.0.0.0')
    except KeyboardInterrupt:
        pass
    finally:
        pass
