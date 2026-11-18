"""Read saved whole sources only; locate native clearance failures without dynamics."""
import sys,json,hashlib
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1136_route_clock_restore'
sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
apply();sys.path.insert(0,str(R/'experiments/v1129_recording_entry_preparation'));from result_io import dump
sys.path.insert(0,str(R/'experiments/v1135_causal_batch'));from geometry import Geometry,REQUIRED,pg
import numpy as np

def main():
 x=json.loads((R/'runs/v858_nav2_verified/v1122/r00_m15_b8_main_WEST_EAST/COUPLED_ENTRY.json').read_text());z=np.load(R/'runs/v1135_causal_batch/domain/JOINT_TABLE.npz');g=Geometry(x,{k:z[k]for k in ['bounds','centers']});reports=[]
 for name in ['saved_v80','cold_v80']:
  src=R/'runs/v1135_causal_batch'/name;j=json.loads((src/'OPTIMIZATION.json').read_text());ss=np.load(src/'SELECTED_SOURCE.npz')['states'];a,b=g.components(ss[:,:3],np.arange(len(ss)));k=int(np.argmin(b));cursor=0;section=[]
  for i,row in enumerate(j['rows']):
   end=cursor+int(row[2]);section.append({'row':i,'speed':row[1],'mode':row[3],'begin':cursor,'end':end,'min_static':float(a[cursor:end+1].min()),'min_dynamic':float(b[cursor:end+1].min()),'end_pose':ss[end,:3].tolist()});cursor=end
  local=np.arange(len(g.centers));poses=np.repeat(ss[k:k+1,:3],len(local),axis=0);ticks=np.maximum(0.,(g.centers-g.original.start)%g.period)/.01;_,allphase=g.components(poses,ticks)
  phase=(g.original.start+.01*k)%g.period;bounds=g.upper(np.array([k]))[0];poly=pg.polygon(bounds)
  reports.append({'profile':name,'minimum_native':k,'minimum_pose':ss[k,:3].tolist(),'min_dynamic':float(b[k]),'static_at_dynamic_min':float(a[k]),'fixed_pose_best_dynamic_over_full_cycle':float(allphase.max()),'phase_outer_polygon':poly.tolist(),'rows':section})
 task=json.loads((R/'experiments/v1135_causal_batch/TASK.json').read_text());path=json.loads((R/task['path']).read_text());answer={'reports':reports,'initial_pose':x['packet'].get('body_xy'), 'known_rectangles':x['setup']['known']['known_rectangles'],'guide':path,'required':REQUIRED,'models':0,'analytical_dynamics_integrations':0,'physical_integrations':0};dump(O/'SAVED_FAILURE_DIAGNOSIS.json',answer)
 print(json.dumps({'reports':[{k:v for k,v in r.items()if k!='phase_outer_polygon'}for r in reports],'guide':path,'rectangles':answer['known_rectangles']},ensure_ascii=False))
if __name__=='__main__':main()
