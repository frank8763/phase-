"""Independent tiny-step midpoint response geometry; no physical model API."""
import importlib.util,math
from pathlib import Path
import numpy as np
from state_reference import GAIN,RATE_COUPLING,VIRTUAL_RATE,REFERENCE_SPEED,MAX_DELTA
R=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location('v997_original_independent_polygon',R/'experiments/v977_state_consistent_recovery/saved_qualification.py')
old=importlib.util.module_from_spec(s);s.loader.exec_module(old)
independently_check_geometry=old.independently_check_geometry

def reconstruct(initial,targets,grid=.0005):
    rows=[np.asarray(initial,float)];n=round(.1/grid);slope=VIRTUAL_RATE/REFERENCE_SPEED
    for target in targets:
        for _ in range(n):
            x,y,a,d=rows[-1];next_d=float(np.clip(target,d-slope*grid,d+slope*grid));mid=(d+next_d)/2
            da=GAIN*math.tan(mid)/.6*grid+RATE_COUPLING*(next_d-d)
            rows.append(np.array([x+grid*math.cos(a+da/2),y+grid*math.sin(a+da/2),a+da,next_d]))
    return np.array(rows)
