import mujoco
m=mujoco.MjModel.from_binary_path('/home/linghu/Documents/Codex/2026-10-31/new-chat/phase-/runs/v649_static_stability/dev25_seed91000002_single_event/paired/scene_model.mjb')
for i in range(m.njnt):
 name=mujoco.mj_id2name(m,mujoco.mjtObj.mjOBJ_JOINT,i)
 if 'steer'in name:print(name,m.jnt_range[i])
print('ctrlrange',m.actuator_ctrlrange[:4])
