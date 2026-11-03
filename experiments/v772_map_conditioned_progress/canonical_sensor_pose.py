"""Exact frozen public pose convention; no simulator or future information."""
import math
import numpy as np
def sensor_pose(q):
    q=np.asarray(q);yaw=math.atan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2))
    return q[:2].astype(np.float32),yaw
