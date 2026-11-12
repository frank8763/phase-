# V1084 restore index

Repository frank8763/phase-, Release phase-braking-reserve-v1084-20261112. Source/results commit67b8572fdb413a154ad8ff44e84d81d51153954e.

RECORD_INDEX.json contains SHA256 and size of each32MiB archive part. INVENTORY.json and SUPPLEMENT_INVENTORY.json contain each original source path, size and SHA256. Download only required archive parts from this Release; concatenate each group in numeric part order, verify archive_sha256, then zstd-decompress and tar-extract selected paths inside the Phase repository. Verify every extracted path against its corresponding inventory. Canonical MJB is referenced from records/nav2_v1077_v1078_20261112/RECORD_INDEX.json, unchanged SHA412f0616d1160dad61bb395919d9442372108ad094e07a5122274df5b29201f8.

CLEANUP_MANIFEST.json is limited to verified-backed raw/prediction caches in this V1084 run and duplicate local archive parts. Small evidence summaries, source and canonical model references remain locally. Stage is excluded.
