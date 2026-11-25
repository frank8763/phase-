"""CPU6 compile-only constructor preparation; no new algorithm retry."""
from pathlib import Path
import hashlib,json,os,subprocess,time
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 os.sched_setaffinity(0,{6});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));assert not(O/'ONCE.json').exists();start=time.monotonic();(O/'ONCE.json').write_text(json.dumps(dict(pid=os.getpid(),unix=time.time(),compile_only=True,max_s=180))+'\n');source=R/'experiments/v1976_mppi_plugin_sync_api/bridge.cpp';before=source.read_text();params=R/'experiments/v1344_causal_night_entry/coherent_mppi_causal_params.json';mapparams=json.loads(params.read_text())['local_costmap']['local_costmap']['ros__parameters'];assert 'map->set_parameter(rclcpp::Parameter("footprint"'not in before
 lines=[]
 for key in ['width','height','resolution','rolling_window','footprint','footprint_padding','transform_tolerance']:
  v=mapparams[key];literal=json.dumps(v)if isinstance(v,str)else'true'if v is True else'false'if v is False else str(v);literal='int64_t('+literal+')'if type(v)is int else literal;lines.append('  map->set_parameter(rclcpp::Parameter('+json.dumps(key)+','+literal+'));')
 marker='  if(map->on_configure(map->get_current_state())';assert before.count(marker)==1;after=before.replace(marker,'\n'.join(lines)+'\n'+marker);(C/'bridge.cpp').write_text(after);(C/'registered_parameters.inc').write_bytes((source.parent/'registered_parameters.inc').read_bytes())
 original=json.loads((R/'runs/v1976_mppi_plugin_sync_api/BUILD_RESULT.json').read_text());cmd=[str(C/'bridge.cpp')if v==str(source)else str(O/'libphase_mppi_map_bootstrap.so')if v==str(R/original['binary_path'])else str(C)if v==str(source.parent)else v for v in original['command']]
 p=subprocess.run(cmd,cwd=R,capture_output=True,text=True,timeout=150);(O/'COMPILE.log').write_text(p.stdout+p.stderr);result=dict(passed=p.returncode==0,closed=True,returncode=p.returncode,source_pins={str(p.relative_to(R)):sha(p)for p in [source,params,C/'bridge.cpp',C/'registered_parameters.inc']},unchanged_controller_parameter_include=sha(C/'registered_parameters.inc')==sha(source.parent/'registered_parameters.inc'),only_map_configuration_before_controller_constructor=True,registered_original_map_parameters=mapparams,plugins_still_external_current_grid=True,missing_inflation_plugin_or_ABI_root_cause_not_yet_proven=True,algorithm_DLL_loads=0,constructor_calls=0,optimizer_calls=0,physics_native=0,replay_native=0,numerical_admission=False,MPPI_crash_not_retried=True,CPU=6,wall_s=time.monotonic()-start)
 if p.returncode==0:result.update(binary_path=str((O/'libphase_mppi_map_bootstrap.so').relative_to(R)),binary_sha256=sha(O/'libphase_mppi_map_bootstrap.so'))
 (O/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k]for k in ['passed','closed','CPU','algorithm_DLL_loads','constructor_calls','optimizer_calls','wall_s']}))
if __name__=='__main__':main()
