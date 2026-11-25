# Compass Leads — Roadmap

Open backlog as of **v1.15.3**. Completed work lives in the README changelog.

**Lift scale (1–5):** 1 = a few lines or a small UI tweak; 2 = a contained feature reusing
existing patterns; 3 = new data shape or a new screen; 4 = multi-part feature, new integration,
or needs research; 5 = architectural change or a large rebuild. Estimates are rough and meant for
ordering, not scheduling.

## Feature backlog

Shipped in v1.15.3 and removed from this list: the manual-entry button on the Scan screen and deleting a qualification question that no lead has answered.

Shipped in v1.14.0 and removed from this list: event-level notes, per-event qualification fields,
and the web contact search for a lead missing only an email or phone. Possible follow-ons: a
per-question breakdown on the Analytics screen, and notification of reps when required answers are
missing (see the follow-up queue).

| Item | Lift | Notes |
|---|---|---|
| "Replace instead of add" choice when uploading an attendee CSV | 1 | Uploads currently add to the existing list. v1.13.7 added a remove-whole-list button, but a choice at upload time would save a step. |
| AI follow-up draft from the lead's notes, opened in Mail | 2 | Claude drafts from name, company, notes and product interest; opens in the rep's mail app via `mailto:` so nothing is sent from the app. Splits the lower-effort half off the follow-up item below. |
| Lead scoring (Hot / Warm / Cold) | 2 | Small schema addition, a chip on each lead, and a filter. Pairs well with the existing-customer flag. |
| Existing-customer flag | 2 | Flag leads who are already Community Justice customers, using the CJ client roster and attendee-list pre-flagging (merged into one item). Needs a decision on where the roster lives: bundled in the app, a Firestore collection, or a Setup import. |
| Follow-up queue: owner, status, due date | 3 | A "needs follow-up" list with an owner, a status (for example New, Contacted, Handed to AE) and a due date, with overdue items surfaced in the app. Covers the weakest phase today: what happens after the show. Needs a shared definition of the statuses. |
| Follow-up notifications (add-on to the queue) | +2 | Reminders for due or overdue follow-ups. In-app badges need no server. Push or email reminders need a server component (for example Firebase Cloud Messaging with a Cloud Function), and as far as I know iOS push requires the app to be installed to the home screen. Best done together with the platform hardening work. |
| Broader contact enrichment | 3 | Beyond the existing `.gov` / county-directory web search. |
| Jurisdiction intelligence card | 3 | Needs a data-source decision first. |
| Booth traffic co-pilot | 3 | Depends on which signals it should read. |
| AI-assisted note capture | 4 | |
| Follow-up message / e-card correspondence | 4 | Needs research before scoping. The AI-draft-in-Mail half is now its own item above. |
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
| Tests, CI, and a build/deploy pipeline | 3 | A headless Playwright regression suite now exists in `tests/` (stubbed Firestore; run by hand). Still missing: running it automatically on every push, linting, real-device camera/barcode coverage, and automated deploy. |
| Self-host or bundle third-party libraries; add integrity hashes | 2 | Libraries load from public CDNs at runtime (cdnjs, unpkg, gstatic). A blocked or compromised CDN degrades or alters the app. |
| Split `index.html` into modules | 5 | One ~2,800-line file is fine for a solo project and hard for a team to review or test. The React rebuild would cover this. |
| Version-controlled Firestore indexes (`firestore.indexes.json`) | 1 | Cross-event matching needs three collection-group indexes that are currently created by hand (README Setup step 7). |
| Move repo and Firebase project under company ownership | 1 | The repo is on a personal GitHub account; project ownership and billing should be recorded and transferred. |
| Surface silent failures: error reporting and degraded-mode notices | 2 | Several failures have been invisible to the rep and to us (a broken CDN library showed up only as "barcode reading unavailable", a swallowed Firestore error just looks like missing data). Add centralized error capture (for example an error-log collection or a hosted error tracker) and a visible banner whenever a feature is running degraded. |
| Data privacy and retention review | 2 | Lead PII (names, emails, phones, free-text notes) is stored in Firebase, and badge photos and an aggregated lead summary are sent to the Anthropic API. Needs an IT/security review and a retention decision. |
