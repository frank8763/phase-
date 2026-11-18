"""Original all-native static evidence audit, new same-format plan directory."""
import sys,types
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];sys.path.insert(0,str(C));from afternoon_tools import *
def module():
 sys.path.insert(0,str(R/'experiments/v1114_coupled_steering_mode'));s=(R/'experiments/v1114_coupled_steering_mode/audit.py').read_text().replace('from common import C,R,dump','from afternoon_tools import C,R,dump');s=s.replace('8100','8000');m=types.ModuleType('afternoon_static_audit');m.__file__=str(C/'static_audit.py');exec(compile(s,m.__file__,'exec'),m.__dict__);return m
if __name__=='__main__':
 proof=module().audit(json.loads(Path(sys.argv[1]).read_text()));print(encode(proof));sys.exit(0 if proof['passed']else 1)
