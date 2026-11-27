"""Primary local outcome metadata, no numerical imports or experiment launches."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import collections,hashlib,json,os
R=Path(__file__).resolve().parents[2];S=R/'runs'/Path(__file__).resolve().parent.name
METHODS=['RP-CCR','DWA','TEB','RPP','MPPI','SVG-MPPI','SCCR','PRIEST','PSF','PCBF']
paths={}
def read(p,expected=None):
 p=Path(p);p=p if p.is_absolute()else R/p;raw=p.read_bytes();h=hashlib.sha256(raw).hexdigest()
 assert expected is None or h==expected,'CANONICAL_RESULT_CHANGED:'+str(p)
 paths[str(p.relative_to(R))]=h;return json.loads(raw)
def kind(x):
 if not x.get('closed'):return 'unexecuted'
 if x.get('qualified_success'):return 'whole'
 if x.get('valid_finite_method_refusal')or x.get('status')=='VALID_FINITE_METHOD_REFUSAL_WITH_INDEPENDENT_PREFIX_AUDIT':return 'valid_refusal'
 return 'technical'
def main():
 assert os.sched_getaffinity(0)=={4};S.mkdir(exist_ok=False)
 base=read('runs/v1805_common_algorithm_registry/LEDGER.json');slots={(x['task_id'],x['method']):dict(x)for x in base['slots']}
 E=R/'runs/v1805_common_algorithm_registry/PARALLEL_METHOD_EVENTS'
 for stage in ['REGISTERED','CLOSED']:
  for p in sorted(E.glob('*.'+stage+'.json')):
   d=read(p);key=(d['task_id'],d['method']);assert key in slots;slots[key].update(d)
 counts={m:dict(total=0,closed=0,whole=0,valid_refusal=0,technical=0,unexecuted=0)for m in METHODS};rows=[]
 for x in sorted(slots.values(),key=lambda x:(x['task_id'],METHODS.index(x['method']))):
  c=counts[x['method']];c['total']+=1;k=kind(x);c[k]+=1;c['closed']+=bool(x.get('closed'))
  if x.get('closed'):read(x['result_path'],x['result_sha256'])
  rows.append(dict(task_id=x['task_id'],method=x['method'],course=x['case_id'],classification=k,result_path=x.get('result_path'),result_sha256=x.get('result_sha256')))
 assert len(rows)==120 and all(c['total']==12 for c in counts.values())
 totals={k:sum(c[k]for c in counts.values())for k in counts['RP-CCR']};assert totals==dict(total=120,closed=72,whole=7,valid_refusal=53,technical=12,unexecuted=48)
 for n in ['runs/v1942_sccr_applicability_decision/RESULT.json','runs/v2122_priest_quiescent_handoff/vehicle/COMPLETION.json','runs/v2125_filter_vehicle_handoff/components/PSF/COMPLETION.json','runs/v2125_filter_vehicle_handoff/components/PCBF/COMPLETION.json','runs/v2128_filter_segment_wire/components/PSF/COMPLETION.json','runs/v2129_filter_measured_clock/DRAFT_REGRESSION.json']:read(n)
 now=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat();result=dict(captured_local=now,counts=counts,totals=totals,rows=rows,models=0,optimizer_calls=0,physics=0,replay=0,new_physical_audit=0,new_formal_claims=0,base_ledger_unchanged=True)
 (S/'RESULT.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 report=['# Common algorithm results — 27 November 2026','',now,'','Ten methods × twelve locked same-known-course phase assignments. Merge frozen base ledger with parallel closed events; no component runs or historical heterogeneous studies are added. Six method systems each have twelve closed records. Twelve technical/evidence censors remain separate from valid method refusals.','', '| Method | Closed | Qualified whole arrival | Valid finite refusal | Technical / evidence censor | Unexecuted |','| --- | ---: | ---: | ---: | ---: | ---: |']
 for m in METHODS:
  c=counts[m];report.append(f"| {m} | {c['closed']}/12 | {c['whole']} | {c['valid_refusal']} | {c['technical']} | {c['unexecuted']} |")
 report+=['','Total:72closed,7whole,53valid refusal,12technical/evidence censors,48unexecuted. RP-CCR whole arrivals:7/12prespecified assignments(58.3%), with three technical censors retained in the denominator. This is a descriptive result; no statistical superiority, unseen-map generalization or equal-work comparison is established. Systems include declared engineering adapters/shared safety supervision, rather than untouched published implementations.','','## Each closed task','','| Task | Course | RP-CCR | DWA | TEB | RPP | MPPI | SVG-MPPI |','| --- | --- | --- | --- | --- | --- | --- | --- |']
 labels=dict(whole='到达',valid_refusal='有效拒绝',technical='技术/证据中断',unexecuted='未执行')
 for task in sorted({r['task_id']for r in rows}):
  selected={r['method']:r for r in rows if r['task_id']==task};report.append('| '+task+' | '+selected['RP-CCR']['course']+' | '+' | '.join(labels[selected[m]['classification']]for m in METHODS[:6])+' |')
 report+=['','## Remaining four methods','','- SCCR: original frozen policy requires camera/depth inputs missing from the common public-map/32-ray input contract. Applicability blocked;12unexecuted, not12algorithm failures.','- PRIEST: original-vehicle component failed the original complete-stop prediction reserve. No formal task has started.','- PSF: first-current5normal+2200stop component passed; later continuous interface reached2queries/10normal before a technical measured-time binding error.20query acceptance not passed;12formal tasks remain.','- PCBF: first-current5normal+2200stop component passed. Continuous-current acceptance remains incomplete;12formal tasks remain.','', 'Current measured-clock correction is software draft only (3real saved inputs,58synthetic decoder clock cases). No new vehicle admission or background experiment is active. Component prefix/audit passes do not count as whole navigation or formal comparison.','','## Evidence','','Per-task canonical result paths and verified SHA256 are recorded in runs/v2130_common_results_readout/RESULT.json; all input hashes in PROVENANCE.json. Old source/result/ledger bytes are unchanged. This report/helper is local and later than existing sealed source/runtime releases; no remote coverage is claimed.']
 report_path=R/'docs/paper_ras/working_20261126/COMMON_RESULTS_20261127.md';report_path.write_text('\n'.join(report)+'\n')
 assert all(hashlib.sha256((R/n).read_bytes()).hexdigest()==h for n,h in paths.items())
 (S/'PROVENANCE.json').write_text(json.dumps(dict(passed=True,closed=True,source_paths_sha256=paths,canonical_closed_results_verified=72,report_sha256=hashlib.sha256(report_path.read_bytes()).hexdigest(),models=0,optimizer_calls=0,physics=0,replay=0,new_formal_claims=0),indent=2)+'\n')
 print(json.dumps(dict(counts=counts,totals=totals,canonical_result_SHA_verified=72,report=str(report_path)),ensure_ascii=False))
if __name__=='__main__':main()
