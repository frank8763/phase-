"""Preparation-only import-path correction; original failed receipt preserved."""
import importlib.abc
from pathlib import Path
import sys
R=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(R/'experiments/v1346_measured_gear_handoff'))
import response_probe as original
original.O=R/'runs/v1379_timed_response_preparation/entry02'
if __name__=='__main__':
    if '--entry-check' in sys.argv:
        sys.meta_path.insert(0,original.NoPhysical())
        sys.path.insert(0,str(R/'experiments/v1114_coupled_steering_mode'))
        from logic import Predictor,initial,kernel,Adapter
        sys.path.insert(0,str(R/'experiments/v1377_timed_handoff_witness'))
        from native_clock_contract import Timeline
        from gear_handoff import GearHandoff
        assert Path(GearHandoff.select.__code__.co_filename).resolve()==R/'experiments/v1346_measured_gear_handoff/gear_handoff.py'
        assert Path(Adapter.compute.__code__.co_filename).resolve()==R/'experiments/v1114_coupled_steering_mode/coupled_control.py'
        import json
        print(json.dumps(dict(passed=True,all_response_and_control_symbols_imported=True,models=0,analytical_native=0)))
    else:raise SystemExit(original.main())
