"""Own frozen manifest; unchanged V862 engine and physical Adapter."""
import sys
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent
sys.path.insert(0,str(R/"experiments/v862_ready_static"))
import ros_bridge as engine
engine.C=C
if __name__=="__main__":sys.exit(engine.main())
