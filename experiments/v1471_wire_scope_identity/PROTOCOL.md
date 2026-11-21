# V1471 narrow entry run identity normalization

V1469 entry is CLOSED FAILED before any target I/O/model/runtime: its TASKS equivalence check normalized the output directory but omitted the separately registered run_id version token. Exact diff is only run_id v1469-originalWE-first-live-event versus v1467-originalWE-first-live-event. No task parameter or physical source discrepancy was observed. Preserve its frozen source, ENTRY_CLOSED and traceback; never rerun it.

This new version changes only that qualification metadata normalization, including the explicit version token for run_id. Production prewire/close grant logic is unchanged from the reviewed V1469 draft. It retains original quota holds/debits, grant owner/boot/expiry, source200ms, event count1, all science,5400s and storage limits. It reuses prior unchanged suites by normalized AST/SHA.

One new CPU2/run_phase/originalguard no-model entry is allowed after static source review. Test actual production Pump.publish with software envelope+real Unix datagram; valid already-debited grants avoid full du before sampling, insufficient/foreign grants refuse, expired or init-grant at nonzero native first does original full preparation. Test fresh software NPZ and qualified exact gzip closure losslessly and with exact charged bytes, no hot du. This is not physical/replay/runtime qualification.

New source must be frozen and every member remotely recovered before any distinct once first-live-event runtime. No new runtime admission/window/launch is currently present. The V1467 actual failure and all counts remain unchanged. Whole-route COMPLETE remains absent.
