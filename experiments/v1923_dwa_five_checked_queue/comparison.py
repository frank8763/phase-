"""Read-only common result census; no re-audit or scientific denominator edit."""
import hashlib,json,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];S=R/'runs/v1923_dwa_five_checked_queue'
def main():
    p=R/'runs/v1805_common_algorithm_registry/LEDGER.json';ledger=json.loads(p.read_text());rows=[]
    for method in dict.fromkeys(r['method']for r in ledger['slots']):
        slots=[r for r in ledger['slots']if r['method']==method]
        rows.append(dict(method=method,denominator=len(slots),closed=sum(bool(r['closed'])for r in slots),whole=sum(r.get('qualified_success')is True for r in slots),valid_refusal=sum(r.get('status')=='VALID_FINITE_METHOD_REFUSAL_WITH_INDEPENDENT_PREFIX_AUDIT'for r in slots),technical=sum(r.get('status')=='TECHNICAL_OR_UNQUALIFIED_EVIDENCE_CENSOR'for r in slots),unexecuted=sum(not r['registered']for r in slots)))
    value=dict(rows=rows,ledger_path=str(p.relative_to(R)),ledger_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),unix=time.time(),all120_denominators_preserved=True,no_statistical_superiority_claim=True,unadmitted_methods_not_complete=True)
    (S/'COMMON_COMPARISON_CENSUS.json').write_text(json.dumps(value,indent=2)+'\n')
    text='# Common algorithm evidence census · 2026-11-25\n\n'
    text+='Original common120 and separate ablation20 denominators remain. Historical SCCR/DWA results use a different contract and are not pooled. Unexecuted/adaptation gaps remain explicit; zero qualified arrivals alone does not establish algorithm superiority.\n\n'
    text+='|Method|Total|Closed|Whole goal|Valid finite refusal|Technical censor|Unexecuted|\n|---|---:|---:|---:|---:|---:|---:|\n'
    for r in rows:text+='|'+ '|'.join(str(r[k])for k in ['method','denominator','closed','whole','valid_refusal','technical','unexecuted'])+'|\n'
    text+='\nMethod/source adaptations and per-task source, control, safety, replay, audit and remote barriers must accompany these counts. No denominator drops or aggregate model-work/equal-work claims. Fixed20 mechanism tests are closed; clean matched pairs with identical trajectories do not establish mechanism benefit.\n'
    (R/'docs/COMMON_COMPARISON_CENSUS_20261125.md').write_text(text)
    print(json.dumps(value),flush=True)
if __name__=='__main__':main()
