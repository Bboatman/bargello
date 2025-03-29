from os import listdir
from os.path import isfile, join
import random
from PIL import Image, ImageDraw
import math
import numpy
from sklearn.metrics.pairwise import cosine_similarity
from collections import deque

base_url = "./refimg"
output_name = "design_out.png"

in_to_px = 10
strip_count = 21
strip_width_in = 2.5
seam_width_in = .25
min_row_size_in = seam_width_in * 4
max_row_size_in = min_row_size_in * 3

def ref_files():
    files = [f for f in listdir(base_url) if isfile(join(base_url, f))]
    return files


def get_colors():
    colors = {}
    for f in ref_files():
        loc = join(base_url, f)
        with Image.open(loc) as im:
            r = list(im.getdata(0))
            g = list(im.getdata(1))
            b = list(im.getdata(2))
            r_avg = str(hex(math.floor(sum(r) / len(r))).capitalize()[2:])
            g_avg = str(hex(math.floor(sum(g) / len(g))).capitalize()[2:])
            b_avg = str(hex(math.floor(sum(b) / len(b))).capitalize()[2:])
            hex_color = "#{}{}{}".format(r_avg, g_avg, b_avg)
            colors[f] = {
                "hex_color": hex_color,
                "rgb": [math.floor(sum(x) / len(x)) for x in [r,g,b]]
            }
    return colors

def get_recommended_order():
    colors = get_colors()
    ordered = [list(colors.keys())[0]]

    for i in range(len(colors.keys())):
        current = ordered[-1]
        current_numerical = numpy.array(colors[current]["rgb"])
        current_numerical = current_numerical.reshape(1, -1)
        match = ""
        dist = -1
        for c in colors.keys():
            if c not in ordered:
                test_numerical = numpy.array(colors[c]["rgb"])
                test_numerical = test_numerical.reshape(1, -1)
                cosim = cosine_similarity(current_numerical, test_numerical)
                if cosim > dist:
                    dist = cosim
                    match = c
        
        if (match is not ""):
            ordered.append(match)

    return ordered

def draw_row(draw, color_list, current_height, row_height):
    colors = get_colors()
    count = 0
    for c in color_list:
        color = colors[c]
        upper_left_x = count * (strip_width_in * in_to_px)
        upper_left_y = current_height
        lower_right_x = (count+1) *  (strip_width_in * in_to_px)
        lower_right_y = current_height + row_height
        fill_val = (color["rgb"][0], color["rgb"][1],color["rgb"][2])
        draw.rectangle(xy = (upper_left_x, upper_left_y, lower_right_x, lower_right_y), 
                fill = (fill_val), 
                outline = (fill_val), 
                width = 0) 
        count += 1

colors = get_colors()
color_list = get_recommended_order()
print(color_list)
width = math.floor(strip_count * strip_width_in * in_to_px)
height = width
img= Image.new(mode="RGB", size=(width, height))

# Creating a Draw object 
draw = ImageDraw.Draw(img) 

current_height = 0
row_height_in = (max_row_size_in + min_row_size_in) / 2
prob = .5
change_rate = 0
while current_height < width:
    direction = random.random()
    size_change = random.random()
    
    items = deque(color_list)

    if direction <= prob:
        #Go left
        items.rotate(-1)
        color_list = list(items)
        prob -= change_rate
    else: 
        #go right
        items.rotate(1)
        color_list = list(items)
        prob += change_rate

    if size_change < .33:
        #shrink
        pass
    elif size_change < .66:
        #no_change
        pass
    else:
        #grow
        pass

    row_height = row_height_in * in_to_px
    draw_row(draw, color_list, current_height, row_height)
    current_height += row_height



img.show()
img.save(output_name)


