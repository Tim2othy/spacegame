from collections import Counter

import numpy as np
from PIL import Image

# If you want to downscale an image to a smaller size, you can use this file
# The png has to be square, set old_size and new_size to the desired values
old_size = 741

new_size = 247
name = "profile_ship"


def most_common_color(pixels):
    """Find the most common pixel color."""
    pixels = [tuple(pixel) for pixel in pixels]  # Convert to tuples (RGB)
    return Counter(pixels).most_common(1)[0][0]  # Most common color


def downscale_image(input_path, output_path):
    """Downscale image to new_size * new_size using the most common color in each grid."""
    original = Image.open("assets/" + input_path)
    original = original.resize((old_size, old_size))
    grid_size = old_size // new_size  # Grid size for SIZExSIZE

    result_image = Image.new("RGB", (new_size, new_size))
    for i in range(new_size):
        for j in range(new_size):
            # Crop the region for the current grid
            left, upper = j * grid_size, i * grid_size
            right, lower = left + grid_size, upper + grid_size
            grid = original.crop((left, upper, right, lower))

            # Ensure the grid is in RGB mode and get the pixels
            grid = grid.convert("RGB")
            pixels = np.array(grid).reshape(-1, 3)  # Flatten pixels
            common_color = most_common_color(pixels)

            # Set the color in the result image
            result_image.putpixel((j, i), common_color)

    result_image.save("assets/" + output_path)
    print(f"Image saved to {output_path}")


# Usage example
downscale_image(name + ".png", name + "_in_" + str(new_size) + ".png")
