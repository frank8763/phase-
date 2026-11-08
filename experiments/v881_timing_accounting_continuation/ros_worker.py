"""Actual standalone entry: import paths explicit before any ROS/model import."""
import sys
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1]
sys.path[:0]=[str(C),str(R/'experiments/v862_ready_static')]
from ros_bridge import main
if __name__=='__main__':sys.exit(main())
