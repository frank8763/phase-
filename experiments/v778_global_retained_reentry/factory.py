"""Reuse verified reset/scenario dependencies, before any navigation physics."""
import os,sys,types
from pathlib import Path

class ContextReady(BaseException):
    def __init__(self,context):self.context=context

def initialize(seed,out):
    import mujoco
    native=mujoco.mj_step
    repo=Path(os.environ['PHASE_REPO'])
    task_seed=int(seed)
    bootstrap_seed=95000011
    os.environ['RPCCR_SEED']=str(bootstrap_seed);os.environ['V541_OUTPUT_DIR']=str(out)
    source=(repo/'current/runner.py').read_text()
    old="    out = __import__('pathlib').Path(__file__).resolve().parents[2] / 'output_v630'"
    assert source.count(old)==1
    source=source.replace(old,"    out = __import__('pathlib').Path(__import__('os').environ['V541_OUTPUT_DIR'])")
    noise_anchor='    shift = B.load_shift(SEED)'
    assert source.count(noise_anchor)==1
    source=source.replace(noise_anchor, f'    shift = B.load_shift({task_seed})')
    anchor='            catalog=GeometryCatalog(env.model,mujoco,xml)'
    assert source.count(anchor)==1
    source=source.replace(anchor,"            from factory import ContextReady\n            raise ContextReady(dict(locals()))")
    reset_anchor='                    result=original_reset(self,*args,**kwargs)'
    assert source.count(reset_anchor)==1
    source=source.replace(reset_anchor,'                    result=_rpccr_reset_without_obsolete_detour(original_reset,self,*args,**kwargs)')
    reset_gate={'reset_calls':0,'old_detour_calls':0,'disabled_before_original_reset':False,'bootstrap_integrations':0}
    def reset_without_obsolete_detour(original_reset,env,*args,**kwargs):
        reset_gate['reset_calls']+=1
        assert reset_gate['reset_calls']==1,'MULTIPLE_BOOTSTRAP_RESETS'
        reset_gate['old_detour_enabled_before']=bool(env.phase21_v3_enable_detour)
        env.phase21_v3_enable_detour=False
        reset_gate['disabled_before_original_reset']=not env.phase21_v3_enable_detour
        result=original_reset(env,*args,**kwargs)
        assert not env.phase21_v3_enable_detour,'BOOTSTRAP_RESET_REENABLED_OBSOLETE_DETOUR'
        return result
    module=types.ModuleType('v649_reset_context');module.__file__=str(repo/'current/runner.py')
    module._rpccr_reset_without_obsolete_detour=reset_without_obsolete_detour
    sys.path.insert(0,str(repo/'current'))
    gui=types.ModuleType('v115_live_view');gui.tick=lambda *a,**k:None;gui.close=lambda *a,**k:None
    sys.modules['v115_live_view']=gui
    exec(compile(source,module.__file__,'exec'),module.__dict__)
    previous_profile=sys.getprofile()
    def prohibit_bootstrap_integration(frame,event,arg):
        if event=='call' and frame.f_code.co_name=='_phase21_v3_build_detour':
            reset_gate['old_detour_calls']+=1
            raise RuntimeError('OBSOLETE_DETOUR_CALLED_DURING_BOOTSTRAP')
        if event=='c_call' and getattr(arg,'__name__','') in ('mj_step','mj_step1','mj_step2'):
            reset_gate['bootstrap_integrations']+=1
            raise RuntimeError('INTEGRATION_DURING_SCENE_BOOTSTRAP')
    sys.setprofile(prohibit_bootstrap_integration)
    try:
        try:module.main()
        except ContextReady as ready:
            context=ready.context
        else:raise RuntimeError('RESET_CONTEXT_NOT_CAPTURED')
    finally:
        sys.setprofile(previous_profile)
    mujoco.mj_step=native
    from arena import prepare
    prepare(context,mujoco)
    assert float(context['env'].data.time)==0.,'BOOTSTRAP_TIME_NOT_ZERO'
    assert reset_gate['reset_calls']==1 and reset_gate['disabled_before_original_reset'] and reset_gate['old_detour_calls']==reset_gate['bootstrap_integrations']==0
    # Only scene bootstrap uses the fixed anchor. Sensor corruption is keyed by task_seed.
    context['E'].seed_all(task_seed)
    os.environ['RPCCR_SEED']=str(task_seed)
    import json,hashlib
    record={'bootstrap_seed':bootstrap_seed,'task_noise_seed':task_seed,'legacy_task_gate_unchanged':True,'navigation_algorithm_changed':False,'sensor_implementation_changed':False,'noise_call_state_after_bootstrap':dict(context['shift']),'zero_integration_bootstrap':True,'initial_time':float(context['env'].data.time),'parent_factory_sha256':hashlib.sha256((repo/'experiments/v695_discovery_verified_fixture/factory.py').read_bytes()).hexdigest(),'legacy_runner_sha256':hashlib.sha256((repo/'current/runner.py').read_bytes()).hexdigest()}
    record['bootstrap_repair']=reset_gate
    (Path(context['out'])/'INITIALIZATION_PROVENANCE.json').write_text(json.dumps(record,indent=2)+'\n')
    return context,native
