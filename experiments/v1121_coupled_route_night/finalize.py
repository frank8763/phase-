"""One zero-model local evidence archive; defer network-dependent delivery."""
import sys,json,fcntl,time,hashlib,importlib.util,os
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1121_coupled_route_night'
sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
apply()
def dump(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def main():
 lock=(O/'finalize.lock').open('a+')
 try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 except BlockingIOError:return
 if(O/'FINALIZED.json').exists():return
 assert(O/'COMPLETION.json').exists();completion=json.loads((O/'COMPLETION.json').read_text());assert completion['closed'];guard=(O/'GUARD.bin').read_bytes();assert(R/'REVIEW_PENDING').read_bytes()==guard
 physical=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(physical,fcntl.LOCK_EX|fcntl.LOCK_NB)
 spec=importlib.util.spec_from_file_location('night_closed_stream_archive',R/'experiments/v1065_preflight_metadata_continuation/archive.py');arc=importlib.util.module_from_spec(spec);spec.loader.exec_module(arc);files=[];excluded={'campaign.console','watchdog.console','finalize.console'}
 for p in arc.walk(O):
  if p.name in excluded or any(part in ['cloud','remote_readback']for part in p.relative_to(O).parts):continue
  files.append(p)
 files.extend(arc.walk(C))
 for t in json.loads((C/'TASKS.json').read_text()):
  out=Path(t['output'])
  if out.exists():files.extend(arc.walk(out))
 cfg=json.loads((O/'CONFIG.json').read_text());report=R/cfg['report']
 if report.exists():files.append(report)
 from campaign import used
 record,catalog=arc.package(R,files,O/'cloud','v1121_overnight',lambda:used()+128*1024**2<cfg['temporary_limit_bytes']);dump(O/'ARCHIVE.json',record);dump(O/'INVENTORY.json',{'files':catalog});answer={'closed':True,'local_source_member_sha_readback_passed':True,'part_reassembly_sha_passed':True,'source_members':len(catalog),'archive_bytes':record['archive_bytes'],'scientific_three_route_passed':bool(completion.get('three_route_passed')),'scientific_fixed24_passed':bool(completion.get('fixed24_passed')),'network_delivery_pending':True,'no_unverified_raw_cleanup':True,'models':0,'physical_integrations':0,'excluded_active_logs':sorted(excluded)};dump(O/'FINALIZED.json',answer);dump(O/'GITHUB_DELIVERY_PENDING.json',{'pending':True,'reason':'offline campaign; source/member/part SHA locally verified; upload selected records on next connected review','archive':'runs/v1121_coupled_route_night/ARCHIVE.json','raw_preserved':True});print(json.dumps(answer),flush=True)
if __name__=='__main__':main()
