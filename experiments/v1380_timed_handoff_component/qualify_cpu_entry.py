"""Entry-only correction: launch original CPU2 context checks on CPU2."""
import subprocess
from pathlib import Path
import qualify as original
R=Path(__file__).resolve().parents[2]
original.O=R/'runs/v1380_timed_handoff_component/qualification02'
run=subprocess.run
def bound(command,*args,**kwargs):
    return run(['taskset','-c','2',*command],*args,**kwargs)
subprocess.run=bound
if __name__=='__main__':original.main()
