from context import R,C,O,read,sha,load
import os,subprocess,json

def main():
 assert os.sched_getaffinity(0)=={2};load('component_immutable_guard',R/'experiments/v1504_priest_namespace_worker/common.py').guard(O)
 source=read(O/'SOURCE_FREEZE.json');assert all(sha(R/n)==h for n,h in source['files'].items());assert read(O/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered']
 ros=load('component_ros_namespace',R/'experiments/v856_nav2_foundation/ros_environment.py');env=ros.environment();env.update(ROS_DOMAIN_ID='195',ROS_LOG_DIR=str(O/'ros_logs'),CUDA_VISIBLE_DEVICES='');p=subprocess.run(ros.command(['/usr/bin/python3.12','-I','-B','-S',str(C/'native_component.py')]),cwd=R,env=env,capture_output=True,timeout=110);assert len(p.stdout)+len(p.stderr)<=4*1024**2;(O/'native.console').write_bytes(p.stdout+p.stderr);assert p.returncode==0,'NATIVE_RPP_API_COMPONENT_FAILED';print(json.dumps(read(O/'RESULT.json')))
if __name__=='__main__':main()
