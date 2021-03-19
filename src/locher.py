import math
import svgwrite
import argparse

#
# defaults
#

default_filename = "pattern.svg"
default_image_width = "100"
default_image_height = "100"
default_fill = None
default_stroke = "#fff"
default_stroke_width = 1

#
# functions
#

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

# uniform:   make rows have equal length (only applies to staggered patterns)
# staggered: holes of every other row are offset (Rv, Qv, etc)
# corners:   start with a hole in the left corner (only applies to staggered patterns)
# skip:      skip this many holes at the beginning/end of rows
def draw_pattern(svg, cfg, sw, sh, wx, wy, px, py, hole_func, uniform=False, staggered=False, corners=False, skip=0):
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
    lw = 1 * 0.5 # TODO line width
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

banner = """
  _               _
 | |  ___    ___ | |__    ___  _ __
 | | / _ \  / __|| '_ \  / _ \| '__|
 | || (_) || (__ | | | ||  __/| |
 |_| \___/  \___||_| |_| \___||_|

 Draw hole patterns as per DIN 24041
"""

print(banner)

#
# argparse
#

parser = argparse.ArgumentParser()
parser.add_argument("hole-type",        nargs = 1)
parser.add_argument("hole-width",       nargs = 1)
parser.add_argument("hole-length",      nargs = '?')
parser.add_argument("hole-partition-x", nargs = 1)
parser.add_argument("hole-partition-y", nargs = '?')
parser.add_argument("-x", "--image-width",  type=int, default = default_image_width)
parser.add_argument("-y", "--image-height", type=int, default = default_image_height)
parser.add_argument("-f", "--fill",         default = default_fill)
parser.add_argument("-s", "--stroke",       default = default_stroke)
parser.add_argument("-l", "--stroke-width", type=int, default = default_stroke_width)
parser.add_argument("-o", "--output-file",  default = default_filename)
# TODO also need args for staggered, uniform, corners, skip 
# -- a bit too many for just one-character args, no? is there a better way?
# PS: we don't actually need staggered, as we can tell from the hole type.

args = parser.parse_args()

svg_width   = str(args.image_width) + "mm"
svg_height  = str(args.image_height) + "mm"
svg_viewbox = "0 0 " + str(args.image_width) + " " + str(args.image_height)

cfg = {"fill": "none", "stroke": "#000", "stroke-width": 1, "stroke-linejoin": "round"}

svg = svgwrite.Drawing(args.output_file, size=(svg_width, svg_height), viewBox=svg_viewbox, profile='tiny')
draw_pattern(svg, cfg, args.image_width, args.image_height, 20, 5, 25, 15, draw_hole_q, staggered=True, uniform=False, corners=True)
svg.save(pretty=True, indent=4) 

## python's sad "ternary" syntax:
## [on_true] if [expression] else [on_false]

