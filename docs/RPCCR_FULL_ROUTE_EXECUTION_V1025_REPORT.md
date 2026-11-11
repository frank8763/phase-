# V1025 一次零模型入口接续的完整目标输入路线开发

原V1024在Popen前Path加字符串异常，0模型；原错误保持，新入口仅改路径构造，算法和原11:48:54截止不变。

NOT_PASSED。新90分钟根窗，所有旧批与旧截止保持，首次异常停止依赖。

```json
{
  "passed": false,
  "closed": true,
  "counts": {
    "model_initializations": 2,
    "navigation_native": 45664,
    "own_replay_native": 45664,
    "private_mujoco_native": 0
  },
  "unknown_counts": [],
  "tasks": [
    {
      "task_id": "static_we",
      "passed": true,
      "status": "GOAL_AND_COMPLETE_STOP",
      "error": null,
      "goal": 0.34950650566674296,
      "maximum_position_m": 0.013833615023211267
    },
    {
      "task_id": "dynamic_we",
      "passed": false,
      "status": "FAILED",
      "error": "AssertionError('NO_COMPLETE_DYNAMIC_INPUT_ROUTE')",
      "goal": 4.237166843630056,
      "maximum_position_m": 0.005907647233441446
    }
  ],
  "unexecuted": [
    "repeat_dynamic_we"
  ],
  "stop_reason": {
    "error": "AssertionError('FIRST_FAILURE_STOP dynamic_we')",
    "traceback": "Traceback (most recent call last):\n  File \"/home/linghu/Documents/Codex/2026-10-31/new-chat/phase-/experiments/v1025_full_route_entry/campaign.py\", line 54, in main\n    if not row['passed']:raise AssertionError('FIRST_FAILURE_STOP '+task['task_id'])\nAssertionError: FIRST_FAILURE_STOP dynamic_we\n"
  },
  "new24_executed": 0,
  "training_updates": 0,
  "hardware_steps": 0,
  "models_authorized": false,
  "guard_original": true,
  "execution_lock_idle": true
}
```

原0.155预测/0.15实际/0.04m与0.035rad跟踪/200完整停车尾/原目标0.45和0.08末点余量保持。V1023用逐原生输入预测替代稀疏几何参考，去掉仅稀疏参考所需的额外误差，原空间延迟20ms余量保持0.088534210m，原始净空准入0.243534210m。一个实际控制者，未启动Nav2 ROS控制动作；不能继承旧版24验收、称算法优越或实时。发现前仅已知静态反应式合同；原测距发现后撤销静态后缀，原因果完整200停车及固定20秒保持观察后，一次完整动态整周期安全输入搜索，拒绝不执行短前缀。低阶模型无长轨迹误差定理，实际跟踪超限即停。

动态全链/原生安全/完整控制状态重放与成功重复均需通过；未执行不作0/24，静态/动态/重复分账。训练/SAC/实机0。Stage隔离。无自动新物理、候选、路线或窗口。必要证据远端来源SHA与解压回读完成后再清缓存。
