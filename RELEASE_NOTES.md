# RemoteTech release-candidate changes

## Account registration update

- Removed email verification from learner and school-admin registration.
- Newly registered accounts can log in immediately after successful registration.
- Removed verification routes, resend-verification UI, admin verification management, verification token functions, and verification-specific tests.
- Retained email delivery only for optional password recovery and progress-sharing features.
- Retained existing account records and passwords; the legacy verification database column/table, if present in an existing database, are ignored and are not required by the updated application.

## Important limitations

This is a release candidate, not a declaration of production readiness or POPIA compliance. Run the full test suite, complete all placeholders in `DATA_POLICY.md`, review school/tenant access boundaries, and perform a security review of student-submitted code execution before production use.
