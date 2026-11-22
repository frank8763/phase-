"""Registered once new lossless receipt source target; no numerical permission."""
import importlib.util
from pathlib import Path
s=importlib.util.spec_from_file_location('v1609_registered_source_target',Path(__file__).with_name('source_target.py'))
module=importlib.util.module_from_spec(s);s.loader.exec_module(module)
if __name__=='__main__':raise SystemExit(module.main())
