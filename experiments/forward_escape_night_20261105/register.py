"""Explicit new user continuation, same morning hard stop; old V830 stays closed."""
import datetime,json,time
from pathlib import Path
from zoneinfo import ZoneInfo
repo=Path(__file__).resolve().parents[2];root=repo/'runs/forward_escape_night_20261105';path=repo/'RPCCR_FORWARD_ESCAPE_NIGHT_AUTHORIZATION_20261105.json';assert not path.exists()
auth=dict(user_instruction=['思考分析，下一步继续通宵的实验','接着将动态的跑出来，然后明天进入算法对照'],authorized_at=datetime.datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),absolute_deadline_unix=1793923200.,hard_stop_beijing='2026-11-06T08:00:00+08:00',deadline_not_extended=True,old_v830_not_reopened=True,
 max_scientific_candidates=1,post_freeze_repairs=0,component_fixed_states=[495,527],component_source='V830 main_slot01/old V82810060002 exactly identical physical trace',component_cap_s=1200,old_replay_native=4216,private_native_cap=360400,component_actual_native_cap=656,component_repeat_native_cap=656,
 scientific_change='Only try_handover while executing a retained backup may append5registered steers x wheel8/12 forward tails, brake after160native; only after original16 and forward4x5 all rejected. Existing ranking, progress.02 and complete328 gates unchanged.',
 component_gate='At least one fixed state must supply a complete forward-escape certificate; each selected branch actual328 and complete repeat plus independent full source/geometry/control/coverage audit and archive verification.',
 conditional_navigation_tasks=['10060002','10060008','10010002_NS','10010001_WE','10010003_EW'],navigation_main_max=5,conditional_repeat_max=5,new24_confirmation=0,
 first_functional_or_safety_evidence_failure_stops=True,nav_public_cap=1200,nav_soft_s=1200,nav_hard_s=1500,nav_outer_s=1505,t0_internal_s=120,t0_outer_s=125,
 future_comparison='Prepare matched scene/seed/safety/budget plan for tomorrow; no automatic comparison starts before verified complete dynamic development. Full new24 acceptance remains separate and unexecuted.',
 training_updates=0,SAC=0,stage_access=0,real_robot=0,all_models_only_run_phase=True,single_cpu_execution_lock=True,subagents=0,chat_monitor=False,network_calls=0,raw_deleted=False,offline_controller=True)
assert time.time()+21600<auth['absolute_deadline_unix']
path.write_text(json.dumps(auth,ensure_ascii=False,indent=2)+'\n');(root/'LEDGER.json').write_text(json.dumps(dict(status='PREPARING',closed=False,absolute_deadline_unix=auth['absolute_deadline_unix'],candidates_started=0,active_simulation=False,comparison_started=False),indent=2)+'\n')
print('REGISTERED_NEW_CONTINUATION_SAME_MORNING_DEADLINE')
