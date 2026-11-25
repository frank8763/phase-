"""Bounded independent CPU4/6 map/information/numerical comparisons; no model."""
from context import R,C,O,read,sha,put,load
import concurrent.futures,copy,math,os,subprocess,time

def map_check():
 os.sched_setaffinity(0,{6});import numpy as np
 from current_map import cost,inflate,Frontend,PARAMS,PUBLIC,rear,inscribed_radius
 rng=np.random.default_rng(1966);cfg=read(PARAMS)['local_costmap']['local_costmap']['ros__parameters'];foot=__import__('json').loads(cfg['footprint']);inscribed=inscribed_radius(foot);cases=[]
 for index in range(8):
  raw=np.zeros((31,37),dtype=np.uint8);raw[rng.random(raw.shape)<.025]=254;raw[rng.random(raw.shape)<.015]=255
  expected=inflate(np,raw,.05,inscribed);text=f'37 31 .05 {inscribed:.17g} .85 4\n'+' '.join(map(str,raw.ravel().tolist()))
  p=subprocess.run([str(O/'inflate_reference')],input=text,text=True,capture_output=True,timeout=5);assert p.returncode==0;actual=np.asarray([int(v)for v in p.stdout.split()],dtype=np.uint8).reshape(raw.shape);assert np.array_equal(expected,actual),'INDEPENDENT_INFLATION_BYTE_MISMATCH';cases.append(dict(index=index,cells=raw.size,byte_exact=True))
 # Roundtrip rear/center at nonzero headings checks .3m coordinate offset.
 for a in [-math.pi,-1.2,0.,.3,math.pi]:
  p=rear([1.,2.,a,.1,.02]);assert math.dist([p[0]+.3*math.cos(a),p[1]+.3*math.sin(a)],[1.,2.])<1e-15
 request=dict(schema='PHASE_CURRENT_SOLVER_INPUT_V1',run_id='software',method='RPP',native_tick=0,sim_time=0.,body=[-4.,-2.,0.,0.,0.],steering={},controller_memory={},scan=dict(native_tick=0,time=0.,xy=[-4.,-2.],yaw=0.,ranges=[3.]*32),goal_xy=[4.,-2.],public_route=[[-4.3,-2.],[4.,-2.]],measurement_source_packet_sha256='a'*64,motion_class_prior_only=True,physical_authority=False)
 def front():return Frontend(np,public_sha256=sha(PUBLIC),parameter_sha256=sha(PARAMS))
 out=front().build(request);assert out['rear_pose_speed']==[-4.3,-2.,0.,0.,0.]and len(out['cells'])==14400 and len(out['footprint_xy'])==36
 negative=[]
 for label in ['actor_truth','future_scan','old_scan','bad_range','phase','live_authority','wrong_method','foreign_schema']:
  bad=copy.deepcopy(request)
  if label in ['actor_truth','phase']:bad[label]=[1,2]
  elif label=='future_scan':bad['scan']['native_tick']=1
  elif label=='old_scan':bad['native_tick']=10;bad['sim_time']=.1
  elif label=='bad_range':bad['scan']['ranges'][0]=float('nan')
  elif label=='live_authority':bad['physical_authority']=True
  elif label=='wrong_method':bad['method']='DWA'
  else:bad['schema']='OTHER'
  try:front().build(bad)
  except AssertionError:negative.append(label)
  else:raise AssertionError('BAD_MAP_SOURCE_ACCEPTED:'+label)
 f=front();f.build(request)
 try:f.build(request)
 except AssertionError:negative.append('duplicate_native')
 else:raise AssertionError('DUPLICATE_CURRENT_MAP')
 put(O/'SOFTWARE_MAP_EXAMPLE.json',out);return dict(passed=True,cpu=6,cases=cases,negative_cases=negative,inscribed_radius_m=inscribed,full_footprint_safety_qualified=False,original_cost_formula_only=True)
def main():
 start=time.monotonic();os.sched_setaffinity(0,{4});assert not(O/'SOFTWARE_ONCE.json').exists();put(O/'SOFTWARE_ONCE.json',dict(unix=time.time(),models=0))
 p=subprocess.run(['g++','-O2','-std=c++17',str(C/'inflate_reference.cpp'),'-o',str(O/'inflate_reference')],capture_output=True,text=True,timeout=60);put(O/'BUILD_REFERENCE.json',dict(passed=p.returncode==0,returncode=p.returncode,compiler_output=p.stderr,models=0));assert p.returncode==0
 with concurrent.futures.ThreadPoolExecutor(max_workers=1)as pool:result=pool.submit(map_check).result()
 put(O/'SOFTWARE_RESULT.json',dict(passed=result['passed'],map=result,models=0,Predictor_calls=0,Allocator_calls=0,physical_native=0,replay_native=0,DLL_loads=0,wall_s=time.monotonic()-start,source_qualified=False));print(__import__('json').dumps(read(O/'SOFTWARE_RESULT.json')))
if __name__=='__main__':main()
