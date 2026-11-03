"""Reconstruct original first65 packets before any new model initialization."""
import gzip,json,math,sys
from pathlib import Path
from types import SimpleNamespace
import numpy as np
repo=Path(__file__).resolve().parents[2];own=Path(__file__).parent
sys.path.insert(1,str(repo/'runtime/mk-mini/training/phase14_lidar_depth_nav/envs'));from sensor_model import packet
pair=repo/'runs/v721_recursive_unseen_navigation/main01/paired';read=lambda p:json.loads(p.read_text());protocol=read(pair/'STATIC_PROTOCOL.json');config=read(pair/'DYNAMIC_PROTOCOL.json');initial=read(pair/'INITIALIZATION_PROVENANCE.json')['noise_call_state_after_bootstrap']
motion=SimpleNamespace(xy=lambda t:np.asarray(config['anchor_xy'])+np.asarray(config['axis_xy'])*config['amplitude_m']*math.sin(t*config['omega_rad_s']+config['phase_rad']))
with gzip.open(pair/'geometry_memory/sensor_packets.jsonl.gz','rt')as f:packets=[json.loads(s)for s in f][:65]
errors=[]
for p in packets:
 q=packet(p['xy'],p['yaw'],p['time'],p['step'],protocol,motion,initial)
 errors.append(max(float(np.max(abs(np.asarray(q[tag])-p[tag])))for tag in ['lidar','depth']))
root=repo/'runs/v728_sensor_calibration';root.mkdir(exist_ok=False);result=dict(status='ORIGINAL_65_RAW_NOISY_PACKETS_EXACT'if max(errors)==0 else'FAIL',packets=len(packets),maximum_error=max(errors),new_initializations=0,new_integrations=0)
(root/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));assert result['status']!='FAIL'
