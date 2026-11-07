"""Conservative historical certificates, time anchored to avoid repeated rounding loss."""
import numpy as np
from recursive_domain import HALF_DIAGONAL,SLACK,SPEED
SCALE=1000000.
def update_height(domain):
 fresh=np.maximum(0.,domain.distance-HALF_DIAGONAL-SLACK)
 raw=(fresh+SPEED*domain.time)*SCALE
 assert np.max(raw)<np.iinfo(np.uint32).max,'HEIGHT_RANGE_OVERFLOW'
 # Zero carries no positive certificate. Flooring once per new observation
 # loses <1 micrometre. Old integer certificates are never re-quantized.
 candidate=np.where(fresh>0.,np.floor(raw),0.).astype('<u4')
 domain.history_height=candidate if not hasattr(domain,'history_height')else np.maximum(domain.history_height,candidate)
