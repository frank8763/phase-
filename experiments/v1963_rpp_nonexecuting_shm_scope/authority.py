"""Pure, fail-closed authority for exactly one synthetic RPP API instance."""
def validate(a,*,now,mono,boot,freeze_sha,fixture_sha,recovery_sha):
 assert a['scope']=='RPP_SYNTHETIC_STRAIGHT_API_ONLY'and a['controller_constructor_cap']==a['valid_solver_cap']==1 and a['physics_authorized']is False,'RPP_COMPONENT_SCOPE'
 assert a['boot_id']==boot and now<a['absolute_deadline_unix']and mono<a['hard_stop_monotonic'],'RPP_COMPONENT_CLOCK'
 assert a['source_freeze_sha256']==freeze_sha and a['fixture_sha256']==fixture_sha and a['source_recovery_sha256']==recovery_sha,'RPP_COMPONENT_SOURCE_BINDING'
 return True
