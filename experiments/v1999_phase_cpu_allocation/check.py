"""Only identity-bound known Phase trees; Stage reservation from user, not inspection."""
from pathlib import Path
import json,os,time,hashlib
R=Path(__file__).resolve().parents[2];O=R/'runs/v1999_phase_cpu_allocation';S=R/'runs/v1990_rpp_unexecuted_output_audit';ALLOWED={2,4,5,6,7};STAGE_REPORTED={8,10,12}
read=lambda p:json.loads(p.read_text())
def identity(pid):
 p=Path('/proc',str(pid),'stat');return p.read_text().split(') ',1)[1].split()[19]
def main():
 os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();topology={}
 for cpu in sorted(ALLOWED|STAGE_REPORTED):
  p=Path('/sys/devices/system/cpu')/f'cpu{cpu}'/'topology';siblings=set()
  for span in(p/'thread_siblings_list').read_text().strip().split(','):
   if '-'in span:a,b=map(int,span.split('-'));siblings.update(range(a,b+1))
   else:siblings.add(int(span))
  topology[cpu]=dict(core_id=int((p/'core_id').read_text()),package_id=int((p/'physical_package_id').read_text()),siblings=sorted(siblings))
 reserved=set().union(*(set(topology[c]['siblings'])for c in STAGE_REPORTED));assert not(ALLOWED&reserved);assert len({(topology[c]['package_id'],topology[c]['core_id'])for c in ALLOWED})==5
 roots=[]
 for p in [S/'NIGHT_LAUNCHER_IDENTITY.json',S/'CAMPAIGN_ONCE_CLAIM.json']:
  v=read(p);assert v['boot_id']==boot;pid=v['pid']
  if Path('/proc',str(pid)).exists():assert identity(pid)==v['start_ticks'];roots.append(pid)
 progress=read(S/'CAMPAIGN_PROGRESS.json');roundbase=S/'rounds'/progress['active'];p=roundbase/'OWNED_CHILD.json'
 if p.exists():
  v=read(p);assert v['boot_id']==boot;pid=v['pid']
  if Path('/proc',str(pid)).exists():assert identity(pid)==v['start_ticks'];roots.append(pid)
 known=set();pending=list(roots);races=[]
 while pending:
  pid=pending.pop()
  if pid in known:continue
  task=Path('/proc',str(pid),'task')
  if not task.exists():races.append(pid);continue
  known.add(pid)
  for t in list(task.iterdir()):
   p=t/'children'
   try:pending.extend(map(int,p.read_text().split()))
   except FileNotFoundError:races.append(int(t.name))
 rows=[]
 for pid in sorted(known):
  task=Path('/proc',str(pid),'task')
  if not task.exists():races.append(pid);continue
  for thread in list(task.iterdir()):
   tid=int(thread.name)
   try:
    before=set(os.sched_getaffinity(tid));after=before
    if not before<=ALLOWED:os.sched_setaffinity(tid,{5});after=set(os.sched_getaffinity(tid))
    assert after<=ALLOWED and not(after&reserved)
    rows.append(dict(phase_pid=pid,tid=tid,before=sorted(before),after=sorted(after),changed=before!=after))
   except ProcessLookupError:races.append(tid)
 policy=dict(passed=True,phase_allowed=sorted(ALLOWED),stage_user_reported=sorted(STAGE_REPORTED),stage_reserved_with_SMT=sorted(reserved),roles={'vehicle':2,'geometry':4,'supervision_IO':5,'MPPI_native_math':6,'SVG_native_math':7},topology=topology,known_Phase_root_pids=roots,threads=rows,raced_ids=races,Stage_process_or_resource_inventory_accessed=False,actual_Stage_affinity_independently_verified=False,Phase_affinity_disjoint_user_reported_Stage_physical_cores=True,models=0,solver_calls=0,physical_native=0,replay_native=0,unix=time.time(),late_outside_prior_source_archive=True)
 p=O/'RESULT.json';assert not p.exists();p.write_text(json.dumps(policy,indent=2)+'\n');print(json.dumps(dict(passed=True,phase=sorted(ALLOWED),stage_reserved=sorted(reserved),Phase_processes=len(known),Phase_threads=len(rows),wrapper_threads_restricted=sum(x['changed']for x in rows),Stage_accessed=False)))
if __name__=='__main__':main()
