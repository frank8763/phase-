"""New root/model binding of unchanged V1158 fixed regression evaluator."""
from pathlib import Path
import sys
import importlib.util

C=Path(__file__).resolve().parent;R=C.parents[1]
sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'))
from resource_policy import apply
apply()


def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


def main():
    old_path=R/'experiments/v1158_excited_steering_model'
    sys.path.insert(0,str(old_path))
    evaluator=load('v1159_fixed_regression_evaluator',old_path/'qualify.py')
    evaluator.C=C;evaluator.O=R/'runs/v1159_bounded_steering_load'
    evaluator.model=load('v1159_fixed_bounded_model',C/'model.py')
    evaluator.accelerator=load('v1159_fixed_bounded_engine',C/'engine.py')
    return evaluator.main()


if __name__=='__main__':sys.exit(main())
