"""Once registered new writer-census source target; zero numerical authority."""
import importlib.util
from pathlib import Path
s=importlib.util.spec_from_file_location('v1612_source_target',Path(__file__).with_name('source_target.py'))
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
if __name__=='__main__':raise SystemExit(m.main())
