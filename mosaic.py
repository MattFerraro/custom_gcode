# import skimage as ski
import imageio.v3 as iio
from skimage.color import rgb2gray
import math


def main():
    # inputs
    filename = "dali.jpg"
    output_width = 12.93  # inches
    x_samples = 13
    x_dist = output_width / (x_samples + 1)
    v_bit_half_angle = 30  # degrees
    safe_retract_z = 0.5  # inches -- this assumes we are zeroed on to the top of the material!
    max_depth = 0.4  # inches

    original = iio.imread(filename)
    grayscale = rgb2gray(original)
    print(grayscale.shape)
    image_height, image_width = grayscale.shape

    aspect_ratio = image_width / image_height
    print(f"Aspect ratio: {aspect_ratio}")

    # outputs
    output_height = output_width / aspect_ratio
    print(f"Physical image will be {output_width} by {output_height} inches")

    y_samples = int(x_samples / aspect_ratio)
    y_dist = output_height / (y_samples + 1)
    print(f"Image will be {x_samples} holes wide by {y_samples} holes tall")

    commands = []

    # spindle start (implied 16,000 RPM)
    commands.append("C6")

    # set to absolute position mode
    commands.append("SA")

    # move to origin but at safe z height
    commands.append(f"J3 0,0,{safe_retract_z}")

    for x in range(x_samples):
        for y in range(y_samples):
            print(f"\nNow at hole X: {x}, Y: {y}")
            x_pos = x_dist * (x + 0.5)
            y_pos = y_dist * (y + 0.5)

            print(f"Moving to {x_pos}, {y_pos}")
            commands.append(f"J3 {x_pos},{y_pos},{safe_retract_z}")
            x_frac = x_pos / output_width
            y_frac = y_pos / output_height

            x_pixel = int(x_frac * image_width)
            y_pixel = int(y_frac * image_height)

            intensity = grayscale[y_pixel, x_pixel]
            # intensity is 0->255 but depth is 0->max_depth
            # and brightness of the hole goes up as depth^2 not linearly with depth
            intensity = intensity / 255
            depth = math.sqrt(intensity) * max_depth

            z_pos = -depth
            commands.append(f"MZ {z_pos}")
            commands.append(f"JZ {safe_retract_z}")

    # spindle stop
    commands.append("C7")

    with open("output.nc", "w") as f:
        f.write("\n".join(commands))


if __name__ == "__main__":
    main()
