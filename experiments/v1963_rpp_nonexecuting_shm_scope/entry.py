from context import R,C,O,read,sha,load
import os,subprocess,json,fcntl

def main():
 assert os.sched_getaffinity(0)=={2}
 execution_lock=(R/'runs/v648_static_unknown/execution.lock').open();fcntl.flock(execution_lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 resources=load('rpp_component_resource_policy',R/'experiments/v1067_causal_replan_brake_reserve/resource_policy.py').apply()
 load('component_immutable_guard',R/'experiments/v1504_priest_namespace_worker/common.py').guard(O)
 if os.environ.get('PHASE_RPP_SOURCE_PREFLIGHT')=='1':
  import time
  from context import put
  a=read(O/'SOURCE_PREFLIGHT_AUTHORITY.json');assert a['controller_calls_authorized']is False and a['boot_id']==__import__('pathlib').Path('/proc/sys/kernel/random/boot_id').read_text().strip()and time.time()<a['deadline_unix']and time.monotonic()<a['deadline_monotonic']
  assert all(sha(R/n)==h for n,h in a['source_files'].items());assert not(O/'SOURCE_PREFLIGHT_ONCE.json').exists();put(O/'SOURCE_PREFLIGHT_ONCE.json',dict(pid=os.getpid(),no_native_child=True))
  put(O/'ENTRY_SOURCE_PREFLIGHT_RESULT.json',dict(passed=True,explicit_RPP_DLL_loads=0,controller_constructors=0,solver_calls=0,physical_native=0,replay_native=0,resource_policy=resources,immutable_guard_installed=True,execution_lock_held_until_return=True,same_production_entry=True));return
 source=read(O/'SOURCE_FREEZE.json');assert all(sha(R/n)==h for n,h in source['files'].items());assert read(O/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered']
 ros=load('component_ros_namespace',R/'experiments/v856_nav2_foundation/ros_environment.py');env=ros.environment();env.update(ROS_DOMAIN_ID='195',ROS_LOG_DIR=str(O/'ros_logs'),CUDA_VISIBLE_DEVICES='');p=subprocess.run(ros.command(['/usr/bin/python3.12','-I','-B','-S',str(C/'native_component.py')]),cwd=R,env=env,capture_output=True,timeout=110);assert len(p.stdout)+len(p.stderr)<=4*1024**2;(O/'native.console').write_bytes(p.stdout+p.stderr);assert p.returncode==0,'NATIVE_RPP_API_COMPONENT_FAILED';print(json.dumps(read(O/'RESULT.json')))
if __name__=='__main__':main()
