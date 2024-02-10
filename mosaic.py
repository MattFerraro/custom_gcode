import numpy as np
# import skimage as ski
import imageio.v3 as iio
from skimage.color import rgb2gray, gray2rgb
from skimage.draw import disk
import math
DIALECT = "shopbot"
# DIALECT = "gcode"


def main():
    # inputs
    filename = "dali.jpg"
    output_width = 12.93  # inches
    x_samples = 50
    x_dist = output_width / (x_samples)
    v_bit_half_angle = 45  # degrees
    safe_retract_z = 0.5  # inches -- this assumes we are zeroed on to the top of the material!
    max_depth = 0.25  # inches

    original = iio.imread(filename)
    grayscale = rgb2gray(original)
    print(grayscale.shape)

    simulation = grayscale.copy() * 0.0

    image_height, image_width = grayscale.shape
    pixels_per_inch = image_width / output_width
    print("Pixels per inch: ", pixels_per_inch)

    aspect_ratio = image_width / image_height
    print(f"Aspect ratio: {aspect_ratio}")

    # outputs
    output_height = output_width / aspect_ratio
    print(f"Physical image will be {output_width} by {output_height} inches")

    y_samples = int(x_samples / aspect_ratio)
    y_dist = output_height / (y_samples)
    print(f"Image will be {x_samples} holes wide by {y_samples} holes tall")

    commands = []

    # spindle start (implied 16,000 RPM)
    commands.append("C6")

    # set to absolute position mode
    commands.append(absolute_mode())

    # move to origin but at safe z height
    # commands.append(f"J3 0,0,{safe_retract_z}")
    commands.append(move_to(0, 0, safe_retract_z))

    radius = max_depth * math.tan(math.radians(v_bit_half_angle)) * 2.0
    print("Max radius in inches: ", radius)
    radius_in_pixels = radius * pixels_per_inch
    print("Max radius in pixels: ", radius_in_pixels)

    for x in range(x_samples):
        for y in range(y_samples):
            # print(f"\nNow at hole X: {x}, Y: {y}")
            x_pos = x_dist * (x + 0.5)
            y_pos = y_dist * (y + 0.5)

            # print(f"Moving to {x_pos}, {y_pos}")
            # move to the hole location at a safe z height
            # commands.append(f"J3 {x_pos},{y_pos},{safe_retract_z}")
            commands.append(jog_to(x_pos, y_pos, safe_retract_z))
            x_frac = x_pos / output_width
            y_frac = y_pos / output_height

            x_pixel = int(x_frac * image_width)
            y_pixel = int(y_frac * image_height)

            intensity = grayscale[y_pixel, x_pixel]
            # intensity is 0->255 but depth is 0->max_depth
            # and brightness of the hole goes up as depth^2 not linearly with depth
            # intensity = intensity
            depth = math.sqrt(intensity) * max_depth - 0.1

            # simulation[y_pixel, x_pixel] = 1
            radius = depth * math.tan(math.radians(v_bit_half_angle))
            radius_in_pixels = radius * pixels_per_inch
            # print(
            #     f"intensity: {intensity} depth: {depth} radius: {radius} radius_in_pixels: {radius_in_pixels}")

            rr, cc = disk((y_pixel, x_pixel), radius_in_pixels,
                          shape=(image_height, image_width))
            simulation[rr, cc] = 1

            z_pos = -depth
            # plunge to depth
            # commands.append(f"MZ {z_pos}")
            # commands.append(move_z(z_pos))
            commands.append(move_to(x_pos, y_pos, z_pos))
            # retract to a safe height
            # commands.append(f"JZ {safe_retract_z}")
            # commands.append(move_z(safe_retract_z))
            commands.append(jog_to(x_pos, y_pos, safe_retract_z))

    # spindle stop
    commands.append("C7")

    with open("output.nc", "w") as f:
        f.write("\n".join(commands))

    simulation_rgb = gray2rgb(simulation) * 255
    iio.imwrite("simulation.png", simulation_rgb.astype(np.uint8))


def move_to(x, y, z):
    if DIALECT == "shopbot":
        return f"M3 {x},{y},{z}"
    elif DIALECT == "gcode":
        return f"G01 X{x} Y{y} Z{z}"


def jog_to(x, y, z):
    if DIALECT == "shopbot":
        return f"J3 {x},{y},{z}"
    elif DIALECT == "gcode":
        return f"G00 X{x} Y{y} Z{z}"


def move_z(z):
    if DIALECT == "shopbot":
        return f"MZ {z}"
    elif DIALECT == "gcode":
        return f"G01 Z{z}"


def jog_z(z):
    if DIALECT == "shopbot":
        return f"JZ {z}"
    elif DIALECT == "gcode":
        return f"G00 Z{z}"


def absolute_mode():
    if DIALECT == "shopbot":
        return "SA"
    elif DIALECT == "gcode":
        return "G90"


if __name__ == "__main__":
    main()
