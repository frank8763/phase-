# V943 necessary records

Scientific status: NOT_PASSED. Source/report/summary are in Git. Complete original main and selected V936–V942 inputs/zero-model failures are in this repository Release.

Release: https://github.com/frank8763/phase-/releases/tag/phase-rpccr-recovery-v943-20261109

RECORD_INDEX.json lists lossless32MiB parts and source/member inventories. REMOTE_VERIFIED.json and DELIVERY_RESULT.json on the Release record final readback and cleanup; embedded archive metadata are earlier closed snapshots. Archive order is primary then supplement.

Restore only needed data, for example:

```bash
python -B experiments/v944_rpccr_segment_postmortem/restore_selected.py runs/v858_nav2_verified/v943/main_we
```

This verifies part, reassembled archive and extracted member SHA. It never launches a model. Restored raw inputs should be removed after use and preservation verification.
