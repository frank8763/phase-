"""Exercise the actual saved input and real reference setter without any model."""
import ast,importlib.abc,json,sys
from pathlib import Path
from types import SimpleNamespace
class NoModels(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name=='mujoco'or name.startswith('mujoco.'):raise RuntimeError('TYPE_QUALIFICATION_NO_MODELS')
sys.meta_path.insert(0,NoModels())
from common import *
import numpy as np
sys.path.insert(0,str(W))
from reserved_recovery import ReservedRecovery


def main():
    old=read(R/'runs/v853_daytime_20261107/FINALIZED.json');assert old['source_and_decompressed_sha_verified']and old['counts']['component_old_replay_native']==3192 and old['counts']['component_private_native']==old['counts']['component_actual_native']==0
    for name,expected in read(R/'experiments/v853_daytime_20261107/CANDIDATE_FREEZE.json')['files'].items():assert sha(R/name)==expected
    p=R/'runs/v851_profile_output_worker/v851_main_slot01/paired/geometry_memory/planning_0303.json';path=read(p)['path'];x=ReservedRecovery.__new__(ReservedRecovery)
    try:x.set_reference(path,0,[4.,-2.],.60)
    except TypeError as e:assert str(e)=='list indices must be integers or slices, not tuple'
    else:raise AssertionError('ORIGINAL_OPERATION_BUG_NOT_REPRODUCED')
    x.set_reference(np.asarray(path,float),0,[4.,-2.],.60);assert x.reference['path']==path and x.reference['index']==0 and x.reference['goal_xy']==[4.,-2.]
    original=(R/'experiments/v853_daytime_20261107/component.py').read_text();new=(C/'component.py').read_text();before="reserved.set_reference(route['path'],trace[step]['path_index'],protocol['goal_xy'],.60)";after="reserved.set_reference(np.asarray(route['path'],float),trace[step]['path_index'],protocol['goal_xy'],.60)";assert new.replace(after,before)==original
    tree=ast.parse(new);call=next(n for n in ast.walk(tree)if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and n.func.attr=='set_reference');namespace=dict(reserved=x,route=dict(path=path),trace={399:dict(path_index=0)},step=399,protocol=dict(goal_xy=[4.,-2.]),np=np);exec(compile(ast.Expression(call),str(C/'component.py'),'eval'),namespace);assert x.reference['path']==path
    for folder in [C,W]:
        for p in folder.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
    result=dict(passed=True,old_exact_TypeError_reproduced=True,new_actual_saved_list_input_exact=True,actual_component_callsite_evaluated=True,component_only_one_type_conversion=True,all_V853_scientific_and_operation_sources_unchanged=True,original_failure_archived=True,old_replay3192_preserved=True,models=0,integrations=0,original_root_deadline_unix=DEADLINE)
    dump(ROOT/'INPUT_TYPE_QUALIFICATION.json',result);print(json.dumps(result))


if __name__=='__main__':main()
