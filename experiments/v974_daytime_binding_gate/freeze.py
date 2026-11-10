"""Freeze the exact scientific closure and the explicit new binding entry."""
import ast,hashlib,json,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;O=R/'runs/v974_daytime_binding_gate';assert not(O/'AUTHORIZATION.json').exists()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();old=json.loads((R/'experiments/v968_rpp_closed_loop_night/SOURCE_FREEZE.json').read_text())['files'];files={}
for rel,h in old.items():
 if rel.startswith(('runs/','records/')):continue
 assert sha(R/rel)==h;files[rel]=h
for name in ['v968_rpp_closed_loop_night','v972_daytime_binding_probe','v974_daytime_binding_gate','v975_daytime_closure']:
 for p in(R/'experiments'/name).iterdir():
  if p.is_file()and not(p.parent==C and p.name=='SOURCE_FREEZE.json'):
   if p.suffix=='.py':ast.parse(p.read_text(),str(p))
   files[str(p.relative_to(R))]=sha(p)
for p in O.glob('*.json'):files[str(p.relative_to(R))]=sha(p)
for p in(R/'runs/v972_daytime_binding_probe').glob('*.json'):files[str(p.relative_to(R))]=sha(p)
for rel in ['runs/v858_nav2_verified/v968/closed_handoff/physics/SETUP.json','runs/v858_nav2_verified/v968/closed_handoff/physics/INITIAL_STATE.npz']:
 files[rel]=sha(R/rel)
(C/'SOURCE_FREEZE.json').write_text(json.dumps(dict(final=True,files=files,models_at_freeze=0,integrations_before_freeze=0,frozen_unix=time.time()),indent=2)+'\n');print(json.dumps(dict(frozen_files=len(files),models=0,integrations=0)))
