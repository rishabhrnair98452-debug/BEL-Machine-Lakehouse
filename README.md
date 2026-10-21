BEL Machine Health Monitoring Dashboard — Updated Project
=========================================================

Includes:
- Role-aware login: Admin, Maintenance Engineer, Operator, Viewer
- Admin-only user management in Settings
- Per-machine report with date filtering, sensor average/min/max, flagged readings and CSV download
- Existing dashboard and sample Bronze/Silver/Gold CSV layers

SECURITY NOTES
- Login category is a consistency check only. The database role is authoritative.
- Admin account creation is performed using create_admin.py; do not add a public sign-up page.
- Do not share .env or users.db.
- Demo thresholds (temperature > 80, vibration > 7, pressure outside 4–7) are illustrative only and are not approved machinery safety limits.

SETUP (Windows PowerShell)
1. Open this project folder in VS Code.
2. Create/activate a fresh virtual environment if needed:
   py -3.12 -m venv venv
   .\venv\Scripts\Activate.ps1
3. Install packages:
   python -m pip install -r requirements.txt
4. Create a .env file in the project root with a private random key:
   BEL_SECRET_KEY=replace_with_a_long_random_secret
   Generate a key with:
   python -c "import secrets; print(secrets.token_hex(32))"
   Copy the generated value after BEL_SECRET_KEY=. Keep this file private.
5. Create an administrator account (first run only):
   python create_admin.py
   Use a password of at least 12 characters.
6. Start the app:
   python app.py
7. Open http://127.0.0.1:5000

If you already have a users.db from your current project, keep it in the project root. The Viewer role is supported by this version; if you need to add a Viewer account, sign in as Admin and use Settings.

Important: the ZIP intentionally excludes .env and users.db. Copy your existing users.db into the project root if you want to preserve existing accounts.
