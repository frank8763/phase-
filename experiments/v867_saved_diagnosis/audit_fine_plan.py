"""Input-only global/reference-to-RPP arc screening against unchanged local footprint and known map."""
import json,math,sys
from pathlib import Path
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[2];O=R/'runs/v869_geometry_software';sys.path.insert(0,str(R/'experiments/v864_diagnosis'))
from snapshot_geometry import dense,field
from collision_witness import cost
sys.path.insert(0,str(R/'experiments/v791_coherent_global_reference'));from exact_footprint import pose_values

def carrot(local,L):
 k=next((i for i,x in enumerate(local)if np.linalg.norm(x)>=L),len(local)-1);p=local[k]
 if k>0:
  a=local[k-1];d=local[k]-a;roots=np.roots([d@d,2*a@d,a@a-L*L]);ts=[float(x.real)for x in roots if abs(x.imag)<1e-9 and 0<=x.real<=1]
  if ts:p=a+max(ts)*d
 return p

def main():
 name=sys.argv[1];out=O/name;plans=json.loads((out/'PLANS.json').read_text());assert plans;path=np.asarray(plans[0]['path']);samples=dense(path.tolist());setup=json.loads((R/'runs/v858_nav2_verified/v864_static/main_ns/physics/SETUP.json').read_text());full=field(setup['known']);padded=field(setup['known'],.15)
 conf=json.loads((R/'experiments/v869_geometry_software/field.yaml').read_text());pix=np.flipud(np.asarray(Image.open(conf['image'])));grid=np.where((255-pix)/255.>conf['occupied_thresh'],254,0);row=dict(value=dict(data=grid.ravel().tolist(),width=grid.shape[1],height=grid.shape[0],resolution=conf['resolution'],origin=conf['origin'][:2]))
 nodecost=[cost(p,.15,row)['cost']for p in samples];arcposes=[];arc_details=[]
 for index in range(len(path)-1):
  pose=path[index];c,s=math.cos(pose[2]),math.sin(pose[2]);local=(path[index:,:2]-pose[:2])@np.array([[c,-s],[s,c]]);L=.6
  for j in range(1,len(local)-1):
   if np.dot(local[j]-local[j-1],local[j+1]-local[j])<0:L=min(L,float(np.linalg.norm(local[j])));break
  pp=carrot(local,L);norm=float(pp@pp);curv=0. if norm<=.001 else float(2*pp[1]/norm);sign=1 if pp[0]>=0 else-1
  for speed in [.08,.20]:
   distance=sign*np.linspace(0,min(1.5*speed,float(np.linalg.norm(pp))),31);theta=pose[2]+curv*distance
   x=pose[0]+(np.sin(theta)-s)/curv if abs(curv)>1e-12 else pose[0]+distance*c;y=pose[1]-(np.cos(theta)-c)/curv if abs(curv)>1e-12 else pose[1]+distance*s
   arc=np.c_[x,y,theta];clear=pose_values(padded,arc);arcposes.extend(arc.tolist());arc_details.append(dict(path_node=index,speed=speed,curvature=curv,minimum_padded_geometric_separation_m=float(np.min(clear))))
 arcposes=np.asarray(arcposes);arc_geometry=pose_values(padded,arcposes);arc_costs=[cost(p,.15,row)['cost']for p in arcposes];bad=[x for x in arc_details if x['minimum_padded_geometric_separation_m']<=0]
 summary=dict(scope='Zero-model ideal-reference geometric/raster screening only; not actual controller output, online costmap, actuator prediction or closed-loop navigation',model_initializations=0,model_integrations=0,nodes=len(path),dense_samples=len(samples),minimum_full_body_known_geometric_clearance_m=float(np.min(pose_values(full,samples))),minimum_local_padded_reference_separation_m=float(np.min(pose_values(padded,samples))),reference_lethal_raster_samples=sum(x>=254 for x in nodecost),ideal_rpp_arc_sample_count=len(arcposes),minimum_local_padded_arc_separation_m=float(np.min(arc_geometry)),arc_lethal_raster_samples=sum(x>=254 for x in arc_costs),worst_arc_details=sorted(arc_details,key=lambda x:x['minimum_padded_geometric_separation_m'])[:5],candidate_screen_passed=bool(np.min(pose_values(padded,samples))>0 and not any(x>=254 for x in nodecost)and np.min(arc_geometry)>0 and not any(x>=254 for x in arc_costs)),held_out_or_dynamic_qualification=False)
 (out/'GEOMETRY_AUDIT.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
