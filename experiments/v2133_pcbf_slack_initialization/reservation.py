from pathlib import Path
import json,subprocess
R=Path(__file__).resolve().parents[2];S=R/'runs'/Path(__file__).resolve().parent.name
JOINT=16095019008;LIMIT=16106127360
# V2131 frozen allprior + futureclosed32 + prep8 + metadata8 + parallel2, plus this4MiB source/math/transport subgrant.
UPPER=15099584512+(32+8+8+2+4)*1024**2

def admission():
 actual=int(subprocess.check_output(['du','-sx','-B1',str(R/'runs')],timeout=20).split()[0]);assert actual<=UPPER and UPPER+(32+512)*1024**2<=JOINT<LIMIT
 return dict(passed=True,joint_peak_bytes=JOINT,actual_allruns_bytes=actual,allruns_upper_bytes=UPPER,new_math_component_subgrant_bytes=4*1024**2,models=0)
def transport_current_upper():return UPPER
