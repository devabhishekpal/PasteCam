from PIL import Image
import cv2
import numpy as np
import os

def paste(filename, x, y):

    filename = filename.replace('\\', '/')
    img = Image.new("RGB", (3508, 2480), (255,255,255))
    img.save("blank.jpg", "JPG")
    window = np.zeroes([3508, 2408, 3], dtype=np.uint8)
    window.fill(255)
    cv2.imshow('Point Here', window)
    pasteImg = Image.open(filename)
    img.paste(pasteImg, (x,y))
    n = len([name for name in os.listdir('../../processedImages')])
    img.save("../../processedImages/image"+ (n+1) + ".jpg")
    

