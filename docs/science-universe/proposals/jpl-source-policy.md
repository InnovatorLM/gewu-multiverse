# JPL SSD API source handling

First-party documentation reviewed on2026-10-26UTC; this is a source-handling
review, not approval of any scientific task or numerical data license.

The [official API index](https://ssd-api.jpl.nasa.gov/doc/) requires minimum
reasonable requests, caching/reuse, one API request at a time, backoff and an
application-specific User-Agent containing correct product name, version and
contact information. It gives no numeric requests-per-second quota in the
retrieved policy and does not specify a contact-information format. A truthful
project issues URL is an implementation choice, not an officially endorsed example.

The service is best effort, may change format without notice and does not promise
indefinite availability. An API format version does not freeze the scientific
data. The [SBDB documentation](https://ssd-api.jpl.nasa.gov/doc/sbdb.html), reviewed
as an example only, distinguishes orbit_id, soln_date, source and epochs; exact
units/time scales depend on the actual endpoint. Retain raw bytes, request
parameters, retrieval UTC, SHA256 and available scientific solution identifiers.
An epoch alone is not a release identifier. Final grading should use frozen
inputs rather than future live responses.

Numerical data reuse licensing and endpoint-specific citation requirements remain
unverified. Other SSD pages timed out and JPL policy pages returned403; no bypass
was attempted. Image policy cannot establish numerical data licensing, and NASA/JPL
affiliation or public access alone is insufficient evidence. Confirm the actual
data product before redistribution; mark unknowns explicitly.

Retained official-document hashes:

| Document | SHA256 |
| --- | --- |
| API index | a001b7508e54e6a180a8bc8ff7a4969056901b81c45ae5a384b2dc4269a7af85 |
| API about | 3ee6637490517a09719abe7d40cfb5686b043f83e29fbd92c288b35d694e7935 |
| SBDB docs | a7361e4de7c45407c2d929f3ec40db3bcedd4312fd322fe8a854b37065311390 |

Only public documentation was fetched for this independent review, with no
scientific API query, model call, ACS operation or credential access.
