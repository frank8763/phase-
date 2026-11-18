"""Pure frozen denominator gates; development and repeats never enter main."""
def main_gate(rows):
    mains=[r for r in rows if r['role']=='main'and ((r.get('result')or{}).get('new_actual_native')or 0)>0];slots=[r['slot']for r in mains]
    assert len(slots)==len(set(slots))and all(1<=s<=24 for s in slots)
    full=sorted(slots)==list(range(1,25));success=sum(r['functional_passed']and r['safety_evidence_passed']for r in mains)
    byroute={c:sum(r['case_id']==c and r['functional_passed']and r['safety_evidence_passed']for r in mains)for c in['WEST_EAST','NORTH_SOUTH','EAST_WEST']}
    bydirection={d:sum(r['direction']==d and r['functional_passed']and r['safety_evidence_passed']for r in mains)for d in['POSITIVE_AXIS','NEGATIVE_AXIS']}
    passed=full and success>=23 and min(byroute.values())>=7 and min(bydirection.values())>=11 and all(r['safety_evidence_passed']for r in mains)
    return dict(passed=bool(passed),full24_executed=full,executed=len(mains),successes=success,failures=len(mains)-success,by_route_successes=byroute,by_direction_successes=bydirection,full_denominator_success_rate=success/24 if full else None)
def final_gate(rows,repeats):
    m=main_gate(rows);fixed={1,9,17};done={r['slot']for r in rows if r['role']=='repeat'and r['functional_passed']and r['safety_evidence_passed']}
    return bool(m['passed']and done==fixed and set(map(int,repeats))==fixed and all(p['passed']for p in repeats.values()))
