#!/usr/bin/env python3
# coding: utf-8

import os
import sys
import math
import signal
import argparse

from version import *

#
# notes
#

# w = hole width     (lochweite, lochgroesse vertikal / y)
# l = hole length    (lochlaenge, lochgroesse horizontal / x)
# p = hole partition (lochteilung, abstand von lochmitte zu lochmitte)
# c = hole clearance (lochabstand, abstand von lochrand zu lochrand)
#
# uniform:   make rows have equal length (only applies to staggered patterns)
# staggered: holes of every other row are offset (Rv, Qv, etc)
# corners:   start with a hole in the left corner (only applies to staggered patterns)
# skip:      skip this many holes at the beginning/end of rows

#
# global configuration
#

cfg_anykey_before_abort = (os.name == 'nt')

#
# defaults
#

default_filename     = "pattern.svg"
default_image_width  = "100"
default_image_height = "100"

default_fill            = "none"
default_stroke          = "#000"
default_stroke_width    = 1
default_stroke_linejoin = "round"

default_uniform = False
default_corners = False
default_skip    = 0

#
# functions
#

def abort(message, code=0, anykey=False):
    print(message)
    if anykey: 
        input("Press any key to end")
    sys.exit(code)

def signal_handler(sig, frame):
    abort("Received signal " + sig + ", exiting.")


def draw_hole_r(svg, cfg, x, y, w, h):
    radius = w * 0.5
    svg.add(svg.circle(center=(x, y), r=radius, **cfg))

def draw_hole_q(svg, cfg, x, y, w, h):
    left = x - w * 0.5
    top  = y - w * 0.5
    svg.add(svg.rect((left, top), (w, w), **cfg))

def draw_hole_l(svg, cfg, x, y, w, h):
    left = x - w * 0.5
    top  = y - h * 0.5
    radius = h * 0.5
    svg.add(svg.rect((left, top), (w, h), radius, radius, **cfg))

def draw_pattern(svg, sw, sh, wx, wy, px, py, hole_func, cfg, **opt):
    uniform = opt["uniform"]
    staggered = opt["staggered"]
    corners = opt["corners"]
    skip = opt["skip"]
    shifted = (uniform and staggered)
    # hole clearance
    cx = px - wx
    cy = py - wy
    # plate edges
    ex = -(2 * wx) if px <= 0 else (2 * px)
    ey = -(2 * wy) if py <= 0 else (2 * py)
    # number of holes
    hx = math.floor((sw - ex + cx) / px)
    hy = math.floor((sh - ey + cy) / py)
    # field width
    fw = px * (hx - 0.5 * shifted)
    fh = py * hy
    # starting point for drawing
    sx = 0.5 * (sw - fw) + 0.5 * px
    sy = 0.5 * (sh - fh) + 0.5 * py
    # hole drawing props
    lw = cfg["stroke-width"] * 0.5
    hwx = wx - lw
    hwy = wy - lw

    for row in range(0, hy):
        mod = staggered * ((row % 2) ^ (not corners))
        skip = shifted * skip
        less = (shifted or mod) + ((not mod) * skip)
        y = sy + (row * py)
        for col in range((mod * skip), (hx - less)):
            x = sx + (col * px) + (mod * px * 0.5)
            hole_func(svg, cfg, x, y, hwx, hwy)

#
# import external dependencies we can't expect to be installed
#

try:
    import svgwrite
except ImportError:
    abort("locher requires svgwrite to run. Try `pip install svgwrite`.", 65, cfg_anykey_before_abort)

#
# register signal handler for sigint
#

signal.signal(signal.SIGINT, signal_handler)

#
# banner
#

banner = """
  _               _
 | |  ___    ___ | |__    ___  _ __
 | | / _ \  / __|| '_ \  / _ \| '__|
 | || (_) || (__ | | | ||  __/| |
 |_| \___/  \___||_| |_| \___||_|

 Draw DIN 24041 hole patterns as SVG
"""

print(banner)
print(" Version " + Version.get_version() + " (using svgwrite " + svgwrite.__version__ + ")\n")

#
# argparse
#

parser = argparse.ArgumentParser()
parser.add_argument("-t", "--hole-type",        required = True)
parser.add_argument("-w", "--hole-width",       required = True,  type = int) # hole size y
parser.add_argument("-l", "--hole-length",      required = False, type = int) # hole size x
parser.add_argument("-p", "--hole-partition-y", required = True,  type = int) # hole partition y
parser.add_argument("-q", "--hole-partition-x", required = False, type = int) # hole partition x
parser.add_argument("-u", "--uniform",          default = default_uniform)
parser.add_argument("-c", "--corners",          default = default_corners)
parser.add_argument("-s", "--skip",             default = default_skip, type = int)
parser.add_argument("-x", "--image-width",  default = default_image_width,  type = int)
parser.add_argument("-y", "--image-height", default = default_image_height, type = int)
parser.add_argument("-f", "--filename",     default = default_filename)
parser.add_argument("--fill",            default = default_fill,   metavar = "FILL-COLOR")
parser.add_argument("--stroke",          default = default_stroke, metavar = "STROKE-COLOR")
parser.add_argument("--stroke-width",    default = default_stroke_width,    type = int)
parser.add_argument("--stroke-linejoin", default = default_stroke_linejoin)

args = parser.parse_args()

svg_width   = str(args.image_width) + "mm"
svg_height  = str(args.image_height) + "mm"
svg_viewbox = "0 0 " + str(args.image_width) + " " + str(args.image_height)

config = {
        "fill":            args.fill,
        "stroke":          args.stroke,
        "stroke-width":    args.stroke_width,
        "stroke-linejoin": args.stroke_linejoin
}

pattern = {
        "w": args.hole_width,
        "l": args.hole_length if args.hole_length else args.hole_width,
        "p": args.hole_partition_y,
        "q": args.hole_partition_x if args.hole_partition_x else args.hole_partition_y
}

options = {
        "uniform": args.uniform,
        "staggered": False,
        "corners": args.corners,
        "skip": 0
}

hole_func = None
hole_type = args.hole_type.lower()

if   (hole_type == "rd"):
    hole_func = draw_hole_r
    pattern["q"] = math.sqrt(2) * pattern["q"]
    pattern["p"] = pattern["q"] * 0.5
    options["staggered"] = True
elif (hole_type == "rv"):
    hole_func = draw_hole_r
    pattern["p"] = math.sqrt(3) * 0.5 * pattern["q"]
    options["staggered"] = True
elif (hole_type == "rg"):
    hole_func = draw_hole_r
    options["staggered"] = False
elif (hole_type == "qd"):
    hole_func = draw_hole_q
    # TODO calc p/q
    # TODO rotate holes?
    options["staggered"] = True
    abort("Hole type " + hole_type + " not implemented", anykey=cfg_anykey_before_abort)
elif (hole_type == "qv"):
    hole_func = draw_hole_q
    # TODO calc p/q
    options["staggered"] = True
    abort("Hole type " + hole_type + " not implemented", anykey=cfg_anykey_before_abort)
elif (hole_type == "qg"):
    hole_func = draw_hole_q
    options["staggered"] = False
elif (hole_type == "hv"):
    abort("Hole type " + hole_type + " not implemented", anykey=cfg_anykey_before_abort)
elif (hole_type == "lg"  or hole_type == "lgl"):
    hole_func = draw_hole_l
    options["staggered"] = False
elif (hole_type == "lv"  or hole_type == "lvl"):
    hole_func = draw_hole_l
    options["staggered"] = True
elif (hole_type == "lge" or hole_type == "lgel"):
    hole_func = draw_hole_l
    options["staggered"] = False
elif (hole_type == "lve" or hole_type == "lvel"):
    hole_func = draw_hole_l
    options["staggered"] = True
else:
    abort("Hole type " + hole_type + " not implemented", anykey=cfg_anykey_before_abort)
#elif (hole_type is "lvq"):
    #
#elif (hole_type is "lgq"):
    #
#elif (hole_type is "lgeq"):
    #
#elif (hole_type is "lveq"):
    #

svg = svgwrite.Drawing(args.filename, size=(svg_width, svg_height), viewBox=svg_viewbox, profile='tiny')
draw_pattern(svg, args.image_width, args.image_height, pattern["l"], pattern["w"], pattern["q"], pattern["p"], hole_func, config, **options)
svg.save(pretty=True, indent=4) 

