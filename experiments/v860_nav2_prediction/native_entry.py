"""Original qualified Adapter and exact factory cwd repair; no new physical controller."""
import runpy,sys
from pathlib import Path
R=Path(__file__).resolve().parents[2]
runpy.run_path(str(R/'experiments/v858_nav2_verified_entry/native_entry.py'),run_name='qualified_cwd_transaction')
import native_worker
if __name__=='__main__':sys.exit(native_worker.main())
