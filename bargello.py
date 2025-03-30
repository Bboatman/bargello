from os import listdir
from os.path import isfile, join
import random
from PIL import Image, ImageDraw
import math
from scipy.spatial import distance
from collections import deque

base_url = "./ref_imgs/camelia"
output_name = "design_out.png"

in_to_px = 10
strip_width_in = 2.5
seam_width_in = .25
height_in = 84

min_row_size_in = seam_width_in * 4
max_row_size_in = min_row_size_in * 3

def ref_files():
    files = [f for f in listdir(base_url) if isfile(join(base_url, f))]
    return files


def get_colors():
    colors = {}
    for f in ref_files():
        loc = join(base_url, f)
        try:
            with Image.open(loc) as im:
                r = list(im.getdata(0))
                g = list(im.getdata(1))
                b = list(im.getdata(2))
                r_avg = math.floor(sum(r) / len(r))
                g_avg = math.floor(sum(g) / len(g))
                b_avg = math.floor(sum(b) / len(b))
                r_hex = str(hex(r_avg).capitalize()[2:])
                g_hex = str(hex(g_avg).capitalize()[2:])
                b_hex = str(hex(b_avg).capitalize()[2:])
                hex_color = "#{}{}{}".format(r_hex, g_hex, b_hex)
                imSize = len(list(im.getdata()))
                colors[f] = {
                    "hex_color": hex_color,
                    "rgb": [math.floor(sum(x) / len(x)) for x in [r,g,b]],
                    "data": [x/imSize for x in list(im.histogram())]
                }
        except:
            continue
    return colors

def get_valid_data(data_list, variance):
    result = [data_list[i] for i in range(len(data_list)) if variance[i] != 0]
    return result

def get_recommended_order(**kwargs):
    colors = get_colors()

    first: str = kwargs.get('first', random.choice(list(colors.keys())))
    if (first not in list(colors.keys())):
        first = random.choice(list(colors.keys()))

    ordered = [first]
    color_list = list(colors.keys())
    vectors = [x["data"] for x in colors.values()]

    sz = len(vectors[0])
    sum_vec = [0] * sz
    for vec in vectors:
        for i in range(len(vec)):
            sum_vec[i] += vec[i]

    sparse_variance = [x /len(vectors) for x in sum_vec]
    variance = get_valid_data(sparse_variance, sparse_variance)[:-1]

    variance = [x/max(variance) for x in variance]
    print(len(variance))
    for i in range(len(colors.keys())):
        random.shuffle(color_list)
        current = ordered[-1]
        data: list[float] = get_valid_data(colors[current]["data"], sparse_variance)[:-1]


        match = ""
        diff_color= float('inf')

        for c in color_list:
            if c not in ordered:
                test_data: list[float] = get_valid_data(colors[c]["data"], sparse_variance)[:-1]
                dist = distance.canberra(data, test_data, variance)
                # print(dist)
                
                if dist < diff_color:
                        match = c
                        diff_color = dist

        if (match != ""):
            ordered.append(match)

    return ordered

def draw_row(draw, color_list, current_height, row_height):
    colors = get_colors()
    count = 0
    strip_width_px =  (strip_width_in - (2 * seam_width_in)) * in_to_px
    for c in color_list:
        color = colors[c]
        upper_left_x = (count) * strip_width_px
        upper_left_y = current_height
        lower_right_x = (count+1) *  strip_width_px
        lower_right_y = current_height + row_height
        fill_val = (color["rgb"][0], color["rgb"][1],color["rgb"][2])
        draw.rectangle(xy = (upper_left_x, upper_left_y, lower_right_x, lower_right_y), 
                fill = (fill_val), 
                outline = (fill_val), 
                width = 0) 
        count += 1

def calculate_cuts(height):
    current_height = 0
    row_height_in = (max_row_size_in + min_row_size_in) / 2
    prob = .5

    cut_guide = []
    while current_height < height:
        cut = {"direction": "none", "amount": min_row_size_in}
        direction = random.random()
        size_change = random.random()
        size_change_amount = .25
        
        if current_height != 0:
            if direction <= prob:
                cut["direction"] = "left"
            else: 
                cut["direction"] = "right"

        if size_change < .4:
            if row_height_in > min_row_size_in + size_change_amount:
                row_height_in -= size_change_amount
        elif size_change < .6:
            pass
        else:
            if row_height_in < max_row_size_in - size_change_amount:
                row_height_in += size_change_amount
        
        cut["amount"] = row_height_in


        row_height = row_height_in * in_to_px
        if (height - (current_height + row_height)) < (seam_width_in * 3 * in_to_px):
            row_height = height - current_height
            cut["amount"] = "remainder"

        current_height += row_height
        cut_guide.append(cut)

    return cut_guide




colors = get_colors()
color_list = get_recommended_order(first="Blue Speckle.png")
strip_count = len(color_list)
width = math.floor(strip_count * (strip_width_in - (2 * seam_width_in)) * in_to_px)
height = height_in * in_to_px

# Creating a Draw object 
cuts = calculate_cuts(height)
seam_height = (len(cuts) - 1) * (2 * seam_width_in)
with open("cut_guide.txt", "w") as cut_file:
    write_color_list = [x.split(".")[0] for x in color_list]
    cut_file.write("Final quilt size {}in x {}in\n".format(strip_count * (strip_width_in - (2 * seam_width_in)), height_in - seam_height))
    cut_file.write("Using {} stripes of length {}in\n".format(strip_count, height_in))
    cut_file.write("Initial colors:\n\t {}\n".format(", ".join(write_color_list)))
    for ind in range(len(cuts)):
        cut = cuts[ind]

        items = deque(write_color_list)
        if cut["direction"] == "left":
            #Go left
            items.rotate(-1)
            write_color_list = list(items)
        elif cut["direction"] == "right": 
            #go right
            items.rotate(1)
            write_color_list = list(items)

        cut_file.write("{}.) Shift {} - starting color {} \n\trow height: {}\n".format(ind, cut["direction"], write_color_list[0], cut["amount"]))

true_height = math.floor((height_in - seam_height) * in_to_px)
img= Image.new(mode="RGB", size=(width, true_height))
draw = ImageDraw.Draw(img) 

current_height = 0
for cut in cuts:
    seam_allowance = (2 * seam_width_in)
    if current_height == 0:
        seam_allowance = seam_width_in

    if (cut["amount"] == "remainder"):
        if (true_height - current_height) > 0:
            row_height = true_height - current_height
        else:
            row_height = 0
    else:
        row_height = (cut["amount"] - seam_allowance) * in_to_px

    items = deque(color_list)
    if cut["direction"] == "left":
        #Go left
        items.rotate(-1)
        color_list = list(items)
    elif cut["direction"] == "right": 
        #go right
        items.rotate(1)
        color_list = list(items)

    draw_row(draw, color_list, current_height, math.floor(row_height))
    current_height += row_height

img.show()
img.save(output_name)


