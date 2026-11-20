"""New output binding only; complete numerical backend remains frozen V1415."""
import importlib.util
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
spec=importlib.util.spec_from_file_location('v1417_frozen_full_backend',R/'experiments/v1415_unified_causal_witness/production_entry.py');backend=importlib.util.module_from_spec(spec);spec.loader.exec_module(backend)
backend.O=O
assert backend.C==R/'experiments/v1415_unified_causal_witness'
if __name__=='__main__':raise SystemExit(backend.main())
