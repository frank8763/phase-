"""User-authorized zero-integration rendering in the existing Phase namespace."""
from pathlib import Path
import importlib.util,sys,subprocess
repo=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('phase_render_namespace',repo/'tools/isolate.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
script=Path(__file__).resolve().parent/'render_static.py'
raise SystemExit(subprocess.run(module.command(script,writable=True)+sys.argv[1:],check=False,timeout=1805).returncode)
