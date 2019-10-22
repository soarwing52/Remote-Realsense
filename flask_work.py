import subprocess
from flask import Flask, render_template, Response, request
import command_for_flask
import os, time, sys

temp = '<h1> word </h1>'
app = Flask(__name__)

@app.route('/')
def index():
    global a
    print(request)
    return render_template('index.html')

def gen(a):
    while True:
        frame = a.recieve_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    global a, running
    if running:
        return Response(gen(a),
                    mimetype='multipart/x-mixed-replace; boundary=frame')
    else:
        return temp

@app.route('/start', methods=['GET'])
def start():
    global a, running
    if running is not True:
        #os.startfile('2_server.py')
        '''
        subprocess.call(["xdg-open", "2_server"])
        print('opening server')
        for remaining in range(150, 0, -1):
            sys.stdout.write("\r")
            sys.stdout.write("{:2d} seconds remaining.".format(remaining)) 
            sys.stdout.flush()
            time.sleep(1)

        sys.stdout.write("\rComplete!            \n")
        '''
        print('opened server')
        a = command_for_flask.ServerCommand()
        a.start_reciever()
        a.send_command('1')
        running = True
    else:
        print('already running')
    return temp.replace('word', 'Start')


@app.route('/quit')
def quit():
    global a, running
    a.send_command('9')
    time.sleep(10)
    running = False
    return temp.replace('word', 'Quit')


@app.route('/restart')
def restart():
    global a
    a.send_command('2')
    return temp.replace('word', 'Restart')


@app.route('/foto')
def foto():
    global a
    a.send_command('4')
    return temp.replace('word', 'Foto')

@app.route('/open')
def open():
    os.startfile(r'2_server.py')
    print('call')
    return temp.replace('word', 'Open')


@app.route('/command/<cmd>')
def command(cmd):
    global a
    lib = {'0': '', 'start': '1', 'restart': '2', 'quit': '9', 'foto': '4', 'true': '5', 'false': '6', }
    try:
        print(cmd, lib[cmd])
        a.send_command(lib[cmd])
    except KeyError:
        #cmd = 'No Command Found'
        pass
    finally:
        return temp.replace('word', cmd)

if __name__ == '__main__':
    time.sleep(30)
    global running
    running = False
    try:
        app.run('0.0.0.0')
    except KeyboardInterrupt:
        pass
    finally:
        pass