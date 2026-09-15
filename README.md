# EventFlow AI

EventFlow AI is a Flask event-management platform with MySQL-backed registration, scheduling, venue, speaker, sponsorship, incident, intelligence, and orchestration services.

## Run locally

```powershell
.\venv\Scripts\Activate.ps1
python app.py
```

The application reads `DATABASE_URL` and `SECRET_KEY` from `.env`. The current development configuration uses MySQL through PyMySQL.

## Production deployment

Use a WSGI server instead of Flask's development server:

```powershell
waitress-serve --listen=*:8080 wsgi:app
```

Required environment variables:

```text
DATABASE_URL=mysql+pymysql://user:password@host:3306/eventflow
SECRET_KEY=replace-with-a-long-random-secret
COOKIE_SECURE=1
```

Set `COOKIE_SECURE=1` only when HTTPS is enabled.

## Milestone 4 verification

```powershell
python -m unittest discover -s tests -v
```

Operational endpoints:

- `/health`: database-backed health probe
- `/api/intelligence`: live metrics, risks, and recommendations
- `/api/platform-ops/checks`: executable readiness checks
- `/api/platform-ops/sections`: reliability, security, performance, deployment, and documentation evidence
- `/api/orchestration/runs`: persisted orchestration audit history