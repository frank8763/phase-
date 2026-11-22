"""Install the unchanged original history-read guard before factory hook scope."""
import hashlib,os,sys,types
from pathlib import Path
R=Path(__file__).resolve().parents[2]
ORIGINAL=R/'experiments/v1180_fresh_recovery_chain/chain_tools.py'

def install(output,source):
 output=Path(output).resolve()
 assert output.is_relative_to(R/'runs')and output.is_dir()and not output.is_symlink()
 assert hashlib.sha256(ORIGINAL.read_bytes()).hexdigest()==source[str(ORIGINAL.relative_to(R))]
 module=compile(ORIGINAL.read_text(),str(ORIGINAL),'exec',dont_inherit=True)
 functions=[v for v in module.co_consts if isinstance(v,types.CodeType)and v.co_name=='history_guard']
 assert len(functions)==1
 function=types.FunctionType(functions[0],dict(Path=Path,os=os,sys=sys),'history_guard')
 assert function.__closure__is None
 function(output)
 return dict(passed=True,original_history_guard_code_exact=True,
             source_sha256=source[str(ORIGINAL.relative_to(R))],output=str(output),
             before_initializer_registration_scope=True,models=0)
