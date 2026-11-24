"""Per-assignment runtime transport; exact source sync reused, no push/ref."""
import importlib.util
from pathlib import Path
R=Path(__file__).resolve().parents[2]
p=R/'experiments/v1914_dwa_hybrid_source_recovery/deliver.py'
s=importlib.util.spec_from_file_location('v1915_same_source_delivery',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
if __name__=='__main__':raise SystemExit(m.main(runtime=True))
