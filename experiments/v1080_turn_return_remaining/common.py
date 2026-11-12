"""Scoped bindings; shared immutable science is reused, never edited."""
import sys,json,hashlib,importlib.util,os,time
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1080_turn_return_remaining';RAW=R/'runs/v858_nav2_verified/v1080'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def paths():
 sys.path[:0]=[str(C),str(R/'experiments/v1079_dual_steering_qualification'),str(R/'experiments/v1070_frozen_sac_proposals'),str(R/'experiments/v1073_live_sac_dependency_entry'),str(R/'runtime/mk-mini'),str(R/'runtime/mk-mini/training/phase14_lidar_depth_nav/envs'),str(R/'experiments/v1067_causal_replan_brake_reserve')]
def dump(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,allow_nan=False,indent=2)+'\n')
def factory():
 m=load('v1080_qualified_scene_binding',R/'experiments/v1067_causal_replan_brake_reserve/scene_binding.py');m.O=O;return m
