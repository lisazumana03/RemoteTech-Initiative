# RemoteTech release-candidate changes

## Included in this package

- New public learner and school-admin registrations require email verification before login.
- Verification tokens are randomly generated, stored as hashes, expire after 24 hours, and are single-use.
- Existing accounts are migrated as verified to avoid locking out users during the upgrade.
- Added a resend-verification page and a school-admin dashboard section for verification status and resend requests.
- Password recovery remains available for all roles. Reset links expire after 30 minutes, are emailed only, and are never displayed in the browser when email delivery is unavailable.
- Password reset token consumption is now performed in the same database transaction as the password update.
- Added `.env.example`, `requirements.txt`, installation guidance, a POPIA/privacy policy template, and focused automated tests.
- Release package omits local databases, virtual environments, Git history, IDE metadata, bytecode and cache folders.

## Required configuration before email features work

Set `APP_BASE_URL` to the deployed app's public base URL and configure `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, and `SMTP_FROM`. A missing or incorrect setting means verification and recovery emails will not be delivered. The app intentionally does not display security links on screen as a fallback.

## Important limitations

This is a release candidate, not a declaration of production readiness or POPIA compliance. Run the tests in an environment with the listed dependencies installed, test email delivery using a dedicated test mailbox, complete all placeholders in `DATA_POLICY.md`, review school/tenant access boundaries, and perform a security review of student-submitted code execution before production use.
