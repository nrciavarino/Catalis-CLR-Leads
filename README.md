# Compass Leads

Booth lead-capture app: scan attendee badges (QR or photo), cross-reference them against an
attendee list, flag anyone missing contact info, and export a Salesforce-ready CSV — all from
a phone browser, no app install required.

Built for a single conference booth used by multiple reps at once; every phone reads and writes
the same live data.

**Current version:** `v1.8.0` (shown in the app's header and Setup tab — always check this
matches what's in this repo before assuming a device is up to date)

---

## Features

- **Badge scanning** — QR codes (JSON payload, vCard, or a bare ID string), or a photo read by
  Claude's vision API if a badge has no code at all
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
- **Event analytics screen** — a deeper, current-event-only view with a bar-chart breakdown of
  Reason for Engagement and Current Software, plus totals and a leads-by-rep breakdown, reached
  from a button on the Leads tab
- **Larger text option** — a Setup-tab toggle that bumps up text size on form fields, labels, and
  the lead list, without touching the tab bar, event pill, or badges (so nothing overflows)
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
- **[qr-scanner](https://github.com/nimiq/qr-scanner)** for QR decoding (1D barcodes are
  intentionally not decoded — badges with only a barcode fall back to photo/manual entry)
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

## Data model (Firestore)

```
events/{eventId}                        { name, createdAt, attendeeColumns: [{key,label}, ...] }
events/{eventId}/leads/{leadId}          { name, company, title, email, phone, notes,
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

- Firestore's test-mode rules let anyone with the project ID read/write the database, and expire
  after 30 days. Fine for a short conference as long as the URL and Firebase config aren't
  published anywhere public — treat it as an unlisted internal tool, not a locked-down one.
- The Anthropic API key, Firebase config, and each device's active-event choice all live in that
  device's browser storage (`localStorage`) — clearing browsing data wipes them; re-connect via
  the setup link (bookmark it) rather than re-pasting from scratch, and re-pick the event from
  the Events tab.
- The one-tap setup link embeds both secrets in the URL itself. Share it privately; don't post it
  anywhere that gets logged or archived outside your control.

## Changelog

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

- QR only — badges with just a 1D barcode aren't decoded (there's no reliable, dependency-light
  way to do that from a browser); they fall back to photo/manual entry.
- Splitting a single "Name" column (when a CSV has no separate First/Last columns) is a
  last-word-is-last-name guess — compound last names will split wrong.
- No offline support. Every screen assumes live connectivity to Firestore and, if used, the
  Anthropic API.
- Photo-based badge reading and the web-search lookup both require the person using that device
  to have entered their own Anthropic API key under Setup.
