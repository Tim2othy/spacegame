import numpy as np
distance = lambda pos1, pos2: np.sqrt(np.sum((np.array(pos1) - np.array(pos2))**2))

vec_add    = lambda v1, v2: np.array(v1) + np.array(v2)
vec_scale  = lambda v, scalar: np.array(v) * scalar

sign = lambda x: (1 if x > 0 else -1 if x < 0 else 0)

