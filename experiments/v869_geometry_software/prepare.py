"""Make fixed model-free known-map fixtures and saved-state witness; freeze before ROS."""
import gzip,hashlib,json,math,time
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;O=R/'runs/v869_geometry_software'
def dump(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
def ranges(known,body):
 out=[];origin=np.asarray(body[:2],float)
 for theta in body[2]+np.arange(32)*2*math.pi/32:
  direction=np.array([math.cos(theta),math.sin(theta)]);best=3.
  for x,y,hx,hy in known['known_rectangles']:
   lo=np.array([x-hx,y-hy]);hi=np.array([x+hx,y+hy]);near=0.;far=3.
   for j in range(2):
    if abs(direction[j])<1e-12:
     if origin[j]<lo[j]or origin[j]>hi[j]:far=-1.;break
    else:
     a,b=sorted([(lo[j]-origin[j])/direction[j],(hi[j]-origin[j])/direction[j]]);near=max(near,a);far=min(far,b)
   if near<=far:best=min(best,near)
  for x,y,rad in known['known_circles']:
   d=origin-[x,y];b=float(d@direction);det=b*b-float(d@d)+rad*rad
   if det>=0:
    hit=-b-math.sqrt(det)
    if hit>=0:best=min(best,hit)
  out.append(best)
 return out

def main():
 assert not(O/'FIXTURES.json').exists();tasks=json.load(open(R/'experiments/v867_margin_navigation/TASKS.json'));known=json.load(open(R/'experiments/v855_renewal_worker/KNOWN_FIELD.json'));cases=json.load(open(R/'experiments/v855_renewal_worker/SCENE_CASES.json'));fixtures={}
 for case in cases:
  name={'WEST_EAST':'we','NORTH_SOUTH':'ns','EAST_WEST':'ew'}[case['id']];task=next(x for x in tasks if x['case_id']==case['id']and x['stage']=='static_main');body=[*case['start_xy'],case['yaw'],0.,0.];fixtures['fine_'+name]=dict(task=task,body=body,scan=dict(native_tick=0,time=0.,ranges=ranges(known,body)),source='ANALYTICAL_KNOWN_MAP_SOFTWARE_FIXTURE_NO_PHYSICAL_SENSOR',config='fine.yaml')
 p=R/'runs/v858_nav2_verified/v864_static/main_ns';a=np.load(p/'physics/NATIVE_TRACE.npz');q=a['qpos'][-1];v=a['qvel'][-1];yaw=math.atan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2));body=[*q[:2],yaw,v[0]*math.cos(yaw)+v[1]*math.sin(yaw),v[5]];s=json.loads(gzip.decompress((p/'physics/SENSORS.json.gz').read_bytes()))[-1];task=json.load(open(p/'TASK.json'))
 for name,config in [('fine_ns_checkpoint','fine.yaml'),('unsmoothed_ns_checkpoint','fine_unsmoothed.yaml')]:fixtures[name]=dict(task=task,body=body,scan={k:s[k]for k in ['native_tick','time','ranges']},source='ACTUAL_SAVED_V864_TERMINAL_ODOMETRY_AND_RANGE_OBSERVATION',config=config)
 dump(O/'FIXTURES.json',fixtures)
 base=json.load(open(R/'experiments/v867_margin_navigation/SOURCE_FREEZE.json'))['files'];files=dict(base)
 for p in C.iterdir():
  if p.is_file()and p.name!='SOURCE_FREEZE.json':files[str(p.relative_to(R))]=hashlib.sha256(p.read_bytes()).hexdigest()
 for p in [O/'FIXTURES.json']:
  files[str(p.relative_to(R))]=hashlib.sha256(p.read_bytes()).hexdigest()
 dump(C/'SOURCE_FREEZE.json',dict(models_authorized=False,files=files))
 now=time.time();dump(O/'SOFTWARE_WINDOW.json',dict(started_unix=now,deadline_unix=now+600,models_authorized=False,maximum_probes=5,task_names=list(fixtures)))
 print('FIXTURES_FROZEN',len(fixtures),'MODEL_INITIALIZATIONS=0')
if __name__=='__main__':main()
