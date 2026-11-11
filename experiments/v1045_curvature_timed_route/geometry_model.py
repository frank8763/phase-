"""Exact existing safety reserves, imported by absolute source path."""
import importlib.util
from pathlib import Path
R=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location('v1045_original_geometry',R/'experiments/v1023_dense_input_route/geometry_model.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
ref=m.ref;REQUIRED=m.REQUIRED;RHO=m.RHO
