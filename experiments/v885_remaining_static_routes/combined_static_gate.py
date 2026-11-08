"""Combine source-identical completed development evidence; never mix confirmation denominator."""
import hashlib,json,sys
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v885_remaining_static_routes'
sys.path[:0]=[str(C),str(R/'experiments/v862_ready_static')]
from authority import validate_ns_anchor
def read(p):return json.loads(p.read_text())
def main():
    completion=read(O/'COMPLETION.json');finalized=read(O/'FINALIZED.json');audit=read(O/'FINAL_INDEPENDENT_AUDIT.json');anchor=validate_ns_anchor();pairs={}
    for case in ['WEST_EAST','EAST_WEST']:
        p=O/(case+'_REPEAT_COMPARISON.json');pairs[case]=read(p).get('passed')is True if p.exists()else False
    rows=completion['rows'];passed=bool(anchor and completion['status']=='REMAINING_STATIC_TWO_ROUTES_PASSED'and len(rows)==4 and all(x['passed']for x in rows)and all(pairs.values())and finalized['source_and_decompressed_sha_verified']and finalized['part_reassembly_sha_verified']and audit['passed'])
    result=dict(passed=passed,combined_three_route_static_development_passed=passed,NS_reused_source_exact_main_and_repeat=anchor,new_WE_and_EW_pairs=pairs,new_navigation_attempted=len(rows),new_navigation_unexecuted=4-len(rows),same_scientific_version='V884_FEASIBLE_RPP',dynamic_navigation=0,new24_executed=0,confirmation_denominator=0,scope='Three fixed static development routes with complete same-config reruns; not independent dynamic confirmation',models_this_gate=0,integrations_this_gate=0)
    (O/'COMBINED_THREE_ROUTE_GATE.json').write_text(json.dumps(result,indent=2)+'\n')
    p=R/'CURRENT_EXPERIMENT.json';j=read(p);j['v885_remaining_static_routes']['combined_three_route_static_development_passed']=passed
    if passed:j['latest_nav2_simulation'].update(status='V884_V885_SAME_VERSION_THREE_STATIC_DEVELOPMENT_ROUTES_PASSED',static_three_route_passed=True,dynamic_passed=False)
    p.write_text(json.dumps(j,indent=2)+'\n');print(json.dumps(result),flush=True)
if __name__=='__main__':main()
