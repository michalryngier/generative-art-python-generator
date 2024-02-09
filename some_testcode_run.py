import ctypes
import random
import time

import numpy as np

interpolate = ctypes.CDLL('./interpolate/interpolate.so')

# Define the C++ function signature
interpolate_function = interpolate.interpolate
interpolate_function.argtypes = [ctypes.c_double, ctypes.POINTER(ctypes.c_double), ctypes.c_int]
interpolate_function.restype = ctypes.POINTER(ctypes.c_double)

# Call the C++ function
points = [[random.randint(1, 5), random.randint(0, 5)] for _ in range(100000)]
size = len(points)

# Convert the list of points to a C-style array
c_points = (ctypes.c_double * (2 * size))(*[item for sublist in points for item in sublist])

# Call the C++ function
results = []
arrange = np.arange(0, 1 + 0.1, 0.1)
start = time.time()
result_pointer = interpolate_function(0.5, c_points, size)
print(f"time: {time.time() - start}")
result_list = [result_pointer[i] for i in range(2)]


# Convert the result from double* to a Python list
print(results)
