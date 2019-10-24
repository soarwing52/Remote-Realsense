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
    if cmd == 'start':
        t = threading.Thread(target=a.run_cam)
        t.start()
        return "start"
    elif cmd == "shot":
        a.take_pic = True
        return "shot"
    elif cmd == "quit":
        a.cam = 0
        return "cmd"
    elif cmd == 'gps':
        a.gps_on()
        return 'GPS'
    elif cmd == 'read':
        a.get_gps()
        return 'read'


if __name__ == '__main__':
    global running
    running = False
    try:
        app.run('0.0.0.0')
    except KeyboardInterrupt:
        pass
    finally:
        pass