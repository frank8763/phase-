"""Disallow the simulator import in every offline validation child process."""
import runpy,sys
from pathlib import Path

def block_simulator(event,args):
    if event=='import' and str(args[0]).split('.')[0]=='mujoco':
        raise RuntimeError('V699_ZERO_INTEGRATION_ANALYSIS_FORBIDS_MUJOCO_IMPORT')
sys.addaudithook(block_simulator)
src=Path(__file__).resolve().parent;target=(src/sys.argv[1]).resolve()
assert target.parent==src and target.name in ['audit_discovery.py','validate_contract.py']
sys.argv=[str(target),*sys.argv[2:]];runpy.run_path(str(target),run_name='__main__')
