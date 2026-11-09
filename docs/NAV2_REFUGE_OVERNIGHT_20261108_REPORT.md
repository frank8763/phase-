# 2026-11-08有限夜间动态开发

{
  "status": "NOT_PASSED",
  "rows": [
    {
      "task_id": "main_we",
      "passed": false,
      "returncode": 1,
      "actual_native": 11086,
      "replay_native": 11086,
      "private_native": 0,
      "goal_m": 3.6729437242591128,
      "output": "/home/linghu/Documents/Codex/2026-10-31/new-chat/phase-/runs/v858_nav2_verified/v897/main_we"
    }
  ],
  "actual_navigation_native": 11086,
  "own_navigation_replay_native": 11086,
  "private_native": 0,
  "platform_actual_native": 1200,
  "platform_replay_native": 1200,
  "original_platform_factory_steps": "NOT_SEPARATELY_INSTRUMENTED_UNKNOWN",
  "new24": 0,
  "training": 0,
  "real_robot": 0,
  "deadline_unix": 1794182400.0,
  "models_this_finalize": 0,
  "integrations_this_finalize": 0,
  "remote_upload_pending": true,
  "raw_cache_preserved_until_remote_verified": true
}

原V894及全部旧失败保持。0新24，不是独立确认或RAS/递归安全保证。原V896输出入口失败保持，V898仅一次用户批准输出接续；导航新候选无冻结后修补或重启。原08:00不延期。断网不丢原件或重试云同步，2GiB有界缓存，联网后远端逐SHA和恢复核验才清。

## 22:28闭批与保存态诊断

本轮22:25:46启动，三原路线真实t0通过；22:28:16西向东首主功能失败，完整重复及其余两路线主/重复共5导航未执行，新24未执行。真实11086原生/11086完整自身重放、私有0；全qpos/qvel/ctrl/mocap误差0，最低实际.269001137m、坏接触0。45.16s实际发现，发现后实际行走3.228018m/36条成功周期参考，但原目标剩3.672944m，未到达。

83.81s请求历史退让点[.224182246,-.680944690,.002711869]，23次真实Smac返回退让路径全部通过同原因果扫掠/末端驻留门。实际退让期间行走1.569326m，98.65s距临时目标最近.276016779m，未入控制.20m容差；末距.364277470m并前后偏移，触发固定25秒退出执行上限。说明已产生并执行反向退让，但临时目标末端跟随未完成；不把23路径PASS当退出或动态成功。唯一根因尚未确定，需区分路径末端前后向cusp/周期重规划与控制曲率/跟随耦合。不能只调长时间或放宽容差追认通过。原冻结源不改、不重启。

SOURCE_REMOTE_VERIFIED：103c31a324ec0ba5187b269057dc8f04fa5aea54已唯一push及远端HEAD确认。主证据404来源/85,060,662原始字节，40,374,979字节压缩后32MiB两块，来源、解压成员及重组SHA全通过；原始证据Release交付状态另看REMOTE_VERIFIED/DELIVERY_RESULT，不把源push当原始证据已交付。台账和当前指针已零模型更正为CLOSED/REVIEW_PENDING，执行锁空闲/本轮已知进程均退出。
