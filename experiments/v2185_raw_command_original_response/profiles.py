"""Fixed original shadow/admission order; no rescue of a shadow refusal."""
METHODS=('DWA_SIGNED_GEAR_SHARED_PATH','RPP_RAW_ABI2')
def plans(cases):
    assert type(cases)is list and len(cases)==2 and [r['method']for r in cases]==list(METHODS)
    return [dict(case,profile=profile,command_native=n)for case in cases for profile,n in [('shadow',10),('admission',5)]]
def shadow_refused(case,passed,blocked):
    assert case['method']in METHODS and case['profile']in {'shadow','admission'}and type(passed)is bool
    assert case['command_native']==(10 if case['profile']=='shadow'else 5)
    if case['profile']=='shadow'and not passed:blocked.add(case['method'])
