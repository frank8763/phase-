# V945 raw evidence

Same-repository Release: https://github.com/frank8763/phase-/releases/tag/phase-rpccr-regression-v945-20261109

`RECORD_INDEX.json` lists32MiB lossless archive parts and their SHA256, in restore
order. Inventories list every decompressed regular member and its SHA256. Source
and compact results stay in Git. Raw is a bounded local cache, removed only after
remote part/archive/member readback. Generated mesh-directory link text is in
GENERATED_LINKS.json; external link targets are not copied or deleted.

Restore only a required prefix with:

```bash
python -B experiments/v946_rpccr_regression_closure/restore_selected.py runs/v858_nav2_verified/v945/main_we
```

The restore performs no models/integrations. It downloads listed archives to a
temporary cache, validates parts/reassembly and extracted member SHA. Delete
restored temporary raw after analysis according to docs/STORAGE_POLICY.md.

Scientific result is NOT_PASSED. Actual recovery action reached its endpoint, but
reference heading envelope failed; original observation liveness later stopped
the run. Retaining a physical/state replay pass does not override that failure.
