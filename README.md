# EventFlow AI

EventFlow AI is an intelligent event-management platform designed to bring the full event lifecycle into one operational workspace. It combines registration, attendance, scheduling, venues, speakers, sponsorships, incidents, analytics, and AI-assisted recommendations in a Flask web application backed by SQLAlchemy and MySQL.

The platform is designed for event teams that need more than a collection of forms. It turns live event data into operational dashboards, highlights risks, recommends next actions, and gives coordinators a shared view of what is happening before and during an event.

## Project overview

EventFlow AI follows an incremental eight-week product roadmap. Each phase adds a focused dashboard while building toward a unified event intelligence command center.

### Weeks 1-2: Registration Intelligence Dashboard

- Register and manage attendees
- Import attendee records from CSV files
- Search, edit, delete, and export registration data
- Track check-ins and attendance activity
- View registration analytics and attendee trends
- Generate QR codes for event check-in workflows

### Weeks 3-4: Venue & Speaker Operations Dashboard

- Manage venues, capacities, facilities, and availability
- Create and manage sessions and schedules
- Maintain speaker profiles and assignments
- Recommend suitable venues and speakers using event data
- Surface scheduling and capacity considerations for operations teams

### Weeks 5-6: Sponsorship & Incident Management Dashboard

- Manage sponsors, sponsorship packages, and commercial value
- Track sponsor deliverables and completion status
- Analyze sponsor performance and delivery risk
- Record, prioritize, and monitor operational incidents
- Support incident analysis and escalation-oriented workflows

### Weeks 7-8: Event Intelligence Command Center

- Combine registration, scheduling, venue, speaker, sponsorship, and incident signals
- Produce live event metrics, risks, alerts, and recommendations
- Coordinate specialized agents through a central orchestration layer
- Provide platform readiness, reliability, security, performance, and deployment checks
- Preserve orchestration runs as an auditable operational history

## Key capabilities

### Operational dashboards

Event teams can move from day-to-day record management to high-level decision-making through dedicated views for attendees, analytics, sessions, speakers, venues, sponsors, incidents, platform operations, and executive intelligence.

### AI-assisted event operations

The intelligence layer aggregates current event data and produces actionable insights. Specialized services support analytics, registration, scheduling, speaker, venue, sponsorship, and platform operations workflows.

### Live monitoring and APIs

The application exposes JSON endpoints for health checks, live dashboard updates, intelligence snapshots, platform checks, and orchestration history. These endpoints can support monitoring tools or a future front-end client.

### Security and deployment readiness

The application adds security response headers, uses environment-based configuration, provides a database-backed health probe, and supports deployment through a WSGI server.

## Technology stack

- **Backend:** Python, Flask, Flask-SQLAlchemy
- **Database:** MySQL with PyMySQL, or another SQLAlchemy-compatible database URL
- **Data and analytics:** Pandas, NumPy, SciPy, scikit-learn, Matplotlib
- **Frontend:** Jinja templates, HTML, CSS, and JavaScript
- **Utilities:** CSV import/export, QR code generation, dotenv configuration
- **Production server:** Waitress through the WSGI entry point

## Project structure

```text
EventFlow-AI/
├── app.py                    # Flask routes and application workflows
├── config.py                 # Environment-based application configuration
├── models.py                 # SQLAlchemy data models
├── wsgi.py                   # Production WSGI entry point
├── services/                 # Analytics, intelligence, and domain agents
├── templates/                # Jinja dashboard and workflow pages
├── static/                   # CSS, JavaScript, and generated QR assets
├── utils/                    # Shared AI and QR helpers
├── tests/                    # Automated verification
├── requirements.txt          # Python dependencies
└── sample_attendees.csv      # Example import data
```

## Run locally

### 1. Create and activate a virtual environment

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
python -m pip install -r requirements.txt
python -m pip install waitress
```

### 3. Configure environment variables

Create a local `.env` file. Do not commit it to GitHub.

```text
DATABASE_URL=mysql+pymysql://user:password@host:3306/eventflow
SECRET_KEY=replace-with-a-long-random-secret
COOKIE_SECURE=0
```

Use `COOKIE_SECURE=1` only when the application is served over HTTPS. Make sure the configured database exists and that the database user has the required permissions.

### 4. Start the application

```powershell
python app.py
```

Open `http://127.0.0.1:5000` in a browser.

## Production deployment

Run the application through Waitress instead of Flask's development server:

```powershell
waitress-serve --listen=*:8080 wsgi:app
```

For production, use a strong secret key, keep credentials outside source control, enable HTTPS, and set `COOKIE_SECURE=1`.

## Verification

Run the automated test suite with Python's built-in unittest runner:

```powershell
python -m unittest discover -s tests -v
```

Useful operational endpoints:

- `/health` - database-backed health probe
- `/api/live` - current intelligence snapshot and active alerts
- `/api/intelligence` - live metrics, risks, and recommendations
- `/api/platform-ops/checks` - executable readiness checks
- `/api/platform-ops/sections` - reliability, security, performance, deployment, and documentation evidence
- `/api/orchestration/runs` - persisted orchestration audit history

## Security note

Configuration files containing passwords, API keys, database credentials, or secret keys must remain local. The repository includes a `.gitignore` for `.env`, virtual environments, generated databases, bytecode, and other runtime artifacts. If a credential has ever been committed, rotate it even after removing the file from the latest commit.

## Roadmap direction

The long-term goal is to make EventFlow AI a dependable command center for event teams: one place to understand event health, identify emerging risks, coordinate operational work, and act on recommendations backed by current data.