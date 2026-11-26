# TravelMadi — Journey Beyond Destiny
Academic full-stack travel reservation demo. Flask serves the frontend and REST API on the same origin. PostgreSQL is the intended deployment database; SQLite is an optional local fallback.

## Windows local setup (PowerShell)
Install Python 3.11+ and PostgreSQL. In pgAdmin create a database named travelmadi. Open PowerShell in this project folder:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:DATABASE_URL='postgresql+psycopg://postgres:YOUR_PASSWORD@localhost:5432/travelmadi'
$env:SECRET_KEY=(& .\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_hex(32))")
$env:ADMIN_EMAIL='admin@example.com'
$env:ADMIN_PASSWORD='REPLACE_WITH_A_STRONG_PASSWORD'
.\.venv\Scripts\python.exe app.py
```
Open http://127.0.0.1:5000. To try without PostgreSQL, omit DATABASE_URL. Keep the same SECRET_KEY across restarts. Admin is created only if email is unused; use a fresh admin email. Register a separate customer through the UI.

## Deployment
Upload the project files (not the zip) to a GitHub repository. Do not commit secrets or the local database. Create a PostgreSQL database and a Python web service on a host such as Render, connected to that repository. Set DATABASE_URL to the provider's database URL, SECRET_KEY to a strong random value, ADMIN_EMAIL and ADMIN_PASSWORD to your chosen credentials, COOKIE_SECURE=1 for HTTPS. Build command: `pip install -r requirements.txt`. Start command: `flask --app app init-db && gunicorn app:app`. Open the web service URL. Hosting availability and cost depend on provider. GitHub Pages cannot execute Flask; the web service hosts both frontend and backend.

## Signature Edition
Emerald and champagne sidebar design, destination photography and database-backed saved journeys. GET /api/wishlist lists saved services; POST /api/wishlist/<id> toggles a saved service.

## API
GET /api/session returns session and CSRF token. Send X-CSRF-Token with every mutation; login rotates it. POST /api/register, /api/login, /api/logout. GET /api/services, /api/availability?id=...&date=YYYY-MM-DD. GET/POST /api/bookings; POST /api/bookings/<id>/cancel. GET /api/admin, POST /api/admin/services, PATCH /api/admin/services/<id> (price, active). All booking prices and capacity are checked on the server. Admin endpoints require admin role.

## Demo walkthrough
Register, log in, choose a service and future date, check availability, reserve, download text ticket, cancel. Sign out and log in as admin to view users, reservations, revenue, add inventory or change price/active status. Try a booking exceeding capacity or accessing admin as a customer.

## Scope
Seeded travel inventory, daily capacity per service, lead passenger, simulated payments/refunds. No live travel provider, actual payment, assigned seat numbers, round-trip workflow, email verification, password reset or production-grade rate limiting. Images use external URLs. No real personal or payment information should be entered. For production add migrations, monitoring, rate limits and security review.

## Trending destinations update
Six photo cards with account-backed destination favourites and hotel search links. Run database initialization again when upgrading an existing deployment. Images use external Unsplash URLs; internet access is required. Hotel inventory is demonstration data.

## Live pricing deployment
Upload the contents of this folder (not the ZIP) to GitHub. On Render create a Python Web Service, free instance, Singapore region. Build: `pip install -r requirements.txt`. Start: `flask --app app init-db && gunicorn --workers 1 --timeout 90 app:app`. Set DATABASE_URL to Neon URI, SERPAPI_KEY to private key, SECRET_KEY to a random secret, COOKIE_SECURE=1, ADMIN_EMAIL and ADMIN_PASSWORD (at least 10 characters). Alternatively use render.yaml as a Blueprint. Never commit credentials. Sign in, use Live journey planner with airport codes (BLR, GOI) and hotel city. Each search makes two provider requests; avoid repeated searches. Live results are provider quotes, not guaranteed fares; hotel nightly fallback is an estimate. Other modules use sample inventory. All bookings and invoices are demo only. No live API or PostgreSQL integration test was performed. Profile displays name/email and payment history; live trips are separate from legacy admin analytics. 
