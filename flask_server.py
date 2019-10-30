from flask import Flask, render_template, Response
from command_class import RScam
import threading

index = """ <h1>Image Stream </h1>
    <img src="{{ url_for('video_feed') }}">"""
app = Flask(__name__)
a = RScam()


@app.route('/')
def index():
    msg = str(a.Location[:])
    return render_template('ui.html', msg = 'mmssgg')


def gen():
    while True:
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + a.img + b'\r\n')


@app.route('/video_feed')
def video_feed():
    return Response(gen(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/cmd/<cmd>')
def command(cmd):
    msg = ""
    if cmd == 'start':
        if a.gps_status.value == 0:
            a.start_gps()
            a.restart = True
            t = threading.Thread(target=a.main_loop)
            t.start()
            msg = 'start loop'

        elif a.gps_status.value == 2:
            msg = "wait for signal"
        else:
            msg = "GPS:{},Camera{} \n {}". format(a.gps_status.value, a.camera_command.value, str(a.Location[:]))
    elif cmd == "gps":
        msg = str(a.Location[:])
    else:
        try:
            a.command = cmd
            msg = '{},{}'.format(cmd, a.msg)
            if cmd == 'quit':
                a.restart = False
                msg = 'quit'
        except KeyError:
            msg = "{} not allowed".format(cmd)
        finally:
            pass
    print(msg)
    return render_template('ui.html', msg=msg)


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
