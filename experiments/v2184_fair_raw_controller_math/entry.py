"""Refuse before any numerical import unless this exact new scope is admitted."""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from context import numerical_admission

def main():
    try:a,w,files=numerical_admission()
    except BaseException as e:
        assert not any(n in sys.modules for n in ['numpy','ctypes','mujoco','torch'])
        print(json.dumps(dict(refused_before_numerical_import=True,error=repr(e),algorithm_loads_constructors_queries_models_physics=0)),flush=True)
        return 77
    # Runtime implementation is an explicit remaining prerequisite; its absence
    # must never be converted into an admitted success or a silent no-op.
    import numeric
    return numeric.execute(a,w,files)

if __name__=='__main__':raise SystemExit(main())
