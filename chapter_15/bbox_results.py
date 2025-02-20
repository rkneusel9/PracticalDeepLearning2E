#
#  file:  bbox_results.py
#
#  Interpret the output of bbox.py
#
#  RTK, 27-Dec-2023
#  Last update:  28-Dec-2023
#
################################################################

import os
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

def IoU(soft,bbox, yc,yb, correctOnly=False):
    """Calculate per class IoU"""
    def CalcIoU(a,b):
        ra,ca,ha,wa = a
        rb,cb,hb,wb = b
        r1,c1 = max(ra,rb), max(ca,cb)
        r2,c2 = min(ra+ha, rb+hb), min(ca+wa, cb+wb)
        i = max(0, r2-r1) * max(0, c2-c1)  # allow no intersection
        u = ha*wa + hb*wb - i
        iou = (i/u) if (u>0) else 0
        return iou
    iou,n = np.zeros(10), np.zeros(10)
    for i in range(len(soft)):
        pc,tc = np.argmax(soft[i]), np.argmax(yc[i])
        iu = CalcIoU(bbox[i],yb[i])
        if (correctOnly):
            if (pc == tc):
                iou[tc] += iu
                n[tc] += 1
        else:
            iou[tc] += iu
            n[tc] += 1
    return iou/n

def DrawBox(img,xlo,ylo,xhi,yhi, color=(255,0,0)):
    x0,x1 = min(xlo,127), min(xhi,127)
    y0,y1 = min(ylo,127), min(yhi,127)
    for i in range(x0,x1+1):
        img[i,y0,:] = color
        img[i,y1,:] = color
    for i in range(y0,y1+1):
        img[x0,i,:] = color
        img[x1,i,:] = color

def Label(img, ch, color=(255,0,0)):
    image = Image.fromarray(img)
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    draw.text((14,14), ch, font=font, fill=color)
    return np.array(image)


if (len(sys.argv) == 1):
    print()
    print("bbox_results <dir> blank|land [images]")
    print()
    print("  <dir>      - source directory (output of bbox.py)")
    print("  blank|land - test image source")
    print("  images     - if present, create .png images")
    print()
    exit(0)

sdir = sys.argv[1]
mode = sys.argv[2].lower()
mdir = "images" if (len(sys.argv) > 3) else ""

#  Load the test images
if (mode == "land"):
    xtest = np.load("../data/mnist/mnist_bbox_land_xtest.npy")
else:
    xtest = np.load("../data/mnist/mnist_bbox_xtest.npy")

#  Load the labels
ytestb = np.load("../data/mnist/mnist_bbox_ytestb.npy")
ytestc = np.load("../data/mnist/mnist_bbox_ytestc.npy")

#  Load the predictions
soft = np.load(sdir + "/softmax.npy")
bbox = np.load(sdir + "/bounding_box.npy")

#  Output bounding box images, if requested
if (mdir != ""):
    os.system("mkdir %s/images 2>/dev/null" % sdir)
    for i in range(len(bbox)):
        img = np.zeros((128,128,3), dtype="uint8")
        img[:,:,0] = xtest[i]
        img[:,:,1] = xtest[i]
        img[:,:,2] = xtest[i]

        #  Predicted bounding box
        xlo,ylo,h,w = (bbox[i]*128).astype("uint8")
        xhi,yhi = xlo+h, ylo+w
        DrawBox(img, xlo, ylo, xhi, yhi, color=(255,0,0))

        #  Label bounding box
        xlo,ylo,h,w = (ytestb[i]*128).astype("uint8")
        xhi,yhi = xlo+h, ylo+w
        DrawBox(img, xlo, ylo, xhi, yhi, color=(0,200,200))
        y = np.argmax(soft[i])

        img = Label(img, "%d" % y)
        Image.fromarray(img).save("%s/images/image__%05d.png" % (sdir,i))

#  Bounding box metrics
iou0 = IoU(soft,bbox,ytestc,ytestb, correctOnly=False)
iou1 = IoU(soft,bbox,ytestc,ytestb, correctOnly=True)

print("IoU for all test samples:")
for i in range(10):
    print("    %d: %0.6f" % (i,iou0[i]))
print("    mean = %0.6f" % iou0.mean())
print()

print("IoU for correctly classified samples:")
for i in range(10):
    print("    %d: %0.6f" % (i,iou1[i]))
print("    mean = %0.6f" % iou1.mean())
print()

