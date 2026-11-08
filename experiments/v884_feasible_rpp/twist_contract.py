"""Final smoothed command must remain representable; never silently change a checked Twist."""
import math
MAX_CURVATURE=math.tan(.42722137342572125)/.6
def require_representable(v,w):
    if not math.isfinite(v)or not math.isfinite(w):raise ValueError('NONFINITE_FINAL_TWIST')
    if abs(v)<.005:
        if abs(w)>1e-6:raise ValueError('IN_PLACE_ROTATION_NOT_NATIVE_REPRESENTABLE')
    elif abs(w)>abs(v)*MAX_CURVATURE+1e-9:raise ValueError('FINAL_TWIST_OUTSIDE_NATIVE_CURVATURE')
    return True
