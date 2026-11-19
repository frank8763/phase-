"""Exact producer-runtime independent audit; physical imports forbidden."""
import importlib.abc
import os
import sys
from component_context import *

class NoPhysical(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0] in {'mujoco','vehicle','torch','physical','factory','rclpy'}:raise AssertionError('AUDIT_MODEL_IMPORT '+name)

sys.meta_path.insert(0,NoPhysical())

def main():
    os.sched_setaffinity(0,{5});task=read(sys.argv[1])
    if task['stage']=='component':from recovery_audit import audit
    else:from route_audit import audit
    proof=audit(task)
    if task['stage']!='component':
        from map_gate import inspect_map
        out=Path(task['output']);grid=read(R/'experiments/v1331_common_static_map/PUBLIC_STATIC_GRID.json')
        proof['checks']['initial_current_window_map_complete']=inspect_map(read(out/'INITIAL_ACTUAL_COSTMAP.json'),grid)['passed']
        proof['passed']=all(proof['checks'].values())
    proof['audit_python']=sys.version;proof['audit_numpy']=__import__('numpy').__version__
    proof['physical_models_imported']=False
    print(json.dumps(proof))

if __name__=='__main__':main()
