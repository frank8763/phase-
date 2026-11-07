"""One immutable supplemental metadata snapshot, no models or network."""
import hashlib,json,zipfile
from pathlib import Path
def close_ops(repo,root,own):
 target=repo/'evidence/rpccr_early_joint_90_ops_20261106';assert not target.exists();target.mkdir()
 files={p for p in root.rglob('*')if p.is_file()and not p.is_symlink()and p.suffix not in['.pyc','.lock']and p.name not in['campaign.console','inhibitor.console']}
 files.update(p for p in own.parent.joinpath('early_joint_90_20261106').glob('*.py'))
 for p in [repo/'CURRENT_EXPERIMENT.json',repo/'RPCCR_EARLY_JOINT_90_AUTHORIZATION_20261106.json',repo/'docs/RPCCR_EARLY_JOINT_90_20261106_REPORT.md',repo/'docs/RPCCR_EARLY_JOINT_90_20261106_PLAN.md',repo/'runs/v841_early_joint/finalize.console',repo/'runs/v841_early_joint/transport.console',repo/'runs/v841_early_joint/driver.console',repo/'runs/v841_early_joint/finalize.console',repo/'runs/v841_early_joint/transport.console',repo/'runs/v841_early_joint/audit_saved.console']:
  if p.exists():files.add(p)
 inventory=[]
 with zipfile.ZipFile(target/'OPERATIONS_SNAPSHOT.zip','x',compression=zipfile.ZIP_DEFLATED)as archive:
  for p in sorted(files):
   data=p.read_bytes();name=str(p.relative_to(repo));h=hashlib.sha256(data).hexdigest();archive.writestr(name,data);inventory.append(dict(path=name,bytes=len(data),sha256=h))
 with zipfile.ZipFile(target/'OPERATIONS_SNAPSHOT.zip')as archive:
  for x in inventory:
   data=archive.read(x['path']);assert len(data)==x['bytes']and hashlib.sha256(data).hexdigest()==x['sha256']
 result=dict(status='SOURCE_SNAPSHOT_DECOMPRESSED_SHA_VERIFIED',sources=len(inventory),models=0,integrations=0,network_calls=0,inventory=inventory,raw_deleted=False,active_log_exclusion='campaign.console and inhibitor.console remain raw, avoiding self-referential archive')
 (target/'MANIFEST.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 (root/'CLOSED_OPERATIONS_ARCHIVE.json').write_text(json.dumps(dict(status=result['status'],archive=str(target.relative_to(repo)),raw_deleted=False),indent=2)+'\n')
