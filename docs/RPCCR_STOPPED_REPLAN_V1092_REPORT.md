# Fresh canonical WE stopped finite-replan validation

```json
{
  "closed": true,
  "passed": false,
  "version": "v1092",
  "scope": "Fresh canonical WE navigation main plus conditional full repeat; eight stopped finite episodes maximum",
  "attempted": [
    "main_west_east"
  ],
  "unexecuted": [
    "repeat_west_east"
  ],
  "error": {
    "error": "AssertionError('FIRST_FUNCTIONAL_OR_SAFETY_FAILURE')",
    "traceback": "Traceback (most recent call last):\n  File \"/home/linghu/Documents/Codex/2026-10-31/new-chat/phase-/experiments/v1092_stopped_replan/campaign.py\", line 43, in main\n    out=Path(task['output']);rp=out/'RESULT.json';rp=rp if rp.exists()else out/'physics/paired/ENTRY_FAILURE_RESULT.json';result=json.loads(rp.read_text())if rp.exists()else dict(passed=False,missing_result=True);row=dict(task=task,result=result,returncode=code);rows.append(row);dump(O/'RESULTS.json',rows);assert code==0 and result['passed'],'FIRST_FUNCTIONAL_OR_SAFETY_FAILURE'\nAssertionError: FIRST_FUNCTIONAL_OR_SAFETY_FAILURE\n"
  },
  "complete_repeat": null,
  "counts": {
    "vehicle_initializations": 1,
    "historical_replay_native": 0,
    "new_actual_native": 39660,
    "own_replay_native": 39660,
    "replay_state_initializations": 1,
    "private_mujoco_native": 0,
    "training_updates": 0,
    "analytical_prediction_native": 183750
  },
  "guard_original": true,
  "source_unchanged": true,
  "whole_route_passed": false,
  "new24_executed": false
}
```

This is one observed WE developmental route from canonical t0, not three-route or24 confirmation. Empirical speed envelope is conditional, not global recursive safety.


日间独立回核：6个完整实际恢复段，39660新实际/39660自身重放，误差0，坏接触0，最低实际净空0.276984656m；终态平速0.000004714m/s，实际发现停车后净位移1.528498m，原目标余2.364657m。25门仅原目标到达失败，其余24门通过。不是跟踪失控、控制权抢占或未实际停车，不能报整路通过。

下一原因验证均0模型：原静态目标路的16个等待相位全在动态净空门拒绝，故单纯错峰不能解决这条路径。把真实测距原因果全周期占据外盒仅加入拓扑提案后，固定20k仅得到安全局部源，未得到完整原目标源；不能声称新路线已就绪。物理场景19实体/单actor、原安全门均未改。下一步需要动态占据感知的完整拓扑搜索/可执行转弯衔接，而非延长导航时间或继续复跑同路。

冻结前两次软件失败（240s完整等待相位搜索、固定旧观测名义拼接拒绝）及只读预编译准备错误保持；闭批诊断还发现原扩展审核把局部finite_plan误当模块属性，已仅在0模型诊断命名空间绑定原函数后完成回核；冻结物理/审核源未改。空间提案首个外盒坐标编码错误被原独立证书拒绝，已保存0模型失败并按原中心/半长接口更正，未用于物理。

当前已恢复REVIEW_PENDING原字节、执行锁空闲，不自动新物理、EW/NS、24或通宵。原NS主/重复成功和所有旧失败保留。初始归档内活跃closure日志是当时快照；此闭批补充归档保存完成后的日志及完整诊断快照，不覆盖原归档。
