"""Unchanged NS-successful science; add preflight model/initial-state binding."""
import importlib.util,sys,types
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1]
spec=importlib.util.spec_from_file_location('v1097_route_worker',R/'experiments/v1089_route_scene_contract/worker.py');prior=importlib.util.module_from_spec(spec);spec.loader.exec_module(prior)
def patched_source():
    s=prior.patched_source();anchor='bind(v,law.Adapter,mj);native=v.native';assert s.count(anchor)==1
    binding="pre=Path(json.loads((O/'CONFIG.json').read_text())['preflight_output'])/'physics';assert setup['model_sha256']==json.loads((pre/'SETUP.json').read_text())['model_sha256'],'PREFLIGHT_MODEL_CHANGED';assert np.array_equal(np.load(pre/'INITIAL_STATE.npz')['state'],np.load(out/'physics/INITIAL_STATE.npz')['state']),'PREFLIGHT_INITIAL_STATE_CHANGED';"
    return s.replace(anchor,binding+anchor)
def load_worker():
    prior.configure();m=types.ModuleType('v1097_same_science_worker');m.__file__=str(prior.ORIGINAL);exec(compile(patched_source(),str(prior.ORIGINAL),'exec'),m.__dict__);return m
if __name__=='__main__':
    prior.configure();exec(compile(patched_source(),str(prior.ORIGINAL),'exec'),dict(__name__='__main__',__file__=str(prior.ORIGINAL)))
