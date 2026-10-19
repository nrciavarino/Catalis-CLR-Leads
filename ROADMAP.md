# Compass Leads — Roadmap

Open backlog as of **v1.13.4**. Completed work lives in the README changelog.

**Lift scale (1–5):** 1 = a few lines or a small UI tweak; 2 = a contained feature reusing
existing patterns; 3 = new data shape or a new screen; 4 = multi-part feature, new integration,
or needs research; 5 = architectural change or a large rebuild. Estimates are rough and meant for
ordering, not scheduling.

## Feature backlog

| Item | Lift | Notes |
|---|---|---|
| Lead scoring (Hot / Warm / Cold) | 2 | Small schema addition, a chip on each lead, and a filter. Pairs well with the existing-customer flag. |
| Existing-customer flag | 2 | Flag leads who are already Community Justice customers, using the CJ client roster and attendee-list pre-flagging (merged into one item). Needs a decision on where the roster lives: bundled in the app, a Firestore collection, or a Setup import. |
| Web-search-for-missing-info on the edit screen | 2 | Parity with the web-contact search already available on the new-lead review flow. |
| Event-level notes | 3 | Free-form notes attached to an event rather than a lead: schedule, venue (booth location, power, wifi, load-in), and lessons learned about setup and staffing. Likely a running list of short timestamped, attributed entries rather than one text blob, so two reps editing at once don't overwrite each other. Optional tags (Schedule / Venue / Setup / Staffing) add roughly half a point. Including the notes in the AI event readout is roughly +1. Touches Firestore data access, so review `firestore.rules` when building. |
| Broader contact enrichment | 3 | Beyond the existing `.gov` / county-directory web search. |
| Jurisdiction intelligence card | 3 | Needs a data-source decision first. |
| Booth traffic co-pilot | 3 | Depends on which signals it should read. |
| AI-assisted note capture | 4 | |
| Follow-up message / e-card correspondence | 4 | Needs research before scoping. |
| NFC / RFID badge reading | 4 | Android-only (Web NFC); not available on iOS. |
| Offline capture with sync-later | 5 | Needs a real service-worker cache plus a local write queue. The current service worker only enables installation. |
| Deeper Salesforce integration | 5 | Today the app produces a Salesforce-shaped CSV for manual import. |
| Full React rebuild | 5 | Long-range. Would also resolve the single-file maintainability concern below. |

## Platform hardening (identified for a production handoff)

These are the gaps between "works well for a sales team at a booth" and "supported company
application." They are known and documented here rather than hidden.

| Item | Lift | Why it matters |
|---|---|---|
| Move AI calls behind a server-side proxy | 3 | Each rep's own Anthropic API key currently lives in their browser's `localStorage` and calls go direct from the browser. A proxy (e.g. a Cloud Function) would hold one company key, enable usage limits and logging, and keep keys off devices. |
| Real authentication and per-role access rules | 4 | Auth is anonymous sign-in: any device that loads the app can read and write everything, and there is no per-user identity or audit trail. Company SSO (e.g. Microsoft Entra via Firebase Auth) plus role-scoped rules would fix this. The Setup PIN is a client-side deterrent only and becomes moot. |
| Tests, CI, and a build/deploy pipeline | 3 | There is currently none. At minimum: linting, a smoke test of the scan → review → save flow, and automated deploy. |
| Self-host or bundle third-party libraries; add integrity hashes | 2 | Libraries load from public CDNs at runtime (cdnjs, unpkg, gstatic). A blocked or compromised CDN degrades or alters the app. |
| Split `index.html` into modules | 5 | One ~2,800-line file is fine for a solo project and hard for a team to review or test. The React rebuild would cover this. |
| Version-controlled Firestore indexes (`firestore.indexes.json`) | 1 | Cross-event matching needs three collection-group indexes that are currently created by hand (README Setup step 7). |
| Move repo and Firebase project under company ownership | 1 | The repo is on a personal GitHub account; project ownership and billing should be recorded and transferred. |
| Data privacy and retention review | 2 | Lead PII (names, emails, phones, free-text notes) is stored in Firebase, and badge photos and an aggregated lead summary are sent to the Anthropic API. Needs an IT/security review and a retention decision. |
