"""Qualified original directory transaction plus the one declared Adapter change."""
import runpy,sys
from pathlib import Path
from steering_adapter import Adapter
R=Path(__file__).resolve().parents[2]
runpy.run_path(str(R/'experiments/v858_nav2_verified_entry/native_entry.py'),run_name='qualified_cwd_transaction')
import vehicle
vehicle.Adapter=Adapter
if __name__=='__main__':
 import native_worker
 sys.exit(native_worker.main())
