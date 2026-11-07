"""Register one independent offline night; never extend any old window."""
import datetime,json,time
from pathlib import Path
from zoneinfo import ZoneInfo
repo=Path(__file__).resolve().parents[2]
root=repo/'runs/overnight_recovery_20261105'
path=repo/'RPCCR_OVERNIGHT_RECOVERY_AUTHORIZATION_20261105.json'
assert not path.exists()
deadline=datetime.datetime(2026,11,6,8,tzinfo=ZoneInfo('Asia/Shanghai')).timestamp()
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
auth=dict(user_instruction='怎么回事？继续开启今天晚上的通宵实验；合理安排实验，无人看守；我离开之后你会断网；认真思考分析',
 authorized_at=datetime.datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),absolute_deadline_unix=deadline,
 hard_stop_beijing='2026-11-06T08:00:00+08:00',deadline_basis='New round; morning08:00 stated to user; never extends old V828/other windows',
 max_scientific_candidates=1,scientific_scope='Complete ranked return search over existing nominal candidates with unchanged progress and full328 admission gates',
 qualification='Zero-model saved evidence regression/callsite/positive and negative gate tests before freeze',
 development_tasks=['V828_failed10060002','V828_failed10060008','original10010002_NS','original10010001_WE','original10010003_EW'],
 development_mains_max=5,conditional_complete_repeats_max=5,first_functional_or_safety_evidence_failure_stops=True,
 new_confirmation=0,reason_no_fresh_confirmation='Tonight is targeted known-failure and three-route development; full new24 start budget unavailable',
 post_freeze_repairs=0,additional_action_pool=False,threshold_changes=False,nav_public_cap=1200,nav_soft_s=1200,nav_hard_s=1500,nav_outer_s=1505,
 t0_internal_s=120,t0_outer_s=125,model_physics_only_run_phase=True,single_cpu_sequential_execution_lock=True,
 training_updates=0,SAC=0,real_robot=0,stage_access=0,subagents=0,external_messages=0,old_failures_sources_deadlines_immutable=True,
 offline_controller_required=True,chat_monitor=False,automatic_network_operations=False,
 raw_evidence_deleted=False,finalization='Zero-model independent persisted audit, full source/decompressedSHA verification and32MiB lossless transport; restore originalREVIEW_PENDING')
assert time.time()<deadline
dump(path,auth);dump(root/'LEDGER.json',dict(status='PREPARING_ZERO_MODEL',closed=False,absolute_deadline_unix=deadline,scientific_candidates_started=0,models_started=False,confirmation_started=False))
print(json.dumps(dict(registered=True,absolute_deadline_unix=deadline,new_models=0)))
