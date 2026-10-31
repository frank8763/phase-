"""Offline observed-map necessary-connectivity diagnostic, no hidden geometry."""
import os,json,time
from pathlib import Path
from collections import deque
import numpy as np
from factory import initialize
from exact_footprint import build
from instrumentation import dump
root=Path(os.environ['PHASE_RUNS'])/'v648_static_unknown';out=root/'truth_connectivity_probe_16';out.mkdir();begin=time.monotonic();c,native=initialize(91000002,out/'paired')
src=root/'static_pilot_15_single_seed2/paired/memory/planning_0489.json';d=json.loads(src.read_text());w=d['causal_input'];w['sensor_points']=[]
protocol=json.loads((root/'static_pilot_15_single_seed2/paired/STATIC_PROTOCOL.json').read_text());w['circles']=w['circles']+[[*u['xy'],u['radius']]for u in protocol['physical_unknown_obstacles']]
field=build(c['F'],w)
# Inspect the entire central aperture, with a yaw choice at every center cell.
axis=np.arange(-1.5,2.501,.05);ay=np.arange(-1.5,2.501,.05);xx,yy=np.meshgrid(axis,ay,indexing='ij');positions=np.c_[xx.ravel(),yy.ravel()];yaw=np.arange(72)*2*np.pi/72
best=[];best_yaw=[]
for i in range(0,len(positions),32):
 xy=positions[i:i+32];p=np.c_[np.repeat(xy,72,axis=0),np.tile(yaw,len(xy))];v=field.pose_values(p).reshape(-1,72);best.extend(v.max(1));best_yaw.extend(v.argmax(1))
best=np.array(best).reshape(xx.shape)
rows=[]
for floor in [.15,.15-.05/2**.5-(2*np.pi/72/2)*np.linalg.norm(field.half)]:
 free=best>=floor;start=tuple(np.rint((np.array(d['pose'][:2])+1.5)/.05).astype(int));seen=np.zeros_like(free);seen[start]=True;q=deque([start])
 while q:
  x,y=q.popleft()
  for dx,dy in [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]:
   a,b=x+dx,y+dy
   if 0<=a<len(axis)and 0<=b<len(ay)and free[a,b]and not seen[a,b]:seen[a,b]=True;q.append((a,b))
 rows.append({'floor_m':floor,'connected_to_left_boundary':bool(np.any(seen[0])),'connected_to_bottom_boundary':bool(np.any(seen[:,0])),'visited_cells':int(seen.sum())})
dump(c['out']/'connectivity.json',{'input':str(src),'rows':rows,'x':axis,'y':ay,'best_clearance':best,'best_yaw_index':np.array(best_yaw).reshape(xx.shape),'actual_navigation_steps':0,'elapsed_s':time.monotonic()-begin,'scope':'EVALUATION TRUTH ONLY; never planner input. Orientation-relaxed connectivity, positive is not SE2/dynamic feasibility'})
print(rows,flush=True)
