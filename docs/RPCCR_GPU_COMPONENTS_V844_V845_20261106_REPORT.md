# V844 GPU提案与V845原生资格实际结果

{
  "gpu_proposal_component_passed": true,
  "gpu_p95_ms": [
    9.210713708307594,
    8.826328789291438,
    8.815810859960038,
    8.819766447413713
  ],
  "maximum_numpy_formula_error": 4.831690603168681e-12,
  "gpu_peak_allocator_bytes": 119516672,
  "native_fixed_states": 4,
  "native_candidate_sequences": 16,
  "original_safety_gate_passed_sequences": 8,
  "candidates_meeting_all_native_and_progress_gates": 0,
  "candidates_meeting_first8_progress_gate_only": 6,
  "all_states_native_development_passed": false,
  "native_compute_ms": [
    171.5284350211732,
    161.2348740163725,
    151.12652195966803,
    150.52220498910174
  ],
  "maximum_ideal_native_xy_error_m": 0.6771644767388417,
  "counts": {
    "old_replay_native": 9584,
    "private_native": 5376,
    "actual_branch_native": 0,
    "repeat_branch_native": 0,
    "new_navigation": 0,
    "new24": 0
  },
  "model_initializations": null,
  "approximate_gpu_counted_steps": 11096064,
  "approximate_setup_work": "3 eager warmups and CUDA graph capture; capture execution count not asserted",
  "full_closed_loop_realtime_passed": false,
  "dynamic_acceptance_passed": false,
  "new_policy_trained": false,
  "source_unchanged": true
}

GPU提案512条/42公开段，四例数学和20ms p95门通过；仅为理想模型计算，非完整车模。原生16尾中8条原安全门合格，另8条净空不足；原安全合格的8条均不满足新增首8原生目标增益>=.001的开发资格，不能将它们称为安全失败。全部16末速、自体和控制幅值/速率过门、整尾目标进展为正。无实际分支接管/新导航/确认/训练，旧9584原生重放误差0，5376私有。新增673半步规划查询包括原329/657子集，不是新增实际积分或连续时间保证。候选未达到资格即停止该批，无改阈值/增加候选/重跑。

四候选原生认证150.5–171.5ms，端到端GPU与CPU实联闭环延迟未测，不称80ms实时通过。GPU理想/原生位置偏差最大.677m，直接移植便宜运动模型不够。两个阶段原冻结SHA与原始来源、零模型独立公式回读保留；后端并行物理测试另立协议，不混本批成功。

零模型元数据更正：初始FINALIZED中candidates_meeting_added_first8_progress_gate=0的字段名不准确，该0实际指全部门合并通过数；首8进展单项通过6/16，原安全门通过8/16，二者交集0。原候选行和独立审核无误，原FINALIZED/归档保持，另存runs/v845_gpu_native_qualification/METADATA_CORRECTION.json供回读。
