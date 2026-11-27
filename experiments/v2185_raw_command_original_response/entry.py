"""Refuse before NumPy, model imports or a Predictor when not admitted."""
import json,sys
from context import require_admission

def main():
    try:a,w,source=require_admission()
    except BaseException as e:
        assert not any(n in sys.modules for n in ['numpy','mujoco','torch','ctypes'])
        print(json.dumps(dict(refused_before_numerical_import=True,error=repr(e),new_predictors_models_physics=0)));return 77
    import numeric
    return numeric.execute(a,w,source)
if __name__=='__main__':raise SystemExit(main())
