from curses.ascii import SI
from PIL import Image
from collections import Counter
import numpy as np

old_x = 134
old_y = 158

new_x = 34
new_y = 40
name = "images"


def most_common_color(pixels):
    """Find the most common pixel color."""
    pixels = [tuple(pixel) for pixel in pixels]  # Convert to tuples (RGB)
    return Counter(pixels).most_common(1)[0][0]  # Most common color


def downscale_image(input_path, output_path):
    """Downscale image to new_x * new_y using the most common color in each grid."""
    original = Image.open(input_path)
    original = original.resize((old_x, old_y))
    grid_size = old_x // new_x  # Grid size for SIZExSIZE

    result_image = Image.new("RGB", (new_x, new_y))
    for i in range(new_x):
        for j in range(new_y):
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

    result_image.save(output_path)
    print(f"Image saved to {output_path}")


# Usage example
downscale_image(name + ".png", name + "_in_" + str(new_x) + ".png")
