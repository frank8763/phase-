"""Original metadata and gates, with one explicitly parameterized predictor."""
import importlib.util,json
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1]
s=importlib.util.spec_from_file_location('v1044_original_whole_input',R/'experiments/v1023_dense_input_route/whole_input.py');old=importlib.util.module_from_spec(s);s.loader.exec_module(old)
s=importlib.util.spec_from_file_location('v1044_curvature_predictor',C/'model.py');new=importlib.util.module_from_spec(s);s.loader.exec_module(new)
Predictor=new.Predictor;initial=old.initial;checks=old.checks;public_setup=old.public_setup;virtual=new.virtual;virtual_rate=new.virtual_rate
PARAMETERS=json.loads((C/'PARAMETERS.json').read_text())
