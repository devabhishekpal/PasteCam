import io
import os
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from PIL import Image
import numpy as np
import time
import screenpoint
from datetime import datetime
import pyscreenshot
import requests
import logging
import pasteHandler as ph

max_view_size = 700
max_ss_size = 400
basnet_service_ip = "http://127.0.0.1"
dist = 3 #Later replace this with the distance of view from screen

app = Flask(__name__)
CORS(app)

#Default route
@app.route('/', methods=['GET'])
def reply():
    return 'Welcome to PasteCam'


#Check ping stats
@app.route('/ping', methods=['GET'])
def ping():
    logging.info('ping')
    req = requests.get(basnet_service_ip, headers={'Host': args.basnet_service_host})
    logging.info(f'pong: {req.status_code} {req.content}')
    return 'pong'


#Handle cut requests
@app.route('/cut', methods=['POST'])
def cut():
    logging.info('CUT')

    logging.info('Receiving data')

    #Converting to unsigned int8
    if 'data' not in request.files:
        return jsonify({
            'status' : 'error',
            'error' : 'missing file parameter `data`'
        }), 400
    
    data = request.files['data'].read()
    if len(data) == 0:
        return jsonify({
            'status' : 'error',
            'error' : 'empty image received'
        }), 400
    
    with open('cut_received.jpg', 'wb') as recFile:
        recFile.write(data)
    
    #Send data to BASNET service
    logging.info('sending to BASNet service')
    headers = {}
    files = {'data' : open('cut_received.jpg', 'rb')}
    result = requests.post(basnet_service_ip, headers = headers, files = files)

    #Save mask locally
    logging.info('Saving mask locally')
    with open('cut_mask.png', 'wb') as maskFile:
        maskFile.write(result.content)
    
    logging.info('Open mask')
    mask = Image.open('cut_mask.png').convert("L")

    #Convert string to Pillow image
    logging.info('Creating image')
    reference = Image.open(io.BytesIO(data))
    empty = Image.new('RGBA', ref.size, 0)
    img = Image.composite(reference, empty, mask)

    #Save image locally
    logging.info('Saving image')
    scaled_img = img.resize((img.size[0]* dist, img.size[1] * dist))
    scaled_img.save('cut_current.png')

    #Store image in buffer
    buff = io.BytesIO()
    img.save(buff, 'PNG')
    buff.seek(0)

    return send_file(buff, mimetype = 'image/png')


#Handle paste requests
@app.route('/paste', methods=['POST'])
def paste():
    logging.info('PASTE')

    #Convert image data to unsigned 8byte int
    if 'data' not in request.files:
        return jsonify({
            'status' : 'error'
            'error' : 'missing file param `data`'
        }), 400
    data = request.files['data'].read()
    if len(data) == 0
        return jsonify({
            'status' : 'error'
            'error' : 'empty image'
        }), 400
    with open('paste_received.jpg', 'wb') as receivedFile:
        receivedFile.write(data)
    
    #Convert to Pillow image
    logging.info('Loading image')
    view = Image.open(io.BytesIO(data))

    #Make sure view size is within max_view_size
    if view.size[0] > max_view_size or view.size[1] > max_view_size:
        view.thumbnail((max_view_size, max_view_size))
    
    #Take a screenshot
    logging.info('Taking a screenshot')
    ss = pyscreenshot.grab()
    screen_width, screen_height = ss.size

    #Make sure the screenshot is within max_ss_size
    if ss.size[0] > max_ss_size or ss.size[1] > max_ss_size:
        ss.thumbnail((max_ss_size, max_ss_size))
    
    #Find the view centroid in screen space
    logging.info('Find the projected point')
    view_arr = np.array(view.convert("L"))
    screen_arr = np.array(ss.convert("L"))
    x, y = screenpoint.project(view_arr, screen_arr, False)

    found = x != -1 and y != -1 #Making sure the point is found

    if found:
        #Bring image to screen space
        x = int(x / ss.size[0] * screen_width)
        y = int(y / ss.size[1] * screen_height)
        logging.info(f'{x}, {y}')
        img_path = os.path.join(os.getcwd(), 'cut_current.png')
        ph.paste(img_path, x, y)

if __name__ == '__main__':
    os.environ['FLASK_ENV'] = 'development'
    app.run(debug = True, host = '0.0.0.0', port = int(os.environ.get('PORT', 8080)))
