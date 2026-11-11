"""8GiB temporary ceiling, scoped only to this Phase campaign."""
from pathlib import Path
R=Path(__file__).resolve().parents[2];O=R/'runs/v1065_preflight_metadata_continuation_20261111';RAW=R/'runs/v858_nav2_verified/v1065';LIMIT=8*1024**3

def used():return sum(p.stat().st_size for root in [O,RAW]for p in root.rglob('*')if p.is_file()and not p.is_symlink())
def check(extra=0):
 if(O/'ROUND_WINDOW.json').exists():assert used()+extra<=LIMIT,'TEMPORARY8GIB_STORAGE_STOP'
 return True
