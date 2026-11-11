# V1030 新声明较容易课程的动态开发

PASS本新课程开发；**不是原动态任务或24验收通过**。原V1025窄通道失败保持。

只将actor运动中心从[3,-1]改为[1.3,-2]，原19静态体/起终点/车辆/控制/.155预测/.15实际/.04m与.035rad跟踪/200原生完整尾/.45到达及.08末点余量/原测距有界噪声5%漏检不变。周期集合裁剪向量化与89保存更新全部逐数组精确。车辆速度仍.03m/s；.08车速研究未通过未执行。新模型/初态因actor构造位置改变而另存，不冒称旧模型SHA。

真实测距发现、刹停、原因果完整动态路线、实际续行>=1m、目标与完整停稳/全原生状态控制接触重放/成功重复均必须。没有完整路线就停，不能用短前缀凑成功。发现前仅已知静态反应式合同。新课程预演是软件传感器夹具，不是实际成功；实际结果如下：

```json
{
  "passed": true,
  "closed": true,
  "scene": "V1029_ORIGINAL_MAP_OPEN_RECOVERY_SIDE_ACTOR",
  "new_easier_course_only": true,
  "original_dynamic_acceptance_passed": false,
  "new24_executed": 0,
  "counts": {
    "model_initializations": 2,
    "navigation_native": 63866,
    "own_replay_native": 63866,
    "private_mujoco_native": 0
  },
  "unknown_counts": [],
  "rows": [
    {
      "task_id": "dynamic_we",
      "passed": true,
      "error": null,
      "actual_goal_m": 0.3664880556993814,
      "source_searches": [
        {
          "stage": "static_complete",
          "status": "COMPLETE_GOAL_INPUT_ROUTE_SOURCE_QUALIFIED",
          "passed": true,
          "expanded": 2688
        },
        {
          "stage": "dynamic_complete",
          "status": "COMPLETE_GOAL_INPUT_ROUTE_SOURCE_QUALIFIED",
          "passed": true,
          "expanded": 8480
        }
      ]
    },
    {
      "task_id": "repeat_dynamic_we",
      "passed": true,
      "error": null,
      "actual_goal_m": 0.3664880556993814,
      "source_searches": [
        {
          "stage": "static_complete",
          "status": "COMPLETE_GOAL_INPUT_ROUTE_SOURCE_QUALIFIED",
          "passed": true,
          "expanded": 2688
        },
        {
          "stage": "dynamic_complete",
          "status": "COMPLETE_GOAL_INPUT_ROUTE_SOURCE_QUALIFIED",
          "passed": true,
          "expanded": 8480
        }
      ]
    }
  ],
  "unexecuted": [],
  "stop_reason": null,
  "training_updates": 0,
  "hardware_steps": 0,
  "guard_original": true,
  "execution_lock_idle": true,
  "models_authorized": false
}
```

按仿真时钟运行，搜索时车和actor不积分；不称实时、实机或递归保证。下一步仍需原困难课程回迁、三路线/独立确认及公平比较，不混旧成功/失败分母。旧V1024入口Path错误、V1025唯一入口接续和旧闭批均保持。
