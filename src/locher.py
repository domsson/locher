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

# Hole types according to DIN 24041:
#
# Rv  = Rundlochung in versetzten Reihen
# Rd  = Rundlochung in diagonal versetzten Reihen
# Rg  = Rundlochung in geraden Reihen
# Qg  = Quadratlochung in versetzten Reihen
# Qd  = Quadratlochung in diagonal versetzten Reihen
# Qg  = Quadratlochung in geraden Reihen
# Lv  = Langlochung in versetzten Reihen
# Lg  = Langlochung in geraden Reihen
# Lge = Langlochung in geraden Reihen, eckig

# Hole pattern parameters according to DIN 24041:
#
# w  = hole width, vertical         (lochweite, lochgroesse vertikal / y)
# l  = hole length, horizontal      (lochlaenge, lochgroesse horizontal / x)
# p  = hole partition               (lochteilung, abstand von lochmitte zu lochmitte)
# c  = hole clearance               (lochabstand, abstand von lochrand zu lochrand)
# e1 = hole free area at the bottom (ungelochter rand)
# e2 = hole free area at the top    (ungelochter rand)
# f1 = hole free area on the left   (ungelochter rand)
# f2 = hole free area on the right  (ungelochter rand)
# a1 = plate size, vertical / y     (plattenmaß, plattenlaenge)
# b1 = plate size, horizontal / x   (plattenmaß, plattenbreite)
# s  = plate strength               (plattendicke)
# A0 = relative hole free area      (relative freie Lochflaeche)

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

default_output_file  = "pattern.svg"
default_image_width  = "100"
default_image_height = "100"
default_image_zoom   = "1"

default_fill            = "none"
default_stroke          = "#000"
default_stroke_width    = "1"
default_stroke_linejoin = "round"
default_font_family     = "sans-serif"
default_font_size       = "3"

default_scale_stroke    = False

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
    return svg.circle(center=(x, y), r=radius, **cfg, id="hole")

def draw_hole_q(svg, cfg, x, y, w, h):
    left = x - w * 0.5
    top  = y - w * 0.5
    return svg.rect((left, top), (w, w), **cfg, id="hole")

def draw_hole_l(svg, cfg, x, y, w, h):
    left = x - w * 0.5
    top  = y - h * 0.5
    radius = h * 0.5
    return svg.rect((left, top), (w, h), radius, radius, **cfg, id="hole")

def draw_hole_le(svg, cfg, x, y, w, h):
    left = x - w * 0.5
    top  = y - h * 0.5
    return svg.add(svg.rect((left, top), (w, h), **cfg, id="hole"))

def draw_pattern(svg, sw, sh, wx, wy, px, py, f, e, hole_func, cfg, **opt):
    uniform = opt["uniform"]
    staggered = opt["staggered"]
    corners = opt["corners"]
    skip = opt["skip"]
    shifted = (uniform and staggered)
    # hole clearance
    cx = px - wx
    cy = py - wy
    # plate edges
    ex = -(2 * wx) if f <= 0 else (2 * f)
    ey = -(2 * wy) if e <= 0 else (2 * e)
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
    #lw = cfg["stroke-width"] * 0.5
    #hwx = wx - lw
    #hwy = wy - lw
    hwx = wx
    hwy = wy
    # create and add reference hole    
    hole = hole_func(svg, cfg, 0, 0, hwx, hwy)
    svg.defs.add(hole)
    # create the pattern group
    group = svg.g(id="pattern")
    
    # add hole instances to the pattern group
    for row in range(0, hy):
        mod = staggered * ((row % 2) ^ (not corners))
        skip = shifted * skip
        less = (shifted or mod) + ((not mod) * skip)
        y = sy + (row * py)
        for col in range((mod * skip), (hx - less)):
            x = sx + (col * px) + (mod * px * 0.5)
            group.add(svg.use(hole, insert=(x, y)))
    # add the group to the drawing
    svg.add(group)

def draw_ruler(svg, sw, sh, zoom, cfg):
    z = 1.0 / zoom
    path_extras = {"stroke": cfg["stroke"], "stroke-width": (0.5 * z), "fill":"none"}
    text_extras = {"font-family": "sans-serif", "font-size": 3 * z, "font-weight": "bold", "fill": cfg["stroke"]}
    rect_extras = {"fill": "#fff", "fill-opacity": 0.8}
    path = "M" + str(sw-(12*z)) + "," + str(sh-(3*z)) + " v" + str(2*z) + " h" + str(10) + " v" + str(-2*z)
    group = svg.g(id="ruler")
    group.add(svg.rect((0, sh-(4*z)), (sw, 5*z), **rect_extras))
    group.add(svg.path(path, **path_extras))
    group.add(svg.text('10 mm', insert=(sw-(25*z), sh-(0.5*z)), **text_extras))
    svg.add(group)

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
parser.add_argument("-t", "--hole-type",          required = True)
parser.add_argument("-w", "--hole-width",         required = True,  type = float) # hole size y
parser.add_argument("-l", "--hole-length",        required = False, type = float) # hole size x
parser.add_argument("-p", "--hole-partition-y",   required = True,  type = float) # hole partition y
parser.add_argument("-q", "--hole-partition-x",   required = False, type = float) # hole partition x
parser.add_argument("-e", "--hole-free-border-y", required = False, type = float, default = 0)
parser.add_argument("-f", "--hole-free-border-x", required = False, type = float, default = 0)
parser.add_argument("-u", "--uniform",        default = default_uniform)
parser.add_argument("-c", "--corners",        default = default_corners)
parser.add_argument("-s", "--skip",           default = default_skip, type = int)
parser.add_argument("-x", "--image-width",  default = default_image_width,  type = int)
parser.add_argument("-y", "--image-height", default = default_image_height, type = int)
parser.add_argument("-z", "--image-zoom",   default = default_image_zoom,   type = float)
parser.add_argument("-o", "--output-file",  default = default_output_file)
parser.add_argument("--fill",            default = default_fill,   metavar = "FILL-COLOR")
parser.add_argument("--stroke",          default = default_stroke, metavar = "STROKE-COLOR")
parser.add_argument("--stroke-width",    default = default_stroke_width,    type = float)
parser.add_argument("--stroke-linejoin", default = default_stroke_linejoin)
parser.add_argument("--font-size",       default = default_font_size)
parser.add_argument("--scale-stroke",    default = default_scale_stroke, type = bool)

args = parser.parse_args()

zoom_factor = 1.0 / args.image_zoom
svg_width   = str(args.image_width) + "mm"
svg_height  = str(args.image_height) + "mm"
box_width   = int(args.image_width * zoom_factor)
box_height  = int(args.image_height * zoom_factor)
svg_viewbox = "0 0 " + str(box_width) + " " + str(box_height)

#
# Preparations
#

config = {
        "fill":            args.fill,
        "stroke":          args.stroke,
        "stroke-width":    args.stroke_width * zoom_factor,
        "stroke-linejoin": args.stroke_linejoin
}
pattern = {
        "w": args.hole_width,
        "l": args.hole_length if args.hole_length else args.hole_width,
        "p": args.hole_partition_y,
        "q": args.hole_partition_x if args.hole_partition_x else args.hole_partition_y,
        "e": args.hole_free_border_y,
        "f": args.hole_free_border_x
}

options = {
        "uniform": args.uniform,
        "staggered": False,
        "corners": args.corners,
        "skip": 0
}

hole_func = None
hole_type = args.hole_type.lower()

if   (hole_type == "rg"):
    hole_func = draw_hole_r
    pattern["q"] = pattern["p"]
    options["staggered"] = False
elif (hole_type == "rd"):
    hole_func = draw_hole_r
    pattern["q"] = math.sqrt(2) * pattern["q"]
    pattern["p"] = pattern["q"] * 0.5
    options["staggered"] = True
elif (hole_type == "rv"):
    hole_func = draw_hole_r
    pattern["p"] = math.sqrt(3) * 0.5 * pattern["q"]
    options["staggered"] = True
elif (hole_type == "qg"):
    hole_func = draw_hole_q
    pattern["q"] = pattern["p"]
    options["staggered"] = False
elif (hole_type == "qd"):
    hole_func = draw_hole_q
    pattern["q"] = math.sqrt(2) * pattern["p"]
    pattern["p"] = pattern["q"] * 0.5
    options["staggered"] = True
elif (hole_type == "qv"):
    hole_func = draw_hole_q
    pattern["q"] = pattern["p"]
    options["staggered"] = True
elif (hole_type == "lg"):
    hole_func = draw_hole_l
    options["staggered"] = False
elif (hole_type == "lge"):
    hole_func = draw_hole_le
    options["staggered"] = False
elif (hole_type == "lv"):
    hole_func = draw_hole_l
    options["staggered"] = True
elif (hole_type == "lve"):
    hole_func = draw_hole_le
    options["staggered"] = True
else:
    abort("Hole type " + args.hole_type + " not implemented", anykey=cfg_anykey_before_abort)

#
# Core
#

svg = svgwrite.Drawing(args.output_file, size=(svg_width, svg_height), viewBox=svg_viewbox)
#svg = svgwrite.Drawing(args.output_file, size=(svg_width, svg_height), viewBox=svg_viewbox, profile='tiny')
draw_pattern(
    svg,
    box_width,
    box_height,
    pattern["l"],
    pattern["w"],
    pattern["q"],
    pattern["p"],
    pattern["f"],
    pattern["e"],
    hole_func,
    config,
    **options
)
draw_ruler(
    svg,
    box_width,
    box_height,
    args.image_zoom,
    config
)
svg.save(pretty=True, indent=4) 

#
# Done
#

abort("Done! SVG written to " + args.output_file, anykey=cfg_anykey_before_abort)

