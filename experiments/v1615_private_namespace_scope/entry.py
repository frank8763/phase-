"""Once new namespace ownership SOURCE target; no numerical permission."""
import importlib.util
from pathlib import Path
s=importlib.util.spec_from_file_location('v1615_registered_namespace_target',Path(__file__).with_name('source_target.py'))
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
if __name__=='__main__':raise SystemExit(m.main())
