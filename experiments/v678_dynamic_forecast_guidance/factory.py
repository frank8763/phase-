"""Reuse verified reset/scenario dependencies, before any navigation physics."""
import os,sys,types
from pathlib import Path

class ContextReady(BaseException):
    def __init__(self,context):self.context=context

def initialize(seed,out):
    import mujoco
    native=mujoco.mj_step
    repo=Path(os.environ['PHASE_REPO'])
    os.environ['RPCCR_SEED']=str(seed);os.environ['V541_OUTPUT_DIR']=str(out)
    source=(repo/'current/runner.py').read_text()
    old="    out = __import__('pathlib').Path(__file__).resolve().parents[2] / 'output_v630'"
    assert source.count(old)==1
    source=source.replace(old,"    out = __import__('pathlib').Path(__import__('os').environ['V541_OUTPUT_DIR'])")
    anchor='            catalog=GeometryCatalog(env.model,mujoco,xml)'
    assert source.count(anchor)==1
    source=source.replace(anchor,"            from factory import ContextReady\n            raise ContextReady(dict(locals()))")
    module=types.ModuleType('v649_reset_context');module.__file__=str(repo/'current/runner.py')
    sys.path.insert(0,str(repo/'current'))
    gui=types.ModuleType('v115_live_view');gui.tick=lambda *a,**k:None;gui.close=lambda *a,**k:None
    sys.modules['v115_live_view']=gui
    exec(compile(source,module.__file__,'exec'),module.__dict__)
    try:module.main()
    except ContextReady as ready:
        context=ready.context
    else:raise RuntimeError('RESET_CONTEXT_NOT_CAPTURED')
    mujoco.mj_step=native
    return context,native
