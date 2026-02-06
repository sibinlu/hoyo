# Prefect Deployment

This directory contains Prefect workflow deployments for automating HoYoLab check-ins and code redemption.

## Overview

Two automated flows:
- **hoyo-auth-weekly**: Renews authentication every Sunday at 2 AM
- **hoyo-checkin-daily**: Runs check-in and code redemption daily at 10 AM

## Prerequisites

1. **Prefect installed** in your environment:
   ```bash
   pip install prefect
   ```

2. **Prefect server running** with a local work pool:
   ```bash
   prefect server start
   prefect worker start --pool my-local-pool
   ```

3. **Docker setup completed** (see main README.md):
   - Docker image built: `docker-compose build`
   - Environment variables configured in `.env`
   - Session data exists at `/Users/sixomac/SessionData/hoyo_session_data.json`

4. **Authentication completed locally** (one-time):
   ```bash
   cd /Users/sixomac/project/hoyo
   ./bin/hoyo auth
   ```

## Deploying Flows

From the hoyo project root:

```bash
cd /Users/sixomac/project/hoyo
python deploy/prefect_deployment.py
```

This will deploy both flows to your Prefect server.

## Architecture

### hoyo_auth_flow (Weekly - Sunday 2 AM)
- Runs authentication locally (requires browser access)
- Updates session data for the week
- Uses local `./bin/hoyo auth` command

### hoyo_checkin_flow (Daily - 10 AM)
- Checks for valid session data
- Runs check-in and code redemption via Docker
- Uses `docker-compose run --rm hoyo checkin redeem`

## Flow Execution Details

### Authentication Flow
```python
./bin/hoyo auth
```
- Must run locally (not in Docker) because it opens a browser
- Creates/updates session data in `/Users/sixomac/SessionData/`
- Scheduled weekly to prevent session expiration

### Check-in Flow
```python
docker-compose run --rm hoyo checkin redeem
```
- Runs in Docker container for isolation
- Uses existing session data (mounted as volume)
- Outputs logs visible in Prefect UI

## Monitoring

View deployments and runs:
```bash
prefect deployment ls
prefect flow-run ls --limit 10
```

Or visit the Prefect UI:
```
http://127.0.0.1:4200
```

## Troubleshooting

### Session expired error
Run authentication manually:
```bash
cd /Users/sixomac/project/hoyo
./bin/hoyo auth
```

### Docker command fails
Verify Docker setup:
```bash
cd /Users/sixomac/project/hoyo
docker-compose run --rm hoyo checkin redeem
```

### Missing session file
Check that session data exists:
```bash
ls /Users/sixomac/SessionData/hoyo_session_data.json
```

### Deployment not found
Redeploy the flows:
```bash
python deploy/prefect_deployment.py
```

## Environment Variables

Docker container uses `.env` file (see `.env.example`):
```bash
HOYO_USER=your_email@example.com
HOYO_PASSWORD=your_password
SESSION_PATH=/app/SessionData  # Container path, not host path
```

## Schedule Customization

To change schedules, edit [prefect_deployment.py](prefect_deployment.py):

```python
# Auth flow schedule (Cron format)
schedule=Cron("0 2 * * 0", timezone="America/Los_Angeles")  # Sunday 2 AM

# Checkin flow schedule
schedule=Cron("0 10 * * *", timezone="America/Los_Angeles")  # Daily 10 AM
```

Then redeploy:
```bash
python deploy/prefect_deployment.py
```

## File Structure

```
/Users/sixomac/project/hoyo/
├── deploy/
│   ├── prefect_deployment.py    # Deployment configuration
│   └── README.md                # This file
├── bin/hoyo                     # CLI wrapper
├── main.py                      # Application entry point
├── docker-compose.yml           # Docker orchestration
├── .env                         # Environment variables (gitignored)
└── README.md                    # Main project documentation
```

## Related Documentation

- Main project README: [../README.md](../README.md)
- Docker setup: [../README.md#docker-usage](../README.md#docker-usage)
- Prefect docs: https://docs.prefect.io
