import ctypes
import random
import time

interpolate = ctypes.CDLL('./interpolate/interpolate.so')

# Define the C++ function signature
interpolate_function = interpolate.interpolate
interpolate_function.argtypes = [ctypes.c_double, ctypes.POINTER(ctypes.c_double), ctypes.c_int]
interpolate_function.restype = ctypes.POINTER(ctypes.c_double)

# Call the C++ function
t = 0.5  # Replace with your desired interpolation parameter
points = [[random.randint(0, 100), random.randint(0, 1000)] for _ in range(22)]
size = len(points)

# Convert the list of points to a C-style array
c_points = (ctypes.c_double * (2 * size))(*[item for sublist in points for item in sublist])

# Call the C++ function
start = time.time()
result_pointer = interpolate_function(t, c_points, size)
print(time.time() - start)


# Convert the result from double* to a Python list
result_list = [result_pointer[i] for i in range(2)]
print(result_list)
