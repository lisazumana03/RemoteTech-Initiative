# RemoteTech

RemoteTech is a Streamlit learning application for Python quests, learner progress, and school-level administration.

## Requirements

- Python 3.11 or another Python version supported by the pinned dependencies in `requirements.txt`.
- SQLite for local development, or PostgreSQL for hosted deployments.
- SMTP credentials only if you want password recovery emails and progress-sharing emails.

## Local setup (Windows PowerShell)

1. Open this project folder in a terminal.
2. Create a virtual environment:
   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
3. Install dependencies:
   ```powershell
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env` and configure the values you need. Never commit `.env`.
5. Create an initial administrator account:
   ```powershell
   python seed_admin.py
   ```
   The one-time seed script creates an administrator account for initial setup. Use a real, controlled administrator email address.
6. Start the app:
   ```powershell
   streamlit run main.py
   ```

## Account registration and password recovery

Learner and school-admin accounts can log in immediately after successful registration; email verification is not part of the account activation flow. SMTP remains optional and is used only for password-reset and progress-sharing emails. Password reset links expire after 30 minutes and are single-use.

## Database

Without `DATABASE_URL`, the app uses `SQLITE_PATH` (default `remotetech.db`). For PostgreSQL, set `DATABASE_URL` to a private connection string supplied by your database host. Back up the database before upgrades and test restoration regularly.

## Security and privacy notes

- Never commit passwords, API keys, SMTP credentials, `.env` files, local databases, or real learner data.
- Do not use SQLite/local mode as a production deployment plan for a multi-school service without a deliberate operational review.
- Do not expose student-submitted code execution to the public until the sandbox has undergone a security review in the intended hosting environment.
- Review `DATA_POLICY.md` and complete every deployment-specific item before sharing the policy with schools. This document is operational guidance, not legal advice or a claim of POPIA compliance.

## Tests

Run syntax checks with:
```powershell
python -m compileall -q .
```

Run the automated tests with:
```powershell
pytest
```
