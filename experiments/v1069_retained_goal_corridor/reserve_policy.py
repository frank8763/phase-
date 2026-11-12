"""Remove the added 20mm advisory stop threshold; preserve the original gate.

This pure policy consumes the unchanged complete-stop prediction. It grants
no control without that original predictor, geometry, and body/control checks.
"""
import math
REQUIRED=.24353421020226934
def admit_preview(proof):
 current=float(proof['current_stop_minimum_raw_m']);future=float(proof['preview_stop_minimum_raw_m']);required=float(proof['required_raw_m'])
 assert required==REQUIRED,'ORIGINAL_RAW_GATE_CHANGED'
 assert math.isfinite(current)and math.isfinite(future),'NONFINITE_PREVIEW'
 extra=min(.001,max(0.,current-required)/2)
 return bool(proof['current_stop_passed']and current>=required and future>=required+extra)
