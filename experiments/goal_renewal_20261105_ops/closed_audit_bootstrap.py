"""One unchanged frozen audit in a separate read-only evidence view. No models."""
import argparse,importlib.abc,runpy,sys
from pathlib import Path
class NoModels(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name=='mujoco' or name.startswith('mujoco.'):
            raise RuntimeError('CLOSED_SUPPLEMENT_FORBIDS_MODELS_AND_INTEGRATIONS')
sys.meta_path.insert(0,NoModels())
repo=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser();p.add_argument('audit',choices=['goal','discovery']);a=p.parse_args()
own=repo/'experiments/v826_goal_reference_renewal'
for directory in [repo/'runtime/mk-mini/experiments/phase_rpccr_p0b76_online_gate_v1',repo/'runtime/mk-mini/experiments/phase_rpccr_p0b68_v1',own]:
    sys.path.insert(0,str(directory))
view=repo/'runs/goal_renewal_20261105/closed_audit_supplement/evidence_view'
if a.audit=='goal':
    target=own/'audit_goal_renewal.py';sys.argv=[str(target),str(view)]
else:
    target=own/'audit_field_discovery.py';sys.argv=[str(target),str(view),'--output-dir',str(view.parent/'discovery_chain')]
runpy.run_path(str(target),run_name='__main__')
