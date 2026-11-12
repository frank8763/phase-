# Fresh canonical NS measured-pose navigation validation

```json
{
  "closed": true,
  "passed": false,
  "version": "v1088",
  "scope": "Remaining fixed WEST_EAST and declared north-shifted EAST_WEST mains and full repeats; NS milestone reused read-only",
  "attempted": [
    "main_west_east"
  ],
  "unexecuted": [
    "repeat_west_east",
    "main_east_west",
    "repeat_east_west"
  ],
  "error": {
    "error": "AssertionError('FIRST_FUNCTIONAL_OR_SAFETY_FAILURE')",
    "traceback": "Traceback (most recent call last):\n  File \"/home/linghu/Documents/Codex/2026-10-31/new-chat/phase-/experiments/rpccr_execution_core/fresh_campaign.py\", line 43, in main\n    out=Path(task['output']);rp=out/'RESULT.json';rp=rp if rp.exists()else out/'physics/paired/ENTRY_FAILURE_RESULT.json';result=json.loads(rp.read_text())if rp.exists()else dict(passed=False,missing_result=True);row=dict(task=task,result=result,returncode=code);rows.append(row);dump(O/'RESULTS.json',rows);assert code==0 and result['passed'],'FIRST_FUNCTIONAL_OR_SAFETY_FAILURE'\nAssertionError: FIRST_FUNCTIONAL_OR_SAFETY_FAILURE\n"
  },
  "complete_repeat": null,
  "counts": {
    "vehicle_initializations": 1,
    "historical_replay_native": 0,
    "new_actual_native": 0,
    "own_replay_native": 0,
    "replay_state_initializations": 0,
    "private_mujoco_native": 0,
    "training_updates": 0,
    "analytical_prediction_native": 0
  },
  "guard_original": true,
  "source_unchanged": true,
  "whole_route_passed": false,
  "new24_executed": false
}
```

These are two observed development routes; existing NS milestone is separate. EAST_WEST starts at declared(4,-1.9), not original(4,-2). No24 confirmation. Empirical speed envelope is conditional, not global recursive safety.

## 零模型入口诊断（原批次保持失败）

首WE真实初始化1，原生导航/私有/重放/解析预测/训练全部0，实际起点(-4,-2,0)、初始净空.314999653m、坏接触0。入口硬编码了NS场景MJB SHA，实际WE SHA为af6f0c393382a255afb35ff1ae0db5256100705c85cc264d25bdc3541966db53，因此在首积分前拒绝。独立审核和原归档器也有同一个NS哈希假设；归档器首次自动收尾因此失败，原错误保留。

这是准备时遗漏的可避免接口错误，不是已运行的WE导航失败。保存的443个模型数组合同有441项字节SHA相同，差异是body_pos和派生光照light_poscom0；模型XML除已登记的actor锚点NS(-1.5,-1.2)→WE(3,-1)外完全相同。两路线本来拥有不同actor课程位置，不能要求整个场景MJB同一SHA。原路线/actor没有新改动，也没有证明所有任意模型差异都可接受。

已运行保存输入差分诊断及actor尺寸/mocap篡改拒绝例，0新模型积分。正确修复应同时覆盖生产、独立审核、归档：车辆动力学/静态地图/控制合同严格一致，课程特定actor及完整场景模型分别登记与锁定；每个重复仍要求与自己的主模型完整SHA一致。不能简单删掉模型门。

本轮首次异常即停，剩余WE重复/EW主/EW重复未执行，没有冻结后修补或重跑；原南北成功主+重复及旧错误、关机中断保持。下一物理接续须另行明确授权，当前REVIEW_PENDING原字节/执行锁空闲。现仅零模型保存失败现场及全部新MJB（不使用NS模型排除规则），独立来源/解压SHA归档另记，不将归档成功当功能成功。
