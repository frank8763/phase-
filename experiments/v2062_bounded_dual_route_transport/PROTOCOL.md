# Bounded process-local proxy/direct Release transport

MPPI08 and09 original IO episodes failed all6GET transports at the first Release
metadata request, with approximately5s connection timeouts and no HTTP response.
All original failures remain immutable. Current detached route probe gives
proxyHTTP200, unauthenticated direct403, then authenticated both exact Release
id458891864. This supports intermittent connection failure; the historical root
cause is not proven. A common weakness is all original curl/gh/urllib fallbacks
inherit the same proxy, so they are not independent network routes.

New metadata-only client keeps6GET attempts total and36reads total. Attempts1–3
use the preferred route,4–6 use the other route. On success retain the selected
route only in this I/O worker so original upload/range downloader inherits it.
Never change system/global proxy settings or Stage processes. Proxy credentials
and GitHub token stay only in memory, never records. Requests remain restricted
to the Phase Release API. Non-GET uncertain writes are still single-attempt;
original remote existence/digest reconciliation remains unchanged.

One software test drives the actual request dispatcher with a failed proxy and
working directroute: original goes red after6, new goes green at4. Bothfailed
remains6cap, POSTfailure remains1attempt. This is a transport seam, not a model
qualification. One new600s same09archive recovery, no reseal/push/ref/model/query/
physics/replay/audit. Full actual remote block/member/whole/indexSHA, exact
duplicate transport cleanup and canonical barrier precede any next model.

Subsequent originally unclaimed MPPI10–12 use the original frozen source and
owner. Their transport wrapper injects this exact qualified client and reserves
two finite600s IOepisodes. Preserve every failure. No infinite network loop,
new seed, safety/parameter change or additional formal task.15GiB original
jointpeak16095019008 and grants unchanged. Any unresolved failure stops models.
Old SVG sources stay frozen/unexecuted; do not clone another wait-only numerical
source while MPPI is active. Prepare its prerequisite after MPPI actually closes.
