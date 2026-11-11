import importlib.util
from pathlib import Path
R=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location('v1045_qualified_curvature_model',R/'experiments/v1044_curvature_speed_prediction/whole_input.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
Predictor=m.Predictor;PARAMETERS=m.PARAMETERS;initial=m.initial;checks=m.checks;public_setup=m.public_setup
