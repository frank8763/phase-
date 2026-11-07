# V842补充审核后条件12小时实际结果

{
  "status": "STOPPED_EXCEPTION",
  "pilot_supplement": {
    "status": "SUPPLEMENTAL_PILOT_COMPLETE_CHAIN_VERIFIED",
    "development_passed": true,
    "independent_audit_passed": true,
    "complete_chain_passed": true,
    "native_replay_exact": true,
    "source_unchanged": true,
    "preflight_passed": true,
    "new_pilot_navigation": 0,
    "new_replay_integrations": 0,
    "new_metadata_model_reads": 1,
    "metadata_integrations": 0,
    "original_navigation_native": 5800,
    "original_private_native": 14253664,
    "original_replay_native": 5800,
    "original_batch_status_preserved": "NOT_PASSED",
    "original_audit_timeout_preserved": true,
    "original_reactive_count_FAIL_preserved": true,
    "complete_both_log_witness_coverage": true,
    "coverage_negative_cases": 10,
    "complete_repeats": 0,
    "new24": 0,
    "completed_unix": 1793943121.565865,
    "archive": "evidence/rpccr_v842_audit_supplement_20261106",
    "transport": "evidence/rpccr_v842_audit_supplement_20261106_transport",
    "source_and_decompressed_sha_verified": true,
    "raw_files": 57427,
    "raw_bytes": 4956646822,
    "raw_deleted": false,
    "report": "docs/RPCCR_V842_AUDIT_SUPPLEMENT_20261106_REPORT.md"
  },
  "conditional12": null,
  "scientific_revisions": 0,
  "new24": 0,
  "training": 0,
  "Stage": 0,
  "network": 0,
  "automatic_restart": false,
  "old_batch_and_deadlines_preserved": true
}

原先导闭批NOT_PASSED与两个审核超时原样保留，补充独立全门通过后只原两失败及完整重复开发；不是新24动态验收。实际积分以各阶段独立审核为准，未知不填0。
