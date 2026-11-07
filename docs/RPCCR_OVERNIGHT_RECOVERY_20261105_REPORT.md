# 无人值守返回搜索开发实际结果

状态：STOPPED_DEVELOPMENT_NOT_PASSED。

{
  "status": "STOPPED_DEVELOPMENT_NOT_PASSED",
  "stage": "v830_ranked_return_development",
  "final": {
    "status": "NOT_PASSED",
    "development_passed": false,
    "confirmation_passed": false,
    "combined_three_route_development_passed": false,
    "archive": "evidence/rpccr_ranked_return_v830_20261105",
    "transport": "evidence/rpccr_ranked_return_v830_20261105_transport",
    "source_and_decompressed_sha_verified": true,
    "raw_files": 17989,
    "raw_bytes": 2331695176,
    "raw_deleted": false,
    "report": "docs/RPCCR_RANKED_RETURN_V830_REPORT.md",
    "new_models_finalizer": 0,
    "new_integrations_finalizer": 0
  },
  "main_gate": {
    "passed": false,
    "main_attempts": 1,
    "main_successes": 0,
    "planned_main": 5,
    "unexecuted_main": 4,
    "success_rate": null,
    "route_successes": {
      "NORTH_SOUTH": 0,
      "EAST_WEST": 0,
      "WEST_EAST": 0
    },
    "direction_successes": {
      "POSITIVE_AXIS": 0,
      "NEGATIVE_AXIS": 0
    }
  },
  "navigation_native": 4248,
  "private_native": 3701744,
  "replay_native": 4248,
  "complete_repeats": 0,
  "new_confirmation": 0,
  "old_V828_NOT_PASSED_preserved": true,
  "no_automatic_new_candidates": true,
  "network_calls": 0
}

两次V828失败现为开发样本；原三路线也属开发，完整重复另计。今晚新24确认0，不能称动态验收通过。原V828及所有旧失败/截止保持。准确或未知积分以本批独立终审为准，null不填0。源、风险、模型、329/657覆盖和完整328尾门不减。REVIEW_PENDING恢复，不自动修补、新候选、新池或训练。报告见 docs/RPCCR_RANKED_RETURN_V830_REPORT.md。
