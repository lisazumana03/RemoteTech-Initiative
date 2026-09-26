# RemoteTech — Data Retention & Hosting Policy

*Last updated: [fill in date before sending to a school]*

This document is written to answer what a school's procurement or IT
contact typically asks before signing off on a classroom tool. It
describes what RemoteTech actually does today, based on the current
codebase — not aspirational policy. Update it if the implementation
changes.

## 1. What personal information is collected

Per the POPIA notice already shown at registration (`register.py`):

- Full name
- Username
- Email address
- School name and class code (optional, self-reported)
- Learning progress: points, badges, completed quests, time spent per
  quest, last-active timestamp

RemoteTech does **not** collect: ID numbers, dates of birth, home
addresses, phone numbers, payment card details, or biometric data.
Payment details for school licenses are handled entirely by Stripe —
this app never sees or stores card numbers (see §5).

Passwords are hashed with bcrypt before storage; the plaintext password
is never written to disk or logged.

## 2. Where data is hosted

- **Database:** by default, a local SQLite file (`remotetech.db`) for
  development. In production, set the `DATABASE_URL` environment
  variable to point at a hosted Postgres instance (see `db.py`) — for
  example a managed Postgres add-on from Render or Railway.
- **Region:** *[fill in — depends on which host/region you provision;
  for a South African pilot, prefer a host with an EU or, if available,
  an Africa-region data center, and state the actual region here once
  chosen]*.
- **Application hosting:** *[fill in — e.g. Render/Railway web service
  running this Streamlit app]*.
- **Backups:** *[fill in — most managed Postgres add-ons take automatic
  daily backups with a retention window; state the provider's actual
  backup retention period once you've chosen a host, e.g. "7 days of
  automatic daily backups, provider-managed"]*.
- **Subprocessors:** the hosting provider (database + app), and Stripe
  for payment processing. No other third parties receive student data.
  RemoteTech does not use student data for advertising, and does not
  sell or share it with third parties, per the existing POPIA notice.

## 3. Retention period

- **Active accounts:** progress data is retained for as long as the
  account is active, so a student's history is available to them and
  their teacher across a school year.
- **Inactive accounts:** *[decide and fill in a concrete number — e.g.
  "accounts inactive for 24 months are flagged for deletion; the school
  admin is notified before deletion occurs"]*. The admin dashboard
  already surfaces students inactive 7+ days (`get_inactive_students`)
  as an early-warning signal, not a deletion trigger.
- **Demo/trial account:** the shared demo account's progress is never
  persisted — it resets by design (`is_demo` handling in
  `remote_tech_app.py`), so no personal data accumulates there.
- **Password reset tokens:** expire after 30 minutes and are stored only
  as a hash, never in plaintext (`remotetech_data.py`,
  `RESET_TOKEN_TTL_MINUTES`).
- **License keys** (school payment/activation): stored only as a hash,
  same pattern as password reset tokens (`billing.py`).

## 4. Deletion

A user (or a teacher/admin on their behalf) can request deletion at any
time. This is already implemented end-to-end: the **Profile page** has a
"Delete my account and all my data" control (`profile.py`) that calls
`delete_user_data(username)` in `remotetech_data.py`, which removes the
user's row and all associated progress, quest-time, and password-reset
records from the database in one operation.

Deletion requests from a school (e.g. end of contract, or a parent
request under POPIA) can be actioned by a school's own admin account, or
by RemoteTech operator on request, within *[fill in — e.g. "30 days"]*.

## 5. Payments

Card payments are processed by Stripe via a hosted Stripe Checkout page
(`billing.py`, `pricing.py`). Card numbers and other cardholder data are
entered directly into Stripe's page and never transit or touch
RemoteTech's servers or database. RemoteTech stores only: the school
name, a contact email, the plan purchased, and a hashed license key —
never payment card details.

## 6. Security measures already in place

- Passwords hashed with bcrypt (never stored or logged in plaintext).
- Password reset and license-activation tokens stored as SHA-256 hashes,
  single-use, time-limited.
- Role-based access: only accounts with `role = "admin"` can view the
  Admin Dashboard or other students' progress; students only ever see
  their own data and a leaderboard scoped to their class.
- Student-submitted code runs in an isolated sandboxed subprocess with a
  restricted builtins list, wall-clock timeout, and (on POSIX hosts)
  CPU/memory limits (`sandbox.py`) — this protects the hosting
  infrastructure, not personal data directly, but is worth mentioning to
  a school's IT reviewer since "students submit and run code" is
  sometimes flagged as a risk on its own.

## 7. Contact

For a data access, correction, or deletion request, or any other privacy
question, contact: *[fill in — an actual email address a school can use;
POPIA requires this to be a real, monitored inbox]*.

---
**Before sending this to a school:** fill in every `[fill in ...]`
bracket above with your actual hosting provider, region, backup
retention window, and contact email. A procurement reviewer will notice
placeholder text — better to send this once it's concrete than to send
it early and follow up with corrections.
