"""Actual isolated CPU2 import/serialization/write boundary, zero construction."""
import argparse
import ast
import fcntl
import importlib.abc
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name


class NoPhysical(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0] in {'mujoco','vehicle','torch','factory','physical','rclpy'}:
            raise AssertionError('ZERO_MODEL_CPU2_ENTRY_IMPORT:'+name)


def install_guard():
    path=R/'runtime/mk-mini/experiments/phase_rpccr_p0b3_v1/pilot.py'
    tree=ast.parse(path.read_text());node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='write_guard')
    scope=dict(Path=Path,os=os,OUT=O)
    exec(compile(ast.Module(body=[node],type_ignores=[]),str(path),'exec'),scope)
    sys.addaudithook(scope['write_guard'])
    return str(path.relative_to(R))


def main():
    p=argparse.ArgumentParser();p.add_argument('--mode',choices=['entry','producer','guard'],required=True);args=p.parse_args()
    assert sorted(os.sched_getaffinity(0))==[2] and os.environ.get('PHASE_REPO')==str(R)
    os.chdir(R);sys.meta_path.insert(0,NoPhysical())
    registration=json.loads((O/'CPU2_PREPARATION_REGISTRATION.json').read_text())
    assert registration['maximum_model_constructions']==registration['maximum_model_steps']==0 and registration['physical_admission'] is False
    assert args.mode in registration['entry_modes']
    attempts=[]
    def forbid_construction(frame,event,arg):
        if event=='call':
            filename=Path(frame.f_code.co_filename).name
            if ((frame.f_code.co_name=='__init__' and filename in {'coupled_model.py','prediction.py','kernel.py'})
                    or (frame.f_code.co_name=='step' and filename in {'coupled_model.py','prediction.py','kernel.py'})
                    or frame.f_code.co_name=='create_vehicle'):
                attempts.append(dict(file=filename,function=frame.f_code.co_name))
                raise AssertionError('MODEL_CONSTRUCTION_OR_STEP_IN_ZERO_QUALIFICATION')
    sys.setprofile(forbid_construction)
    guard=install_guard()
    import response_generator as source
    with (R/'runs/v648_static_unknown/execution.lock').open('r') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        Predictor,initial,kernel,Adapter,Geometry,Gear,Capture=source.binding()
        functions=[source.generate,source.clone_private_branch,Predictor.step,initial,Adapter.compute,Geometry.tube,Gear.select,Capture.select]
        bindings={fn.__qualname__:str(Path(fn.__code__.co_filename).resolve().relative_to(R)) for fn in functions}
        assert os.environ['MUJOCO_GL']=='osmesa' and os.environ['CUDA_VISIBLE_DEVICES']==''
        import numpy as np
        io=source.exact('v1398_qualified_producer_json',R/'experiments/v1383_exact_timed_handoff/evidence_io.py')
        proof=dict(passed=True,entry_mode=args.mode,actual_cpu=sorted(os.sched_getaffinity(0)),physical_imports_forbidden=True,
                   model_constructor_attempts=attempts,model_constructions=0,analytical_native=0,physical_native=0,
                   production_guard=guard,source_bindings=bindings,osmesa_environment=True,physical_admission=False,
                   full_model_generator_qualified=False)
        if args.mode=='entry':
            # Use the exact branch factory, with software wheel arrays only.
            owner=SimpleNamespace(front=[1.,2.],front_rate=[3.,4.],adapter=SimpleNamespace())
            owner.adapter.encoders=lambda:owner.front+owner.front_rate
            branch=source.clone_private_branch(owner,lambda a,b:a+b)
            branch.front[0]=9.;owner.front_rate[0]=8.
            assert branch.adapter.encoders()==[9.,2.,3.,4.] and owner.adapter.encoders()==[1.,2.,8.,4.]
            proof['private_branch_encoder_owner_is_independent']=True
            try:source.generate({}, {}, authority={'models_authorized':False},lock=lock,peer_command=None,save_branch=None)
            except AssertionError as exc:assert str(exc)=='CURRENT_WITNESS_NOT_REGISTERED'
            else:raise AssertionError('UNREGISTERED_GENERATOR_STARTED')
            proof['unregistered_model_entry_refused']=True
        if args.mode=='producer':
            value=dict(passed=np.bool_(True),failed=np.bool_(False),states=np.array([[1.,2.],[3.,4.]]),ulp=np.nextafter(np.float64(1.),np.float64(2.)))
            path=O/'cpu2_preparation/ACTUAL_PRODUCER_JSON.json';io.atomic(path,value)
            parsed=json.loads(path.read_text());assert parsed['passed'] is True and parsed['failed'] is False and parsed['states']==[[1.,2.],[3.,4.]] and parsed['ulp']>1.
            try:io.atomic(O/'cpu2_preparation/REJECT_NONFINITE.json',dict(value=np.nan))
            except ValueError:pass
            else:raise AssertionError('PRODUCER_ACCEPTED_NONFINITE')
            proof['actual_numpy_producer_json_roundtrip']=True
        if args.mode=='guard':
            checks=[]
            def reject(name,call):
                try:call()
                except PermissionError:checks.append(name)
                else:raise AssertionError('CPU2_WRITE_ESCAPE_ACCEPTED:'+name)
            target=O/'cpu2_preparation/WRITE_ALLOWED.json';io.atomic(target,dict(fixture=True));assert json.loads(target.read_text())['fixture']
            reject('source_tree_write',lambda:(C/'UNEXPECTED_WRITE.tmp').write_text('forbidden'))
            reject('other_round_write',lambda:(R/'runs/v1396_rpp_rpc_retirement/UNEXPECTED_WRITE.tmp').write_text('forbidden'))
            reject('parent_traversal',lambda:(O/'../../UNEXPECTED_WRITE.tmp').write_text('forbidden'))
            reject('outside_mkdir',lambda:(R/'runs/v1396_rpp_rpc_retirement/UNEXPECTED_DIRECTORY').mkdir())
            reject('outside_rename',lambda:target.replace(R/'runs/v1396_rpp_rpc_retirement/UNEXPECTED_RENAME.tmp'))
            link=O/'cpu2_preparation/readonly_source_link';link.symlink_to(C,target_is_directory=True)
            reject('symlink_write_escape',lambda:(link/'UNEXPECTED_WRITE.tmp').write_text('forbidden'))
            proof['guard_rejections']=checks
        assert not attempts and not any(n in sys.modules for n in ['mujoco','vehicle','torch'])
        io.atomic(O/('cpu2_preparation/'+args.mode+'.json'),proof)
        print(json.dumps(proof))
    sys.setprofile(None)


if __name__=='__main__':main()
