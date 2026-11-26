# Bounded continuous-input preparation, zero solver/model work

V2079 original-vehicle interface closedPASS2210actual/replay,10normal plus full
2200stop. A full task needs repeated fresh queries with one retained optimizer
instance, RNG and warm-start memory. Recreating the solver at every step would
change the method. Persisting all100x100x4 map planes at each step can exhaust
the original224MiB task cap (the saved first canonical frame alone is382583B).

Prepare a bounded local in-memory stream whose child input is read-only and
whose exact map/state data are unchanged. Parent owns one endpoint, child reads
the other as stdin. Only one request may be outstanding; at most6000 current
queries plusEOF/close, each <=1MiB. The caller must independently bind current
receipt and all map/state SHA and save controls/source/selected-route evidence;
this channel supplies no numerical or physical admission. Socket buffers are
64KiB requested per endpoint (record actual kernel values); no full maps are
written persistently merely for transport. Every sent frame byte/hash/count is
observable. The future original independent audit must rebuild maps from saved
causal input and path/source before any formal qualification.

One software fixture on CPU5 using the exact unchanged OutputBoundary, real
subprocess and saved first frame plus an explicitly labelled software envelope.
Byte-exact SHA delivery across two frames, unchanged full-source input, count/
size/repeated-inflight/foreign-owner/closed guards and original raw descriptor
refusal. No original solver/vehicle call, stored command playback, model, physics,
replay, source qualification or formal task. This is preparation for a future
frozen persistent peer; current2210 success is not full-task admission. Preserve
all prior failed scopes and the original15GiB/joint peak/224MiB task cap.
