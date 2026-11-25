"""Concrete new numeric fixtures and exact dependency closure, no algorithm calls."""
from common import R,C,ROOT,put,read,sha,load
from pathlib import Path
import json,math,os,re,subprocess,time

def main():
 os.sched_setaffinity(0,{6});start=time.monotonic();assert not(ROOT/'PREPARATION.json').exists();(ROOT/'lanes').mkdir()
 for lane in ['MPPI','SVG-MPPI']:(ROOT/'lanes'/lane).mkdir()
 path=[[i*.05,.04*(i*.05)**2,math.atan(.08*i*.05)]for i in range(41)];put(ROOT/'lanes/MPPI/INPUT.json',dict(scope='NEW_SYNTHETIC_GENTLE_CURVE_CONTROLLER_MATH_ONLY',rear_pose_speed=[0.,0.,0.,0.,0.],path_xyyaw=path,cells=[0]*14400,physical_native=0,not_common_task=True,expected_specific_twist_not_selected=True));put(ROOT/'lanes/SVG-MPPI/INPUT.json',dict(scope='NEW_SYNTHETIC_OFFSET_SLOPED_REFERENCE_AUTHOR_MATH_ONLY',state=[0.,.2,.1,0.,0.],not_common_task=True,actor_truth_supplied=False,physical_native=0))
 config=read(R/'runs/v1661_svg_binding_namespace/CONFIG.json');put(ROOT/'lanes/SVG-MPPI/CONFIG.json',config);planes={k:[]for k in ['collision_layer','distance_field','angle_field','speed_field']}
 for ix in range(100):
  x=5-(ix+.5)*.1
  for iy in range(100):
   y=5-(iy+.5)*.1;planes['collision_layer'].append(float(math.hypot(x-1.5,y-.2)<=.15));planes['distance_field'].append(abs(y-(.1*x+.2))/math.sqrt(1.01));planes['angle_field'].append(math.atan(.1));planes['speed_field'].append(.1)
 put(ROOT/'lanes/SVG-MPPI/MAPS.json',planes)
 ns=load('source_only_namespace',C/'namespace.py');cmd,env=ns.command('SVG-MPPI',C/'inventory_bootstrap.py');p=subprocess.run(cmd,cwd=R,env=env,capture_output=True,timeout=20);assert p.returncode==0,(p.stderr[-1000:]);bootstrap=json.loads(p.stdout);assert bootstrap['algorithm_DLL_loads']==0;put(ROOT/'BOOTSTRAP_ELF_INVENTORY.json',bootstrap)
 pins=read(R/'runs/v1983_rpp_bounded_console_queue/NATIVE_DEPENDENCIES.json')['namespace_ELF_files_SHA256'].copy();pins.update(bootstrap['files']);root=R/'runs/v856_nav2_foundation/rootfs';repo_files={};static=read(R/'runs/v1981_mppi_static_runtime_inputs/RESULT.json')['ELF_files'];todo=[]
 for name,row in static.items():
  p=Path(name);assert sha(p)==row['sha256'];todo.append(p)
 todo+=[R/'runs/v856_nav2_foundation/rootfs/opt/ros/jazzy/lib/libmppi_critics.so',R/'runs/v1655_svg_original_build_flags/libphase_svg_author_cpu.so',R/'runs/v1656_svg_solver_interface/libphase_svg_bridge.so'];folders=[R/'runs/v1655_svg_original_build_flags',R/'runs/v931_deadband_consistent_mppi/install/lib',root/'opt/ros/jazzy/lib',root/'opt/ros/jazzy/lib/x86_64-linux-gnu',root/'usr/lib/x86_64-linux-gnu',root/'usr/lib',root/'lib/x86_64-linux-gnu',Path('/usr/lib/x86_64-linux-gnu'),Path('/lib/x86_64-linux-gnu')];seen=set();missing=[]
 def pin(p):
  p=p.absolute();h=sha(p)
  if p.is_relative_to(R):
   relative=p.relative_to(R);repo_files[str(relative)]=h
   runtime='/'+str(relative).split('/rootfs/',1)[1]if '/rootfs/'in str(relative)and str(relative).split('/rootfs/',1)[1].startswith('opt/')else str(p)
  else:runtime=str(p)
  pins[runtime]=h
  real=p.resolve()
  if real!=p:
   if real.is_relative_to(R):repo_files[str(real.relative_to(R))]=sha(real)
   runtimereal=('/'+str(real.relative_to(root)))if real.is_relative_to(root/'opt')else str(real)
   pins[runtimereal]=h
 while todo:
  assert len(seen)<512 and time.monotonic()-start<120
  p=todo.pop();name=str(p)
  if name in seen:continue
  seen.add(name);pin(p);dynamic=subprocess.check_output(['readelf','-d',str(p)],text=True,timeout=5)
  for needed in re.findall(r'\(NEEDED\).*?\[(.*?)\]',dynamic):
   provider=next((d/needed for d in folders if(d/needed).is_file()),None)
   if provider is None:missing.append(dict(parent=name,needed=needed))
   else:todo.append(provider)
 assert not missing,missing
 metadata=[R/'runs/v931_deadband_consistent_mppi/install/share/phase_deadband_mppi/plugin.xml',R/'runs/v931_deadband_consistent_mppi/install/share/phase_deadband_mppi/package.xml',R/'runs/v931_deadband_consistent_mppi/install/share/ament_index/resource_index/nav2_core__pluginlib__plugin/phase_deadband_mppi',R/'runs/v931_deadband_consistent_mppi/install/share/ament_index/resource_index/packages/phase_deadband_mppi',root/'opt/ros/jazzy/share/nav2_mppi_controller/critics.xml',root/'opt/ros/jazzy/share/nav2_mppi_controller/mppic.xml']
 for p in metadata:repo_files[str(p.relative_to(R))]=sha(p)
 put(ROOT/'NAMESPACE_ELF_PINS.json',dict(files=pins,repo_dependency_files=repo_files,static_ELF_files=len(seen),unresolved=[],bootstrap_SHA=sha(ROOT/'BOOTSTRAP_ELF_INVENTORY.json'),dynamic_dependencies_not_guaranteed_complete=True));proof=dict(passed=True,concrete_new_inputs=True,CPU_lanes=dict(MPPI=6,SVG_MPPI=7),static_ELFs=len(seen),namespace_pins=len(pins),new_algorithm_DLL_loads=0,constructors=0,optimizer_calls=0,physics=0,replay=0,wall_s=time.monotonic()-start);put(ROOT/'PREPARATION.json',proof);print(json.dumps(proof))
if __name__=='__main__':main()
