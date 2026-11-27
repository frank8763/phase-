# Fair comparison and identifiable mechanism effects

Current work addresses the user's two priorities: credible comparison and an
identifiable mechanism contribution. This document records a new development
design, not experimental success or a runnable physical queue. Old common120
and mechanism20 results are immutable and remain separate.

## What the existing results identify

The new V2182 saved-record readout verifies72canonical outcome SHA records.
Of51clean refusals among the five completed comparator systems,32occur at
complete-stop acceptance (DWA10,MPPI11,SVG-MPPI11),16at common command-domain
acceptance (RPP9,TEB7), and3at a finite TEB query. These are termination-stage
counts. They do not prove actual collision, a globally infeasible task, or a
published method's inability to navigate. The remaining12technical cases are
separate from these clean refusal counts.

The saved DWA common01 boundary is0.24268471109899914m against the unchanged
0.24353421020226934m predicted floor, a0.0008494991032702015m deficit. This
single witness suggests inspecting planner/supervisor consistency. It does
not justify reducing the margin or extrapolating the cause to all32cases.

For mechanisms, the full onward-precheck branch has saved attempts in WE01,
WE02 and WE04. WE01 shows a selection-acceptance divergence: full refuses
where no_onward admits refuge0. Its incomplete independent evidence prevents
a clean causal whole-navigation conclusion. WE04's two successful variants
select refuge0; the existing closed study reports identical trajectories.
Successful EW12 uses the response-reserved early path in both variants, so
the time-selection branch is bypassed. EW10 also saves this bypass, while
several other failed cases lack a reached selection record. Missing does not
mean inactive. The4NS cases are registered inactive-route controls.

## Fairness: separate method roles and establish positives first

The old adapted-system comparison stays in its original table. A new shared
controller-module group will be labelled separately. RPP is a tracker and
PSF/PCBF require a declared nominal controller; they must not be silently
presented as interchangeable complete navigation systems. SCCR-CP denotes
the controller-only adaptation; historical environment state injection is
excluded. The orientation-state SLSQP prototype is not author PRIEST/CEM.
An inapplicable author method remains inapplicable, rather than being renamed
into a successful or failed version of that author method.

Before any new physical registration, pin the same original plant source,
public map, task geometry, sensor producer, shared route frontend, safety
supervisor, output mapping, capture lifecycle and control-slot semantics.
Make public static map, causal32rays, complete measured186features, measured
rear-body/steering and controller memory equally available. Methods may
ignore features; no method receives privileged actor truth. Retain the actual
original causal freshness and full physical safety checks; the older minimal
software wire's200ms clock allowance is not a replacement execution contract.

The proposed module group has a0.1m/s maximum speed and1/1.32 maximum curvature
for every member, with0.05s fresh control slots. These are NEW-group choices,
not a claim about old parameter equality or native-author equivalence. In
particular the old baseline wire has a0.1m/s cap whereas saved RP-CCR proposal
schedules can use0.12m/s; the old comparison must not be described as having
identical action bounds. Final registrations need real source hashes, not the
explicit dummy hashes used by the software tests. Every output projection or
gear conversion must be uniform and disclosed; no selective command rescue.

The28November real-source inspection now pins14actual local files and exact
AST/line witnesses (`runs/v2182_fairness_mechanism_diagnosis/REAL_SOURCE_WITNESSES.json`).
DWA and RPP have byte-identical `response.py` files; their `points`, `verify`
and `acquire` observation functions also have identical ASTs. This is a narrow
source equivalence, not verification of the complete dependency/runtime closure.
Their frontends and proposal interfaces differ: DWA queries the task goal
directly, masks samples to forward speed at least0.005m/s, accepts at most0.08m/s
and queries every10native ticks with two5-tick admissions. RPP consumes a
planned path with gear segments, applies signed-speed/yaw projection and a
near-zero deadband, accepts at most0.1m/s and queries every5ticks. Thus even
these two old systems do not have a matched frontend, proposal domain, output
adaptation or query schedule. This does not establish which difference caused
any particular refusal. Eight negative source-binding checks pass; incomplete
bundles are denied and the new shared-module group is still NOT ready.

First development capability slots are DWA and RPP, representing the two
dominant refusal families, followed by MPPI and the remaining applicable
modules. This order is fixed from failure stages, not from favorable new
outcomes. Each method gets one declared integration/configuration; preserve
its first refusal and stop its branch rather than tune the test input.

The common module data boundary is now implemented in V2182`shared_interface.py`.
It supplies identical measured-state/32ray/complete186/path/gear/whole-goal
envelopes independently of method identity, binds source and packet identities,
and uses the exact original pure receipt and twist-domain predicates. The new
group explicitly uses STRICT output acceptance for every member, with no output
clipping, sign repair or silent missing-feature padding. Five-native candidate
requests retain the original2200zero continuation; they are NOT certificates.
The old RPP projected-pair ABI therefore still needs a declared raw-core
integration, and DWA needs its declared shared-path goal adapter/parameters.
Neither adapter is implemented or qualified by the data boundary.

The separate DWA shared-path preparation is now implemented in
`dwa_shared_path.py`. It preserves the measured body-centre state and converts
the common rear-axle segment poses to body-centre poses using each pose's yaw;
the segment endpoint is a planning target and never substitutes for the actual
whole-task goal. RPP retains the same segment in its native rear frame. Four
rotated/gear fixtures and the saved exposed common01 route pass this data check.
No unicycle-to-controlled-plant equivalence follows from frame consistency.

Its declared NEW-group parameters are signed speed±0.1m/s, curvature1/1.32,
dt0.05s and speed-grid resolution0.005m/s; horizon, objective weights,
acceleration limits, body dimensions and disabled stuck-spin remain unchanged.
The finer grid follows from the0.01m/s rest acceleration window at the new
control period, rather than a navigation outcome. A finite mathematical grid
check finds9forward and14reverse admissible samples on the installed NumPy;
raw grids are retained, and no symmetry/equal-work claim is made. Only a
declared signed-gear mask is inserted in the upstream candidate loop; exact
mask removal reproduces every upstream function AST. These bodies were
syntax-compiled only: no native DWA query, trajectory prediction or cost
function was executed. Actual query binding, common route planner, live186
producer and original physical gates remain unqualified. Old DWA results and
parameters are unchanged.

A separate raw RPP core bridge has now been implemented and compiled once on
CPU4 (ABI2,208824bytes; `RPP_RAW_BUILD_RESULT.json`). Its reversible source
transformation replaces the old ExecutableRPP type/include with the upstream
Nav2 class and increments the ABI. Request/map/TF/path checks, parameters,
lifetime and once/poison behavior are retained. This removes the old inner
Phase projection/deadband and projected-pair recheck; upstream native checks
remain, and the same external strict command and original full-stop gates are
still required. Static ELF tools observe the expected eight C exports and
direct dependencies without loading the library. There has been NO DLL load,
FFI call, controller construction or control-output query. Transitive runtime
dependencies and actual map/TF/input compatibility remain unverified. This is
an implementation/build milestone, not an RPP capability result or permission
to reuse an old loader/window. The old ABI1 loader must reject this new ABI.

One software check supplied the same saved receipt/path and an explicitly
SYNTHETIC186 block to all10labels: envelope and candidate-output hashes were
identical, with32negative cases passing. The saved receipt alone was correctly
refused for missing186. An additive method-identity guard subsequently rejected
10foreign-method replies and an unknown label; reverting only that guard gives
the exact previously tested AST, and all10envelope hashes stay unchanged. The
first helper is retained byte-exact with its original proof. These are data
checks, not10executed algorithms, live producer validation, frontend planning,
policy inference or physical capability. Source pins alone do not attest that
a producer executed. Original fresh-acquisition, safety, clock, replay, audit
and full resource admission remain external mandatory gates. No200ms wire
allowance is substituted for the original execution checks.

A capability task uses the exposed common01 original start, map, actor phase,
sensor seed and8m task goal, with a bounded500normal-native budget. Its auxiliary
criterion is at least0.25m nonzero measured progress followed by the ORIGINAL
2200-step stop, complete capture/N+1, exact own replay and independent audit.
This is a motion capability component, never whole-goal arrival or a formal
confirmation sample. Record all safety refusals and error-stop outcomes. A
successful software fixture or zero-motion run cannot qualify a method.

Only after applicability and positives are established should a frozen new
comparison begin. PSF and PCBF comparisons fix the same nominal controller
and shared frontend, and retain the same external physical supervisor even
in the nominal-only arm. Internal filter intervention and external-supervisor
refusal are separate outcomes. No equal-total-work claim follows from equal
information or nominal work caps; internal factory/Allocator work remains
unknown unless measured.

## Mechanisms: record activation, selection change and outcome separately

The implemented pure-data readout distinguishes three levels:

1. Entering the onward/time branch.
2. Changing the chosen refuge, wait, or admission decision.
3. Changing an independently qualified physical outcome.

For timing, preserve all40wait evaluations in their original0..1950/50order,
including failure and complete-slack values. Recompute the original largest
reserve-slack/shortest-wait selection and the wait0-only counterfactual from
that logged bundle. Mark the retained fast-path bypass explicitly. A wait0
result alone does not establish inactivity. A partial search cannot establish
an identifiable selection effect. The software predicate was checked against
the exact original selection AST; no optimizer/model was executed.

For onward, preserve prefix eligibility and onward eligibility separately for
each candidate in its original order. Full selects the first eligible prefix
with an eligible onward source; no_onward selects the first eligible prefix
and still plans onward from the measured handoff. Never remove the external
supervisor, shorten the stop, or count a refuge endpoint as the actual goal.
Do not invent a counterfactual prefix proof that the old full run did not save.

Four NEW development phases, two per route, are now fixed by the independent
SHA recipe in `runs/v2182_fairness_mechanism_diagnosis/MECHANISM_DEVELOPMENT_TASKS_LOCKED.json`.
They retain the original route sensor seeds and all start/goal/model conditions.
There are8assignments, with full/ablation order counterbalanced by replicate.
All are currently UNEXECUTED/UNADMITTED. Report inactive, censored and failed
cases, retain the full screen denominator, and do not replace unsuccessful
phases. Development activation screening is not independent confirmation.

V2182`mechanism_observer.py` now implements source-bound observational hooks
for future full/no_time and full/no_onward functions. Only scalar results of
PERFORMED evaluations are logged. Removing the hooks reproduces each of the
four original/transformed function ASTs exactly; the original generators were
compiled for syntax only and never executed. Nine synthetic fact sequences and
18negative checks pass. These checks distinguish fast-path return, all40waits,
partial search, measured-onward-only invocation and deadline censoring before
the refuge branch. Composed full feedback is kept separate from independently
evaluated prefix feedback. Missing prefix/onward results remain explicitly
unknown, and no extra model evaluation is introduced to obtain counterfactuals.

This closes an instrumentation implementation gap, not a mechanism-efficacy
gap. Actual quota-bound persistent logging, observer binding into a future
registered driver and physical validation remain unqualified. Logging costs
can affect a deadline-limited search, so static AST reversion is not runtime
timing or trajectory equivalence. An observer failure must close the branch,
and an interrupted record cannot be labelled inactive or a benefit. WE01's
old independent-evidence gap remains unchanged.

Primary physical outcome remains original whole-goal arrival with complete
stop/evidence. Secondary endpoints include admission divergence, selected
refuge/wait, executed prefix before a finite onward refusal, distance progress,
and measured work subsets. A finite search failure is not proof that a refuge
is globally unrecoverable. Inactive and technically censored pairs cannot be
converted into positive mechanism results. If full is worse, report that too.
No benefit is guaranteed; the experiment can falsify the intended advantage.

After a final mechanism implementation is frozen, independent confirmation
must use a separately preregistered phase pool that has not supplied development
outcomes. Do not select only cases on which full already succeeded. An
activation-defined stratum must be defined from common pre-treatment evidence,
with the full screened population reported alongside it.

## Physical execution prerequisites and bounded scheduling

V2181's fixed-reservation repair is CLOSED_UNQUALIFIED. Its software fixture
success does not establish the future contact/error-tail capture envelope.
No physical background process is running. A new complete lossless evidence
lifecycle or justified bound is a necessary prerequisite for both priorities;
do not reopen V2180 or V2181, change a TTL/hold size alone, or start a source
qualification merely to create activity.

The tentative capability slots and8mechanism assignments are a finite design,
not a guarantee that all fit current15GiB retention. Before EACH once claim,
charge all retained old and newly closed evidence, actual archive/readback
peak, task224MiB,IO272MiB and root512MiB, and reject unfunded later slots before
initialization. Preserve unexecuted slots. Source/unique push/actual remote chain,
full combined evidence validation, original REVIEW and both locks are required.
CPU2 remains the sole original plant/Predictor/replay/audit lane; CPU0/4/5 can
advance software, geometry and I/O, while CPU6 numerical peers require their
own real qualification. No unqualified parallel plants or Stage CPUs.

The delegated weekend still ends Sunday29November09:00local, with no new
physical admission after07:00. Old frozen windows and the closed orientation
engineering slot are not renewed. This plan prioritizes useful contrasts and
truthful conclusions, rather than completing a method count at the expense of
applicability or evidence integrity.

Evidence: V2182`RESULT.json`, `ACTIVATION_SOFTWARE.json`,
`FAIR_CONTRACT_SOFTWARE.json` and the locked development task manifest.
These are new local records after26d4, not members of that old sealed release.

The lossless-recording work does not remove the execution prerequisite. V2183's
single compact-layout candidate read back all44,750 saved native records and
8,953 scans bit-for-bit, reducing its stream from91,054,205 to26,270,791bytes.
Its preregistered necessary scenario still totals47,745,233bytes against
39,813,120available, before unqualified prediction/model costs. The capacity
criterion FAILED and that long-route format branch is CLOSED. The prospective
10MiB emergency reserve was never activated or I/O-qualified. No third codec
attempt, altered criterion or physical launch follows from the compression
result. Fairness source work and the manuscript can proceed independently;
short physical capability requires its own complete capacity/driver/audit gates.


## Shared nominal frontend implementation, 28 November

One pure public-static geometry search now returns217nominal poses on the exposed
common01 course. Independent scalar polygon/segment/circle distances agree on
1081dense samples to6.66e-16m; sampled minimum is0.2450000942m and the original
adaptive-start planning guard is0.2440000942m. This is neither a continuous or
dynamic safety certificate nor a physical arrival. No controller was queried.
The full physical predictor and original safety margins remain mandatory.

Both controller modules must receive the same0.6m local single-gear route window.
Giving DWA only the entire path endpoint while RPP sees its curve would retain
a frontend mismatch. The new window and per-yaw rear/body transforms are
implemented; actual progress tracking, gear-cusp rest, live information producer
and physical driver integration remain unqualified. The global task goal is
retained separately. Evidence: V2182`NOMINAL_FRONTEND_GEOMETRY.json`; this does not
change any formal or mechanism outcome count.

## Fixed historical raw-controller mathematics preparation,28November

V2184 source-only qualification is now closed:29655 inherited files and23new
pins, with no DLL load, FFI, controller construction or query. The software
checks passed7positive/12negative fixtures and three real unadmitted CLI
checks, including the actual read-only Phase and ROS namespaces. Source code
is frozen. A unique remote source recovery must precede the two planned native
mathematical queries. The historical causal input is never sent to a physical
plant. This scope is neither a capability positive nor the all10 camera group.

The initial all-in-Release archive forecast failed its reserved margin and is
preserved. The fixed-cap source partition now puts necessary code in Git, with
actual remote blob bytes/SHA checks, and the binary, inputs and metadata in a
Release with actual full readback. No recording codec, scientific input or safety
threshold changed. An extra capacity verifier initially mishandled a recorded
directory symlink; a shell-ordering mistake let source-only qualification run
before that extra check finished. This gap is preserved. The corrected702-member
stat/SHA and five link-text checks completed before any push or numerical
work; no link target was inspected. Source qualification is not rerun or
relabelled as numerical admission. All120/20/new8 outcomes remain unchanged.

## Actual raw-interface mathematical result,28November

V2184 closed with one DWA and one upstream raw RPP query on the fixed exposed
common input and0.6m path. DWA returned speed0.009999999999999998m/s and yaw
4.85722573273506e-17rad/s; RPP returned0.1m/s and0rad/s. Both passed the same
strict command predicate without clipping/retry. This checks native interfaces,
not physical tracking/stopping/arrival. Source/runtime actual-remote verification
and eligible transport cleanup are closed. Late I/O helper provenance and
preparation failures are disclosed in RAW_CONTROLLER_INTERFACE_V2184_20261128.md.
Original120/20/new8 and the physical recording capacity limitation remain.

## Complete186 route and previous-action context, saved-data boundary

The186 block includes route/waypoint/goal, previous virtual action and a frozen
base-policy output; it is not merely a camera vector. A matching dimension and
origin packet alone cannot bind these semantics. The additive ContextBoundary
now binds the measured origin, float32 body path, waypoint, goal, previous action
units and same-episode commit, producer source pins and the exact feature bytes.
It preserves the previously tested shared_interface.py and all V2184 code.

One actual archived V2176 native0 frame contains complete186 values and an
existing independent-prefix review. Its nominal rear path converted to body
centres matches the saved feature path exactly in float32. The new software
check provides those saved bytes/context to all10method labels: envelopes and
candidate requests match exactly;12mismatched-context negatives refuse and
poison the boundary. No producer, learned actor, renderer, model, native
controller, replay or independent physical audit was reexecuted. Historical
timestamps remain historical. These are10data envelopes, not10run algorithms.

V2176's original functional refusal,200actual/200replay and incomplete original
SCCR qualification remain unchanged. This saved-data positive does not qualify
the new live186 producer, original Phase21risk fusion, camera-input distribution,
control-history/waypoint lifecycle or physical comparison. Complete live
freshness/capture/independent qualification remains necessary. The result and
new helpers are LOCAL after26769; no earlier Source/Release coverage is claimed.

## Timing-observer procedural software coverage

A separate fixed mock test executes copies of the exact original timing
function and no_time transform, with and without observational hooks. All
Engine, geometry, search, binding, reserve, clock and checkpoint dependencies
are explicitly fake; no legacy module or actual planner/model is loaded.
For both variants, retained fast return, changed wait choice, all40infeasible
and deadline interruption give identical before/after answers, first exceptions
and fake call traces(8cases/16mock function executions). Retained cases perform
zero fake simulations, completed cases40, interrupted cases7; incomplete choice
and causal navigation benefit remain unknown. This extends AST-removal checks
to mock control flow; it does not establish actual numerical decision/clock
identity, physical activation, equal work or mechanism benefit. Initial system
Python lacked NumPy before any mock function ran; the test then used the
existing Phase Python under read-only namespace with only S2182 writable.
No package, source qualification or numerical experiment was added.
