# Compass Leads

Booth lead-capture app: scan attendee badges (QR or photo), cross-reference them against an
attendee list, flag anyone missing contact info, and export a Salesforce-ready CSV — all from
a phone browser, no app install required.

Built for a single conference booth used by multiple reps at once; every phone reads and writes
the same live data.

**Current version:** `v1.0.2` (shown in the app's header and Setup tab — always check this
matches what's in this repo before assuming a device is up to date)

---

## Features

- **Badge scanning** — QR codes (JSON payload, vCard, or a bare ID string), or a photo read by
  Claude's vision API if a badge has no code at all
- **Attendee cross-reference** — upload any CSV; name/company/email/phone columns are matched
  automatically however they're labeled, and anything else in the file becomes its own column
- **Web-search fallback** — if a lead is missing contact info and the attendee list doesn't have
  it either, one tap searches public `.gov`/county-directory listings for it (opt-in, not
  automatic — it's a multi-second call and shouldn't slow down scanning)
- **Missing-contact flagging** — visually flagged on the lead card and in the CSV export, both
  at the moment of scanning and later when editing
- **Duplicate-scan detection** — warns if someone else on the team already scanned this name
- **Editable competitor list** — the "current software" dropdown is a shared, editable list, not
  hardcoded
- **Multiple events** — switch, rename, or add events; everything scanned ties to whichever
  event is active, shared across every phone
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
                                            currentSoftware, contactSource, source, matched,
                                            scannedBy, savedAt }
events/{eventId}/attendees/{attendeeId}  { firstName, lastName, company, email, phone, ...any
                                            custom columns from an uploaded CSV }
meta/shared                              { activeEventId }
meta/competitors                         { list: [...] }
```

Attendee columns are file-driven: the four canonical fields (First Name, Last Name, Company,
Email, Phone) always exist; anything else in an uploaded CSV becomes its own column,
auto-registered on the event so every rep's table matches. Leads deliberately stay single-field
for name (a badge scan or photo read has no reliable way to split first/last).

`contactSource` on a lead is one of `badge`, `attendee-list`, `web-search`, or empty — mainly so
a web-found contact can be flagged for verification in the CSV export rather than treated as
confirmed.

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
- The Anthropic API key and Firebase config live in each device's browser storage
  (`localStorage`) — clearing browsing data wipes them; re-connect via the setup link (bookmark
  it) rather than re-pasting from scratch.
- The one-tap setup link embeds both secrets in the URL itself. Share it privately; don't post it
  anywhere that gets logged or archived outside your control.

## Known limitations

- QR only — badges with just a 1D barcode aren't decoded (there's no reliable, dependency-light
  way to do that from a browser); they fall back to photo/manual entry.
- Splitting a single "Name" column (when a CSV has no separate First/Last columns) is a
  last-word-is-last-name guess — compound last names will split wrong.
- No offline support. Every screen assumes live connectivity to Firestore and, if used, the
  Anthropic API.
- Photo-based badge reading and the web-search lookup both require the person using that device
  to have entered their own Anthropic API key under Setup.
