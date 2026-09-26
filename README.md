# Compass Leads

Booth lead-capture app: scan attendee badges (QR or photo), cross-reference them against an
attendee list, flag anyone missing contact info, and export a Salesforce-ready CSV — all from
a phone browser, no app install required.

Built for a single conference booth used by multiple reps at once; every phone reads and writes
the same live data.

**Current version:** `v1.11.0` (shown in the app's header and Setup tab — always check this
matches what's in this repo before assuming a device is up to date)

---

## Features

- **Badge scanning** — QR codes (JSON payload, vCard, or a bare ID string), 1D barcodes
  (Code128/39, EAN, UPC, ITF, Codabar), or a photo read by Claude's vision API if a badge has no
  code at all. QR and barcode both run continuously off the same live camera view — nothing to
  pick or switch between, the app just recognizes whichever one is in frame
- **Business card photo reading** — the same "No QR — take photo" flow used for code-less badges
  also recognizes business cards; Claude decides which one it's looking at and reads back
  whatever name/company/title/email/phone it can find either way
- **Attendee cross-reference** — upload any CSV; name/company/email/phone columns are matched
  automatically however they're labeled, and anything else in the file becomes its own column
- **Web-search fallback** — if a lead is missing contact info and the attendee list doesn't have
  it either, one tap searches public `.gov`/county-directory listings for it (opt-in, not
  automatic — it's a multi-second call and shouldn't slow down scanning). Once a search actually
  completes — whether it finds something or comes up empty — that lead remembers it was already
  tried, so reopening it shows "search again" instead of re-running a search that already ran. A
  failed/errored attempt (bad key, no connection) doesn't count, so that case still shows as a
  fresh, unsearched lead
- **Team activity** — a live card on the Leads tab showing total leads, matched-attendee count,
  missing-contact count, and a per-rep leaderboard for the current event
- **Prize-winner picker** — pulls one random lead from the current event and shows their name,
  company, and captured contact info as tap-to-act links (email/call/text); tap again for a
  re-draw
- **One-tap contact everywhere** — any email or phone number shown in the app (lead list, prize
  winner) is a live link — tap to email, call, or text straight from where it's displayed
- **Attendee table, sized for a phone — and for a bigger screen too** — on a phone, First/Last
  Name freeze in place on the left and the row-action buttons freeze on the right, so only the
  middle columns (Company, Email, Phone, and anything custom) scroll and the name stays visible
  the whole time. On a tablet/desktop-width screen (roughly 700px and up), Name unfreezes and
  sizes like any other column instead, since there's room to show every column without swiping
  and the fixed-width freeze was cramping and truncating names there
- **Click-to-sort attendee list** — tap any column header to sort the table by that column; tap
  again to reverse direction. The chosen column and direction are remembered on that device for
  next time
- **Resizable attendee columns** — drag the edge of any column header to widen or narrow it; the
  size is remembered per column on that device, so it doesn't reset the next time the table loads
- **Add an attendee straight to leads** — a quick action on each attendee row opens the same
  review/edit screen a badge scan would, prefilled with that attendee's info
- **Cross-event relationship memory** — if a lead's email, phone, or name+company matches
  someone captured at a *different* past event, the review screen surfaces it: which event, when,
  and what was noted. An email or phone match is shown as certain; a name+company-only match is
  flagged "verify" since names repeat. Only works for leads captured from v1.11.0 onward — see
  [Known limitations](#known-limitations)
- **Event analytics screen** — a deeper, current-event-only view with a bar-chart breakdown of
  Reason for Engagement and Current Software, plus totals and a leads-by-rep breakdown, reached
  from a button on the Leads tab
- **Larger text option** — a Setup-tab slider (100%–160%) that scales text size on form fields,
  labels, and the lead list, without touching the tab bar, event pill, or badges (so nothing
  overflows). Defaults to 120% for easier reading at a booth; each device remembers its own
  chosen size
- **Missing-contact flagging** — visually flagged on the lead card and in the CSV export, both
  at the moment of scanning and later when editing
- **Duplicate-scan detection** — warns if someone else on the team already scanned this name
- **Editable competitor list** — the "current software" dropdown is a shared, editable list, not
  hardcoded
- **Editable engagement-reason list** — same pattern for "why did this person stop by" (defaults:
  Saw a demo, Existing Customer, Interested in Learning more, Drawing registrant)
- **Multiple events, per-device** — each phone stays on whichever event it picks until that rep
  changes it, so reps at different conferences at the same time can each work their own event.
  Reps who are both on the same event still share leads, attendees, and duplicate warnings live.
  Add, rename, or delete events from the Events tab; a brand-new device with no choice yet falls
  back to whatever event was most recently made active anywhere on the team
- **In-app help** — a single "What do you need help with?" menu in the Setup tab, collapsed by
  default — tap it to expand the full list of topics (event switcher, photo reading, sync dot,
  lead badges, CSV export, attendee-list matching, duplicate warnings, web contact lookup,
  current-software field, team activity, prize winner, event analytics), then tap any topic for
  a plain-English explanation without leaving the screen
- **Salesforce-ready export** — CSV with First/Last Name, Company, Title, Email, Phone, Lead
  Source, Contact Source, and more
- **Installable** — "Add to Home Screen" on iOS/Android for an app-like icon, no App Store
- **One-tap team setup** — generate a link with your Firebase config + API key baked in; anyone
  who opens it is fully configured, no copy-pasting

## How it's built

- **`index.html`** is the entire app — plain HTML/CSS/JS, no build step, no framework
- **[Firestore](https://firebase.google.com/docs/firestore)** (Firebase, free tier) is the shared
  database — every phone reads/writes the same events, leads, and attendees in real time
- **Anthropic API**, called directly from the browser with your own API key
  (`anthropic-dangerous-direct-browser-access`), for:
  - reading badge photos (vision)
  - the optional web-search contact lookup (`web_search` tool)
- **[qr-scanner](https://github.com/nimiq/qr-scanner)** for QR decoding, running continuously
  against the live camera view
- **[@zxing/browser](https://github.com/zxing-js/browser)** for 1D barcode decoding (Code128/39,
  EAN, UPC, ITF, Codabar) — a second, independent check against that same camera view on a
  ~450ms interval, so QR and barcode both work without the rep picking a mode. Loaded
  defensively: if this script fails to load, or its API doesn't match what's expected, barcode
  detection just silently stays off and QR scanning is completely unaffected
- **[PapaParse](https://www.papaparse.com/)** for CSV import/export
- Hosted anywhere static (GitHub Pages, Firebase Hosting, Netlify) — camera access requires
  HTTPS, so it won't work opened directly from a local file

## Files

| File | Purpose |
|---|---|
| `index.html` | The whole app |
| `manifest.json` | PWA manifest, enables "Add to Home Screen" on Android |
| `service-worker.js` | Minimal service worker, exists only so Chrome treats the app as installable |
| `icon-192.png`, `icon-512.png` | Home-screen icons |
| `test-badges.html`, `test-badges-2.html` | Printable/on-screen-scannable fake badges for testing the scan flow (QR, vCard, barcode, no-code, varied colors/layouts) |
| `sample-attendees.csv`, `sample-attendees-2.csv` | Sample attendee lists matching the test badges, for exercising attendee-match and dynamic columns |
| `firestore.rules` | Firestore security rules — requires anonymous auth (see Security notes below); publish this in the Firebase console, don't leave the project on its default test-mode rules |

## Setup

### 1. Create a Firebase project (free, ~5 minutes)

1. [console.firebase.google.com](https://console.firebase.google.com) → **Add project**.
2. **Build → Firestore Database → Create database.** Start in test mode (see
   [Security notes](#security-notes) below).
3. **Project settings → Your apps → Web (`</>`) → Register app.** Copy the `firebaseConfig`
   object it gives you.

### 2. Host the files

Needs to be served over `https://` — camera access won't work otherwise. Easiest no-computer
option:

1. Save all the repo's files to your device.
2. Create a GitHub repo, upload the files (**Add file → Upload files**, or
   `github.com/<user>/<repo>/upload/main` if the button's hard to find on mobile).
3. Repo **Settings → Pages** → Source: **Deploy from a branch**, Branch: **main**, folder:
   **/ (root)** → **Save**. Wait ~1 minute for a `https://<user>.github.io/<repo>/` URL.

(Firebase Hosting or Netlify work too, if you've got a CLI handy — same static files either way.)

### 3. Connect the app

Open the hosted URL. First run shows a **Connect Compass Leads** screen — paste in the
`firebaseConfig` from step 1. That's saved to that device's browser only; repeat per device, or
use the one-tap setup link below.

### 4. Optional: badge photo reading + web search

Setup tab → paste an [Anthropic API key](https://console.anthropic.com) (pay-as-you-go, separate
billing from any Claude.ai subscription). Enables "No QR — take photo" and the web-search
contact lookup. Skip it and both just fall back to manual entry.

### 5. Optional: one-tap link for the rest of the team

Setup tab → **Generate setup link** → send it privately (DM, not a public channel — it contains
your Firebase config and API key in plain text). Anyone who opens it is fully configured
automatically.

### 6. Required: enable anonymous auth and publish the security rules

Skipping this leaves the project on Firebase's default test-mode rules, which allow anyone on
the internet with your project ID to read/write your database, and which Firebase automatically
locks down (denying **all** requests, including the app's own) 30 days after project creation.

1. Firebase console → **Authentication** → **Sign-in method** tab → **Anonymous** → **Enable** →
   **Save**. (Nothing user-facing changes — the app signs in silently on connect, no login
   screen.)
2. Firebase console → **Firestore Database** → **Rules** tab → replace the contents with this
   repo's `firestore.rules` → **Publish**.
3. Reload the app on a device and confirm leads/attendees still load — if step 1 was skipped,
   every read/write will fail once the rules are published.

If you're re-securing a project that's already past its 30-day test-mode window and denying all
requests, do step 1 and step 2 in that order — signing in has to work before the rules can
require it.

### 7. Required for cross-event memory: one Firestore index

The email and phone matches work automatically (Firestore indexes single fields by default,
including for the collection-group query this feature relies on). The name+company match needs
one composite index created once:

1. Firebase console → **Firestore Database** → **Indexes** tab → **Add index**.
2. **Collection ID:** `leads`, scope **Collection group** (not "Collection").
3. Fields: `name` (Ascending), then `company` (Ascending) → **Create**.

Until this is created, name+company matching silently fails (logged to the browser console, not
shown to the rep) while email/phone matching keeps working — see
[Data model](#data-model-firestore) below.

## Data model (Firestore)

```
events/{eventId}                        { name, createdAt, attendeeColumns: [{key,label}, ...] }
events/{eventId}/leads/{leadId}          { name, company, title, email, phone, notes,
                                            emailLower, phoneNormalized,
                                            currentSoftware, reasonForEngagement, contactSource,
                                            source, matched, webSearchAttempted, scannedBy, savedAt }
events/{eventId}/attendees/{attendeeId}  { firstName, lastName, company, email, phone, ...any
                                            custom columns from an uploaded CSV }
meta/shared                              { activeEventId }
meta/competitors                         { list: [...] }
meta/engagementReasons                   { list: [...] }
```

`meta/shared.activeEventId` is now only a **default** for a brand-new device that hasn't picked
an event yet — each phone tracks its own active event locally (in that device's browser
storage) once a rep makes a choice, and that choice sticks until they change it on their own
device. It doesn't get overridden by other reps switching events on their phones.

Attendee columns are file-driven: the four canonical fields (First Name, Last Name, Company,
Email, Phone) always exist; anything else in an uploaded CSV becomes its own column,
auto-registered on the event so every rep's table matches. Leads deliberately stay single-field
for name (a badge scan or photo read has no reliable way to split first/last).

`emailLower` (lowercased email) and `phoneNormalized` (digits-only, last 10) are derived,
write-time-only copies used exclusively for cross-event matching — never shown or exported, so
they can't be confused with the real `email`/`phone` fields a rep sees and edits. They're saved
starting in v1.11.0; leads captured before that don't have them and won't surface in a future
cross-event match (see [Known limitations](#known-limitations)).

Cross-event matching runs a Firestore **collection-group query** across every event's `leads`
subcollection at once, rather than a separate top-level "contacts" collection — no data
restructuring, and the existing security rule for `events/{eventId}/leads/{leadId}` already
covers it (a collection-group query is still bound by the same per-path rule). See
[Setup](#setup) step 7 for the one index this needs.

`contactSource` on a lead is one of `badge`, `attendee-list`, `web-search`, or empty — mainly so
a web-found contact can be flagged for verification in the CSV export rather than treated as
confirmed.

`webSearchAttempted` is `true` once a web-contact search has actually completed for that lead —
found something or confirmed nothing there — so the edit screen can offer "search again" instead
of a fresh search. It's only set on a completed attempt, never on a failed one (bad key, no
connection), so an errored attempt still shows as unsearched.

## Versioning

`APP_VERSION` is a plain string constant near the top of the `<script>` block in `index.html`,
shown in the header (next to the rep's name) and at the bottom of the Setup tab. Bump it on every
change you ship, so anyone can glance at a device and tell whether it's running the latest file —
this matters more than usual here since there's no auto-update mechanism; someone has to
manually replace `index.html` on the host.

## Security notes

- **Firestore rules require anonymous auth.** The app calls
  `firebase.auth().signInAnonymously()` right after connecting — silent, no login
  screen, no prompt — and `firestore.rules` (in this repo) requires
  `request.auth != null` on every read/write. This isn't per-user data isolation
  (every signed-in device can read/write everything, matching the shared-team-data
  model above); it exists to stop the raw Firestore REST API from being wide open
  to anyone on the internet with the project ID, which is what Firebase's test-mode
  default allows and what triggers its 30-day auto-lockout warning. **You must
  enable the Anonymous sign-in provider** (Firebase console → Authentication →
  Sign-in method → Anonymous → Enable) and **publish `firestore.rules`**
  (Firestore Database → Rules → paste the file's contents → Publish) — see
  [Setup](#setup) step 6 below. Skipping either step means the app can't read or
  write data at all once you publish the rules.
- The Anthropic API key, Firebase config, and each device's active-event choice all live in that
  device's browser storage (`localStorage`) — clearing browsing data wipes them; re-connect via
  the setup link (bookmark it) rather than re-pasting from scratch, and re-pick the event from
  the Events tab.
- The one-tap setup link embeds both secrets in the URL itself. Share it privately; don't post it
  anywhere that gets logged or archived outside your control.
- **Cross-event memory widens what a routine lookup touches.** Before v1.11.0, a device only ever
  read the one event's data it was actively subscribed to. The cross-event match runs a query
  across *every* event's leads in the project on every single scan/save, not just the current
  one — so in practice (not just in theory) any connected device now regularly reads lead data,
  including notes, from events it was never switched to. This isn't a new hole in the trust
  model — the existing rules already allow any signed-in device to read any event's data on
  request — but it changes an occasional possibility into routine behavior. If that's a problem
  for how your team uses this (e.g. notes written assuming only that event's reps would see
  them), that's worth knowing before turning this on, not after.

## Changelog

- **v1.11.0**
  - Added: 1D barcode decoding (Code128/39, EAN, UPC, ITF, Codabar) — runs alongside the existing
    QR decoder against the same live camera view, so badges with only a barcode no longer fall
    back to photo/manual entry. On-screen instructions only claim barcode support once it's
    confirmed active, never unconditionally
  - Added: business card photo reading — the existing "No QR — take photo" flow now recognizes
    business cards as well as badges; same button, Claude decides which one it's looking at
  - Added: cross-event relationship memory — the review screen now surfaces a prior encounter
    with this person from a *different* past event (email/phone match shown as certain,
    name+company shown as "verify"), with a visible "Checking past events…" indicator so a slow
    connection doesn't make the check silently disappear before it has a chance to complete.
    Requires one Firestore composite index for the name+company match — see Setup step 7. Only
    matches leads captured from this version onward (see Known limitations)
- **v1.10.0**
  - Added: `firestore.rules`, requiring anonymous auth on every read/write, plus a silent
    `signInAnonymously()` call in the app's Firebase connect flow — replaces Firebase's default
    test-mode rules (open to anyone on the internet with the project ID, and set to deny all
    requests 30 days after project creation). See README → Security notes and Setup step 6;
    **enabling Anonymous auth and publishing the rules is a required manual step in the Firebase
    console**, not something this file change does on its own
- **v1.9.1**
  - Fixed: iPhone reps having to re-allow the camera on nearly every scan — after each capture the
    app was fully stopping and destroying the camera stream (`stop()` + `destroy()`), so getting
    back to scanning required a brand-new `getUserMedia()` call every time. iOS Safari (especially
    for a home-screen-installed PWA) is far more likely to re-prompt on each fresh call than
    desktop Chrome is. Internal navigation (opening the review screen, switching tabs away from
    Scan) now pauses the stream instead of releasing it, so it resumes without a new permission
    check; tapping "Stop camera" still fully releases it, since that's a deliberate action
- **v1.9.0**
  - Changed: text size in Setup is now a slider (100%–160%) instead of an on/off checkbox, so
    reps can pick their own comfortable size rather than one fixed "larger" preset
  - Changed: text size now defaults to 120% (larger) on a fresh device instead of defaulting off;
    a device that already had the old checkbox turned off keeps its normal size instead of
    jumping up
- **v1.8.0**
  - Added: resizable attendee-table columns — drag a column header's edge to widen/narrow it,
    remembered per column on that device
  - Changed: Setup → Help is now a collapsed "What do you need help with?" menu that expands to
    show the full topic list, instead of listing every topic on the screen right away
  - Changed: the attendee table's Name columns no longer use a fixed 72px width; they size like
    any other column and can be resized like one, on phone and desktop alike (the phone-width
    freeze-in-place behavior is unchanged — only the sizing was)
- **v1.7.0**
  - Fixed: the frozen Name columns in the attendee table no longer stay cramped at a fixed 72px
    on tablet/desktop-width screens — above roughly 700px wide, Name unfreezes and sizes like any
    other column, since there's room to show every column at once and the phone-sized freeze was
    only needed for the narrow-swipe layout
  - Added: click-to-sort on the attendee table — tap a column header to sort by it, tap again to
    reverse; the chosen column/direction is remembered on that device for next time
  - Changed: consolidated Help down to a single entry point — removed the inline "?" tips that
    were scattered next to individual controls throughout the app (event switcher, photo reading,
    sync dot, lead badges, CSV export, attendee matching, duplicate warnings, web search,
    current-software field, team activity, prize winner, event analytics); Setup → Help now lists
    all of them in one place
- **v1.6.0**
  - Fixed: attendee table sizing on phone — Name now freezes on the left and row actions freeze
    on the right, so only the middle columns scroll
  - Added: quick "add to leads" action on each attendee row, prefilling the same review screen
    a badge scan would use
  - Added: a dedicated event analytics screen (current event only) with bar-chart breakdowns of
    Reason for Engagement and Current Software, plus totals and leads-by-rep
- **v1.5.0**
  - Fixed: web contact search no longer gets stuck on "Searching the web…" when it finds
    nothing, and the "already searched" marker now actually shows up
  - Fixed: the Events tab "Active" badge / "Make active" button now updates immediately when
    you switch events (previously only the header pill updated)
  - Added: one-tap contact links (email/call/text) on the prize-winner screen and the lead list
- **v1.4.0**
  - Fixed: the rep's name now displays in "Signed in as" on repeat visits (previously it only
    painted on first-time setup, even though the name was already being used correctly under the
    hood for lead attribution)
  - Added: web-search-attempted tracking on leads (see Data model above)
  - Added: Team activity card on the Leads tab (totals + per-rep leaderboard)
  - Added: prize-winner picker on the Leads tab
  - Added: larger-text display option in Setup
- **v1.3.0**
  - Added: per-device active event switching — each phone now stays on whichever event it picks
    until that rep changes it, instead of one global active event shared by the whole team
  - Added: in-app Help — a dedicated Help section in Setup, plus inline "?" tips on ~9 controls
- **v1.0.2** — last version tracked before this changelog started; see the rest of this README
  for the feature set as of that release

## Known limitations

- 1D barcode decoding depends on a third-party CDN script (`@zxing/browser`) loading
  successfully; if it doesn't (network policy, ad-blocker, offline install), the app falls back
  to QR + photo/manual entry with no error shown to the rep — the on-screen instructions
  correctly stop mentioning "barcode" in that case, but there's no visible warning that it's
  degraded from a normal launch. Check the browser console if barcode scans aren't registering.
- Cross-event relationship memory only matches leads saved from v1.11.0 onward — `emailLower`
  and `phoneNormalized` aren't retroactively added to leads captured before that, so a real past
  encounter from an older event won't surface until that person is captured again after this
  update. There's also no bulk backfill tool for existing data.
- Splitting a single "Name" column (when a CSV has no separate First/Last columns) is a
  last-word-is-last-name guess — compound last names will split wrong.
- No offline support. Every screen assumes live connectivity to Firestore and, if used, the
  Anthropic API.
- Photo-based badge reading and the web-search lookup both require the person using that device
  to have entered their own Anthropic API key under Setup.
