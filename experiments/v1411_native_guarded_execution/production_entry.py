"""New native backend production entry checks; vehicle execution stays closed."""
import argparse
import ast
import copy
import fcntl
import hashlib
import importlib.abc
import importlib.util
import json
import os
from pathlib import Path
import sys
import traceback

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name


def exact(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


class NoPhysical(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0] in {'mujoco','vehicle','torch','factory','physical','rclpy'}:
            raise AssertionError('V1411_QUALIFICATION_NO_PHYSICAL:'+name)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('output');parser.add_argument('--entry-check',action='store_true');parser.add_argument('--contract-check',action='store_true');parser.add_argument('--injected-early-failure',action='store_true');args=parser.parse_args()
    assert args.entry_check or args.contract_check or args.injected_early_failure,'NO_COMPLETE_PHYSICAL_ROUTE_LAUNCH_AUTHORITY'
    assert os.environ.get('PHASE_REPO')==str(R) and sorted(os.sched_getaffinity(0))==[2]
    out=Path(args.output).resolve();assert out.is_relative_to(O) and out!=O and out.is_dir()
    sys.meta_path.insert(0,NoPhysical())
    def forbid(frame,event,arg):
        if event=='call' and frame.f_code.co_name in {'__init__','step'} and Path(frame.f_code.co_filename).name in {'coupled_model.py','prediction.py','kernel.py'}:
            raise AssertionError('V1411_QUALIFICATION_MODEL_CALL_FORBIDDEN')
    sys.setprofile(forbid)
    sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'))
    from resource_policy import apply
    apply()
    path=R/'runtime/mk-mini/experiments/phase_rpccr_p0b3_v1/pilot.py'
    node=next(n for n in ast.parse(path.read_text()).body if isinstance(n,ast.FunctionDef)and n.name=='write_guard')
    scope=dict(Path=Path,os=os,OUT=out);exec(compile(ast.Module(body=[node],type_ignores=[]),str(path),'exec'),scope);sys.addaudithook(scope['write_guard'])
    io=exact('v1411_actual_atomic_json',R/'experiments/v1383_exact_timed_handoff/evidence_io.py')
    read=lambda p:json.loads(p.read_text())
    assert not read(R/'runs/v1382_weekend_campaign/LEDGER.json')['models_now_authorized']
    result=dict(passed=False,closed=False,models=0,analytical_native=0,physical_native=0,replay_native=0,physical_admission=False)
    with(R/'runs/v648_static_unknown/execution.lock').open('r')as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        try:
            modules={name:exact('v1411_entry_'+name,C/(name+'.py')) for name in ['native_step','reserve','physical_guard','evidence_sink','event_owner','route_command','bridge_execution']}
            generator=exact('v1411_entry_real_model_bindings',R/'experiments/v1410_scalar_feedback_witness/generator.py');generator.binding()
            if args.injected_early_failure:raise RuntimeError('V1411_INJECTED_BEFORE_ANY_MODEL_OR_VEHICLE_CALL')
            if args.entry_check:
                result.update(passed=True,actual_cpu=[2],real_production_sources_loaded=list(modules),model_constructor_step_profile_refusal=True,original_writeguard=True)
            else:
                import numpy as np
                negatives=[]
                def reject(name,fn):
                    try:fn()
                    except(AssertionError,ValueError,KeyError):negatives.append(name)
                    else:raise AssertionError('NATIVE_CONTRACT_NEGATIVE_ACCEPTED:'+name)
                base=R/'runs/v858_nav2_verified/v1396/full9390_main'
                original=read(base/'CAPTURE_COMMANDS.json')[0];reply=original['rpp_reply'];wire=read(base/'OBSERVATIONS_SENT.json')[reply['observation_sequence']]
                p=dict(kind='command',command_source='ORIGINAL_RPP_WITH_SHARED_BRIDGE',run_id=wire['run_id'],sequence=original['packet']['sequence'],issued_at=original['packet']['issued_at'],v=reply['v'],w=reply['w'],origin=reply['origin'],observation_sequence=wire['sequence'],observation_native_tick=wire['native_tick'],observation_sampled_at=wire['sampled_at'])
                now=original['delivery']['validated_monotonic'];sent={wire['sequence']:wire};Commands=modules['route_command'].Commands
                owner=Commands(wire['run_id']);got=owner.accept(p,sent,current_native=wire['native_tick'],now=now);assert got and got['control_owner']=='ORIGINAL_RPP'
                assert owner.accept(p,sent,current_native=wire['native_tick'],now=now)is None and owner.retired[-1]['reason']=='ALREADY_CONSUMED_SEQUENCE'
                assert Commands(wire['run_id']).accept(p,sent,current_native=wire['native_tick']+5,now=now)is None
                assert Commands(wire['run_id']).accept(p,sent,current_native=wire['native_tick'],now=now+.201)is None
                for name,mutate in [('scan_time',lambda x:x.update(observation_sampled_at=x['observation_sampled_at']+.001)),('wrong_run',lambda x:x.update(run_id='foreign')),('nonfinite_envelope',lambda x:x.update(issued_at=float('nan'))),('modeled_packet',lambda x:x.update(kind='ORIGINAL_RPP_MODELED_COMMAND')),('unknown_source',lambda x:x.update(command_source='unknown')),('local_nonzero',lambda x:x.update(command_source='CAUSAL_BRAKE_TIMER'))]:
                    changed=copy.deepcopy(p);mutate(changed);reject(name,lambda changed=changed:Commands(wire['run_id']).accept(changed,sent,current_native=wire['native_tick'],now=now))
                changed=copy.deepcopy(p);changed['origin']['stamp_ns']+=1;reject('stamp_tamper',lambda:Commands(wire['run_id']).accept(changed,sent,current_native=wire['native_tick'],now=now))
                reject('future_native',lambda:Commands(wire['run_id']).accept(p,sent,current_native=wire['native_tick']-1,now=now))
                current=read(R/'runs/v1410_scalar_feedback_witness/model/CURRENT_INPUT.json');spec=current.pop('method_spec');geometry=current.pop('event_geometry');current.pop('input_sha256');current['input_sha256']=modules['event_owner'].session.digest(current)
                bound=modules['event_owner'].finite_input(current,spec,geometry);assert bound['base_input_sha256']==current['input_sha256'];generator.Method(bound)
                malformed=copy.deepcopy(bound);malformed['method_spec']['method']='ORIGINAL_RPP_CURRENT_RESPONSE';reject('method_not_geometry_bound',lambda:generator.Method(malformed))
                native_ast=ast.parse((C/'native_step.py').read_text());apply_node=next(n for cls in native_ast.body if isinstance(cls,ast.ClassDef)for n in cls.body if isinstance(n,ast.FunctionDef)and n.name=='apply')
                assert not any(isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and n.func.attr in {'scan','current'}for n in ast.walk(apply_node))
                probe=dict(passed=np.bool_(True),nested=[np.bool_(False),np.float64(.22),np.int64(200)])
                assert json.loads(modules['evidence_sink'].encode(probe))==dict(passed=True,nested=[False,.22,200])
                io.atomic(out/'NUMPY_JSON.json',probe);assert read(out/'NUMPY_JSON.json')['passed']is True
                result.update(passed=True,negative_checks=negatives,valid_saved_actual_RPC_binding=True,three_valid_stale_retirements=True,method_geometry_and_base_input_bound=True,no_extra_scan_in_apply=True,real_NumPy_evidence_JSON=True,qualification_uses_saved_packet_clock_not_fresh_measurement=True)
        except BaseException as exc:result.update(error=repr(exc),traceback=traceback.format_exc())
        finally:
            result['closed']=True;io.atomic(out/'RESULT.json',result)
    print(json.dumps(read(out/'RESULT.json'),allow_nan=False))
    return 0 if result['passed']else 1


if __name__=='__main__':raise SystemExit(main())
