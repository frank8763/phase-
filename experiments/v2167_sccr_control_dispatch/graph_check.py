from source_graph import *
import os,json
assert os.sched_getaffinity(0)=={0}
S=R/'runs'/Path(__file__).resolve().parent.name;assert not(S/'SOURCE_GRAPH.json').exists()
outer=(ROOT/'envs/phase22/mkmini_phase22_v1_continuous_corridor_env.py','MkMiniPhase22V1ContinuousCorridorEnv');inner=(ROOT/'training/phase6_clean/envs/mkmini_phase6_lidar_camera_astar_sac_env.py','MkMiniPhase6LidarCameraAstarSacEnv')
conditional=ROOT/'training/phase14_lidar_depth_nav/envs/mkmini_phase14_phase9_yawsync_fast_nav_env.py';branches=[];files={};unavailable=[]
for index in range(3):
 g=Graph({(conditional,'Phase14BaseEnv'):index});providers={}
 if index==2:
  missing=ROOT/'training/phase9_static_no_dynamic/envs/mkmini_phase9g2_safe_speed_steer_env.py';assert not missing.exists();unavailable.append(dict(branch_index=2,source=str(missing.relative_to(R)),reason='source absent; runtime branch cannot be presumed available'));continue
 for name in ['_base_action','step','_phase17_apply_safety_shield','_phase21_compute_corridor_state','_phase21_sensor_points','_phase21_v3_build_detour']:
  item,fn=g.provider(outer,name);assert item;providers[name]=dict(provider=g.label(item),line=fn.lineno)
 branches.append(dict(conditional_base_index=index,mro=[g.label(x)for x in g.mro(outer)],providers=providers));files.update({str(p.relative_to(R)):sha(p)for p in g.trees})
assert len(branches)==2 and branches[0]['providers']==branches[1]['providers'],'OUTER_ENTRY_PROVIDER_CONDITIONAL'
g=Graph();providers={}
for name in ['step','_base_pursuit_action','_apply_wheel_ctrl','_ackermann_from_steer_speed','_get_obs']:
 item,fn=g.provider(inner,name);assert item;providers[name]=dict(provider=g.label(item),line=fn.lineno)
files.update({str(p.relative_to(R)):sha(p)for p in g.trees})
v=dict(passed=True,closed=True,outer_conditional_branches=branches,outer_control_entry_providers_invariant_across_available_branches=True,unavailable_conditional_branches=unavailable,actual_outer_import_branch_not_claimed=True,inner=dict(target=g.label(inner),mro=[g.label(x)for x in g.mro(inner)],providers=providers),source_SHA256=files,models=0,inference=0,physics=0,replay=0)
(S/'SOURCE_GRAPH.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(dict(passed=True,outer_mro_lengths=[len(x['mro'])for x in branches],conditional_branches_available=2,conditional_branch_unavailable=1,outer_providers=branches[0]['providers'],inner_providers=providers,runtime_modules_imported=0)))
