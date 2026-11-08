"""Launch genuine binary Nav2 servers; all algorithms come from upstream packages."""
import os,signal,subprocess,time
from pathlib import Path
C=Path(__file__).parent; R=C.parents[1]
SERVERS=[('nav2_map_server','map_server',[]),('nav2_planner','planner_server',['-r','compute_path_to_pose:=smac_compute_path_to_pose']),('nav2_controller','controller_server',['-r','cmd_vel:=cmd_vel_nav']),('nav2_behaviors','behavior_server',['-r','cmd_vel:=cmd_vel_nav']),('nav2_velocity_smoother','velocity_smoother',['-r','cmd_vel:=cmd_vel_nav']),('nav2_collision_monitor','collision_monitor',[]),('nav2_bt_navigator','bt_navigator',[]),('nav2_lifecycle_manager','lifecycle_manager',['-r','__node:=lifecycle_manager_navigation'])]
class Stack:
    def __init__(self,out,config):self.out=Path(out);self.config=Path(config);self.jobs=[];self.files=[]
    def start(self):
        for package,exe,remap in SERVERS:
            f=(self.out/(exe+'.console')).open('w');self.files.append(f)
            args=[f'/opt/ros/jazzy/lib/{package}/{exe}','--ros-args','--params-file',str(self.config),*remap]
            self.jobs.append(subprocess.Popen(args,stdout=f,stderr=subprocess.STDOUT))
    def failed(self):return [(s[1],p.returncode)for s,p in zip(SERVERS,self.jobs)if p.poll() is not None]
    def close(self):
        for p in reversed(self.jobs):
            if p.poll() is None:p.send_signal(signal.SIGINT)
        until=time.monotonic()+4
        for p in self.jobs:
            try:p.wait(timeout=max(.01,until-time.monotonic()))
            except subprocess.TimeoutExpired:p.kill();p.wait()
        for f in self.files:f.close()
