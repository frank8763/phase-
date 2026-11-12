"""Reuse the original V1085 root deadline; model continuation disabled by default."""
import json,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];ORIGINAL=R/'experiments/rpccr_execution_core/fresh_campaign.py'
def patched_source():
 source=ORIGINAL.read_text();start=source.index('wall=time.time();mono=time.monotonic();w=dict(');end=source.index(";dump(O/'ROUND_WINDOW.json',w)",start)
 source=source[:start]+"w=json.loads(Path(cfg['window_reference']).read_text());assert min(w['absolute_deadline_unix']-time.time(),w['hard_stop_monotonic']-time.monotonic())>2000"+source[end:]
 old='signal.setitimer(signal.ITIMER_REAL,5400)';assert source.count(old)==1;source=source.replace(old,"signal.setitimer(signal.ITIMER_REAL,max(.001,min(w['absolute_deadline_unix']-time.time(),w['hard_stop_monotonic']-time.monotonic())))")
 old="CORE/cfg['worker']";assert source.count(old)==1;source=source.replace(old,"Path(cfg['worker_path'])")
 return source
if __name__=='__main__':
 cfg=json.loads(Path(sys.argv[1]).read_text());O=Path(cfg['run_root']);authority=json.loads((O/'ENTRY_CONTINUATION_AUTHORITY.json').read_text());assert authority['permitted']is True,'WAITING_FOR_UNIQUE_ENTRY_CONTINUATION_AUTHORITY';previous=json.loads((R/'runs/v1085_fresh_ns_validation/COMPLETION.json').read_text());assert previous['closed']and previous['counts']['new_actual_native']==0;assert authority['root_deadline_unix']==json.loads(Path(cfg['window_reference']).read_text())['absolute_deadline_unix'];exec(compile(patched_source(),str(ORIGINAL),'exec'),dict(__name__='__main__',__file__=str(ORIGINAL)))
