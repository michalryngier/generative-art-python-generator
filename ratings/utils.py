import numpy as np
from skimage import color
from math import log10


def fractal_dimension(image, threshold=0.9):
    # Function to calculate the fractal dimension using the box-counting method
    def box_count(binary_image, box_size):
        count = 0
        for i in range(0, binary_image.shape[0], box_size):
            for j in range(0, binary_image.shape[1], box_size):
                if np.sum(binary_image[i:i + box_size, j:j + box_size]) > 0:
                    count += 1
        return count

    # Remove the alpha channel if present
    if image.shape[2] == 4:
        image = image[:, :, :3]

    # Convert to grayscale
    gray_image = color.rgb2gray(image)

    # Binarize the image based on the threshold

    binary_image = gray_image > threshold

    # Initialize variables
    sizes = 2 ** np.arange(1, 10)
    counts = []

    # Calculate box count for different box sizes
    for size in sizes:
        counts.append(box_count(binary_image, size))

    # Fit a line to the data points (log-log scale)
    coeffs = np.polyfit(np.log(sizes), np.log(counts), 1)

    # Return the fractal dimension (slope of the line)
    return -coeffs[0], sizes, counts


def benford(n):
    return log10(n + 1) - log10(n)
