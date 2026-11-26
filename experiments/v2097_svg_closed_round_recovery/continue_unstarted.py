"""Scoped import fix for the recovery entry which never reached network I/O."""
from pathlib import Path
import importlib.util,json,sys
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;D=R/'runs'/C.name;T=R/'runs/v2095_svg_common_full_route/runtime_archives/common_01__SVGMPPI'
x=json.loads((D/'RESULT.json').read_text());assert x['closed']and not x['passed']and x['first_error']=='''ModuleNotFoundError("No module named 'reserved_census'")'''
assert not(T/'remote_delivery_dualroute_2097').exists(),'PRIOR_RECOVERY_MUST_HAVE_ZERO_HTTP_AND_ZERO_UPLOAD'
s=importlib.util.spec_from_file_location('original_zero_IO_recovery_entry',C/'recover.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);m.W=D/'unstarted_entry_continuation';m.W.mkdir(exist_ok=False)
before=sys.path[:];sys.path.insert(0,str(R/'experiments/v2095_svg_common_full_route'))
try:raise SystemExit(m.recover())
finally:sys.path[:]=before
