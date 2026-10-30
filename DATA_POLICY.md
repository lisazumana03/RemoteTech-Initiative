# RemoteTech — Privacy, Data Retention and Security Notice

**Document status:** Draft template — not approved legal advice. Complete the deployment-specific fields before sharing this document with a school or processing real learner data.

**Last reviewed:** [ENTER DATE]
**Responsible organisation/operator:** [ENTER LEGAL NAME AND CONTACT DETAILS]
**Privacy / Information Officer contact:** [ENTER MONITORED EMAIL AND POSTAL/PHYSICAL CONTACT DETAILS AS APPLICABLE]
**Application URL:** [ENTER PRODUCTION URL]

## 1. Purpose and scope

RemoteTech provides Python learning activities, quests, progress tracking, and school/teacher reporting. This notice describes the categories of information the application is designed to process. The operator must confirm these details against the deployed application and all connected providers before release.

## 2. Personal information processed

Depending on the features used, RemoteTech may process:

- Full name, username and email address.
- Account role (learner or school administrator/teacher), school name and class code.
- Password hashes, account verification status and time-limited password-reset/verification token hashes.
- Learning records such as points, badges, completed quests, activity/time records, and feedback submitted by a user.
- School licence metadata, such as school name, contact email, plan and hashed licence key.
- Technical information in application, hosting, database, email-provider and payment-provider logs, depending on deployment configuration.

Passwords are hashed with bcrypt before storage. Verification and password-reset tokens are stored as SHA-256 hashes rather than raw tokens. Do not promise that no personal information appears in logs until the deployed logging configuration has been checked.

## 3. Purposes and legal basis

Information may be used to create and secure accounts, deliver lessons, save learning progress, support teacher reporting, operate school licences, recover accounts, respond to support/privacy requests, and maintain service security.

The operator and each participating school must document the applicable lawful basis for each processing purpose under POPIA. Do not rely on a generic checkbox as a substitute for assessing the correct lawful basis, especially for children's personal information. Obtain appropriate advice and establish the required authorisations and safeguards before onboarding learners.

## 4. Children and school responsibilities

RemoteTech may be used by children. Before a school pilot, document who determines the purposes and means of processing, who acts as operator/service provider, which school officials may access learner records, how parents/guardians and learners receive appropriate notices, and what authorisations are required by applicable law. Use age-appropriate notices and minimise collected information. Do not launch to children until these arrangements have been reviewed.

## 5. Access, visibility and sharing

Learners can access their own account and learning progress. School/teacher administration features may expose learner progress for educational support; the operator must verify that access is restricted to the correct school and class before production use. Leaderboards and progress-sharing links can disclose learner information; explain these features to users and schools, provide suitable controls, and ensure shared links expire and can be revoked where supported.

## 6. Hosting and third-party providers — complete before release

- **Application host and region:** [ENTER PROVIDER, COUNTRY/REGION, AND SERVICE]
- **Database provider and region:** [ENTER PROVIDER, COUNTRY/REGION, AND SERVICE]
- **SMTP/email provider:** [ENTER PROVIDER AND PROCESSING REGION]
- **Payment provider:** Stripe is integrated for school checkout; confirm the enabled account, data flows, contract and region before launch.
- **Other subprocessors/logging/monitoring:** [LIST ALL THAT APPLY]
- **Cross-border transfers:** [DOCUMENT WHETHER PERSONAL INFORMATION IS TRANSFERRED OUTSIDE SOUTH AFRICA AND THE SAFEGUARDS/LEGAL BASIS]

Do not publish this policy with unresolved placeholders. Check provider agreements and applicable POPIA requirements for operators, security safeguards, and cross-border transfers.

## 7. Retention and deletion — set actual periods before release

- **Active learner accounts:** [DEFINE RETENTION AND SCHOOL-YEAR TRANSITION RULE]
- **Inactive accounts:** [DEFINE REVIEW/DELETION PERIOD AND NOTICE PROCESS]
- **Support/feedback records:** [DEFINE PERIOD]
- **Security/application logs:** [DEFINE PERIOD AND ACCESS CONTROLS]
- **Backups:** [NAME PROVIDER, FREQUENCY, RETENTION WINDOW, AND DELETION BEHAVIOUR]
- **Password-reset tokens:** expire after 30 minutes and are single-use.
- **Email-verification tokens:** expire after 24 hours and are single-use.
- **School licence and payment records:** [DEFINE RETENTION FOR ACCOUNTING, CONTRACTUAL, AND LEGAL NEEDS]

The account deletion feature should be tested against all related tables, logs, exports, shared links, and backup retention. Explain any records that cannot be immediately removed and why. A deletion request is not complete merely because the main user row was deleted.

## 8. Security safeguards

Implemented controls include bcrypt password hashing, hashed time-limited reset/verification tokens, email verification for new public learner and school-admin registrations, and role checks for the administration page. These controls require ongoing testing and do not by themselves guarantee security or POPIA compliance.

Before release, verify at minimum: access control and tenant/class separation; rate limiting and abuse controls; secure secret management; HTTPS; database permissions and backups; incident response; dependency updates; audit/log access; and isolation of learner-submitted Python code. A restricted built-ins list or subprocess alone is not a complete security boundary for arbitrary code execution.

## 9. Data subject requests and complaints

Provide a monitored channel for access, correction, deletion, objection, complaints and other applicable requests. Contact: **[ENTER MONITORED PRIVACY CONTACT]**. Document how identity is verified, how requests are logged, who responds, and applicable statutory deadlines. Do not promise a response period until the operator has approved and can meet it.

## 10. Security incidents

Maintain a written process to triage, contain, investigate, record and remediate suspected incidents. Determine when notification to the Information Regulator and affected data subjects is legally required, and who is authorised to make those notifications. Keep current contact details and an incident log.

## 11. Updates and complaints

This notice should be reviewed when the application, hosting, subprocessors, data categories, or purposes change. Publish the effective date and provide the current version to schools and users. Complaints and regulator contact details must be verified from official sources before publication.

---

## Release sign-off checklist

- [ ] Replace every `[ENTER ...]` / `[DEFINE ...]` placeholder.
- [ ] Have South African privacy counsel or a suitably qualified adviser review the POPIA basis, children's information, school/operator agreements, and cross-border transfers.
- [ ] Confirm actual hosting, email, payment, logging, and backup providers.
- [ ] Test data export, correction, account deletion, and backup expiry.
- [ ] Verify teacher/admin permissions are school-scoped.
- [ ] Complete a documented security review, including the Python execution sandbox.
- [ ] Publish a dated privacy notice and provide a monitored contact channel.
