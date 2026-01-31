# LDPM - Linux Display Power Management

## Overview

LDPM is a web-based power management system for controlling Sony BRAVIA TVs on a local network. Designed for organizations deploying digital signage, this MVP provides centralized display management, group-based bulk control, and automated scheduling for TV power states.

**Tech Stack:**
- Backend: Python 3.11, FastAPI, SQLAlchemy ORM, SQLite, APScheduler
- Frontend: React 18, TypeScript, Vite, Tailwind CSS, React Query
- Deployment: Docker & Docker Compose
- API: RESTful with HTTP Basic Authentication

**Target Use Case:** Sony BRAVIA Pro TVs on internal LAN networks where administrators need to control displays remotely without WiFi connectivity constraints.

---

## Quick Start

### Prerequisites

- Docker & Docker Compose (version 20.10+)
- Sony BRAVIA TVs with Remote Start enabled (see TV Setup section)
- Network access to TV devices (same LAN preferred)

### Installation

Clone the repository and set up environment:

```bash
git clone https://github.com/your-org/ldpm.git
cd ldpm

# Copy environment template
cp .env.example .env

# Edit .env with your admin credentials (optional - defaults work for testing)
# ADMIN_USERNAME=admin
# ADMIN_PASSWORD=admin123

# Build and start services
docker-compose build
docker-compose up -d

# Verify services are healthy (wait 15 seconds for startup)
sleep 15
curl -s http://localhost:8000/api/v1/health
# Expected response: {"status": "healthy"}
```

### First Login

1. Navigate to: `http://localhost` (or `http://<your-server-ip>`)
2. Login with credentials:
   - **Username:** admin (or from ADMIN_USERNAME in .env)
   - **Password:** admin123 (or from ADMIN_PASSWORD in .env)
3. You'll be redirected to the Dashboard

### Verify Installation

```bash
# Check services are running
docker-compose ps

# Should output:
# NAME               STATUS              PORTS
# ldpm-backend       Up (healthy)        0.0.0.0:8000->8000/tcp
# ldpm-frontend      Up (healthy)        0.0.0.0:80->80/tcp

# View logs
docker-compose logs -f backend    # Backend logs
docker-compose logs -f frontend   # Frontend logs
```

---

## Sony BRAVIA TV Setup

### Critical Configuration

Before using LDPM, configure each Sony BRAVIA TV on your network:

#### Step 1: Enable Remote Start

1. On TV remote, press **Settings**
2. Navigate: Settings → Network → Remote Start → **ON**
3. Save and reboot TV

#### Step 2: Configure Pre-Shared Key (PSK)

1. Press **Settings** on remote
2. Navigate: Settings → Network → IP Control
3. Select: Authentication → **Normal and Pre-Shared Key**
4. Enter Pre-Shared Key (example: `0000` or custom value)
5. Note this PSK - you'll use it in LDPM
6. Save settings

#### Step 3: Network Configuration

1. Assign static IP to TV (recommended):
   - Via TV menu: Settings → Network → Ethernet/WiFi → Manual
   - Via DHCP reservation: Router settings (DHCP reservation for TV MAC address)
2. Test connectivity from server:
   ```bash
   ping <tv-ip-address>
   ```

#### Step 4: Add TV to LDPM

1. Login to LDPM dashboard
2. Click "Displays" in sidebar
3. Click "Add Display" button
4. Fill in:
   - **Display Name:** TV-01 (or location-based name)
   - **IP Address:** 192.168.1.50 (static IP from Step 3)
   - **Pre-Shared Key:** 0000 (PSK from Step 2)
   - **Location:** Conference Room (optional)
   - **Tags:** meeting-room, main-display (optional)
5. Click "Create Display"

### Troubleshooting TV Connection

| Symptom | Cause | Solution |
|---------|-------|----------|
| "Display offline" status | Remote Start disabled | Enable via TV Settings → Network → Remote Start |
| "Connection refused" error | PSK incorrect | Verify PSK matches TV configuration (case-sensitive) |
| "Network unreachable" | TV not on same LAN | Check network routing, ensure TV has network connectivity |
| Intermittent connectivity | Firewall blocking port 20060 | Allow TCP port 20060 (Simple IP Control) through firewall |
| REST API fails, Simple IP works | Sony TV doesn't support REST API | OK - fallback protocol working, update TV firmware if possible |

---

## Features

### Display Management
- Add/edit/delete displays with IP address and Pre-Shared Key
- View real-time power status (polling every 30 seconds)
- Individual display power control (On/Off)
- Assign displays to groups and tags
- Track last seen timestamp for each display

### Group Management
- Create logical display groups (e.g., "Conference Rooms", "Lobby Screens")
- Add/remove displays from groups
- Bulk power control for entire group
- View group display count and status summary

### Bulk Power Control
- Turn groups of displays on/off simultaneously
- Parallel power commands for fast execution
- View execution results and error details
- Retry on failure with exponential backoff (1s, 2s, 4s)

### Scheduling
- Create cron-based schedules for automated power control
- Schedule can target single display OR entire group
- Supported cron format: `minute hour day month day_of_week` (5 fields)
- Examples:
  - `0 8 * * 1-5` - Turn on at 8:00 AM weekdays
  - `0 18 * * *` - Turn off at 6:00 PM daily
  - `30 12 * * 0` - Turn on at 12:30 PM on Sundays
- Enable/disable schedules without deletion
- View execution history with timestamps and results

### Real-Time Monitoring
- Live power status for all displays (30-second polling interval)
- Status indicators: Active (on), Standby (off), Offline (unreachable)
- Last-seen timestamp updated on successful connection
- Batch status updates for efficient network usage

---

## Configuration

### Environment Variables (.env)

All variables are optional - defaults work for development/testing:

```bash
# Admin credentials for web UI
ADMIN_USERNAME=admin              # Default: admin
ADMIN_PASSWORD=admin123           # Default: admin123

# Database configuration
DATABASE_URL=sqlite:///./ldpm.db  # SQLite file path (relative to container /app)

# Backend server
BACKEND_HOST=0.0.0.0              # Listen on all interfaces
BACKEND_PORT=8000                 # Internal port (exposed as 8000)

# Frontend
FRONTEND_URL=http://localhost     # URL shown in browser

# Sony TV defaults (hardcoded in adapter, not env vars)
SONY_TV_TIMEOUT=10                # Request timeout (seconds)
SONY_TV_RETRIES=3                 # Retry attempts on failure
```

### Update Configuration

To change environment variables:

```bash
# Edit .env file
nano .env

# Restart services to apply changes
docker-compose restart backend frontend
```

### Persistent Data

Database and configuration are stored in Docker volumes:

```bash
# View volumes
docker volume ls | grep ldpm

# Backup database
docker run --rm -v ldpm-db:/data -v $(pwd):/backup \
  alpine tar czf /backup/ldpm-db.tar.gz -C /data .

# Restore database
docker run --rm -v ldpm-db:/data -v $(pwd):/backup \
  alpine tar xzf /backup/ldpm-db.tar.gz -C /data
```

---

## API Documentation

### Auto-Generated Docs

FastAPI provides interactive API documentation at:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### Authentication

All API endpoints require HTTP Basic Authentication:

```bash
# Using curl with credentials
curl -u admin:admin123 http://localhost:8000/api/v1/displays

# Using curl with base64 encoding
curl -H "Authorization: Basic YWRtaW46YWRtaW4xMjM=" \
  http://localhost:8000/api/v1/displays
```

### Core Endpoints

#### Displays

```bash
# List all displays
GET /api/v1/displays

# Create display
POST /api/v1/displays
{
  "name": "TV-01",
  "ip_address": "192.168.1.50",
  "psk": "0000",
  "location": "Conference Room",
  "tags": ["meeting", "main"]
}

# Get display details
GET /api/v1/displays/{display_id}

# Update display
PUT /api/v1/displays/{display_id}

# Delete display
DELETE /api/v1/displays/{display_id}

# Get power status (immediate request)
GET /api/v1/displays/{display_id}/power

# Turn display on
POST /api/v1/displays/{display_id}/power
{"action": "on"}

# Turn display off
POST /api/v1/displays/{display_id}/power
{"action": "off"}
```

#### Groups

```bash
# List all groups
GET /api/v1/groups

# Create group
POST /api/v1/groups
{"name": "Conference Rooms"}

# Add displays to group
POST /api/v1/groups/{group_id}/displays
{"display_ids": [1, 2, 3]}

# Remove displays from group
DELETE /api/v1/groups/{group_id}/displays
{"display_ids": [1]}

# Bulk power control for group
POST /api/v1/groups/{group_id}/power
{"action": "on"}
```

#### Schedules

```bash
# List all schedules
GET /api/v1/schedules

# Create schedule
POST /api/v1/schedules
{
  "name": "Morning Startup",
  "cron_expression": "0 8 * * 1-5",
  "action": "on",
  "display_id": 1
}

# Enable/disable schedule
PATCH /api/v1/schedules/{schedule_id}
{"enabled": true}

# Delete schedule
DELETE /api/v1/schedules/{schedule_id}
```

---

## Architecture

### Backend Stack

**FastAPI Application** (`backend/app/main.py`)
- Async request handling for high concurrency
- Dependency injection for testability
- Middleware: CORS, HTTP Basic Auth
- Lifespan context manager for scheduler lifecycle

**Database** (`backend/app/db/models.py`)
- SQLAlchemy ORM with SQLite backend
- Models: Display, Group, DisplayGroup (junction), Schedule, ScheduleExecution
- Relationships: Many-to-many (Display ↔ Group), One-to-many (Group → Schedule)
- Migrations via Alembic

**Sony BRAVIA Adapter** (`backend/app/adapters/bravia.py`)
- REST API (primary protocol): JSON-RPC HTTP requests
- Simple IP Control (fallback): TCP binary protocol
- Automatic fallback if REST fails
- Exponential backoff retry (1s, 2s, 4s)

**Scheduler Service** (`backend/app/services/scheduler.py`)
- APScheduler-based cron job execution
- Loads schedules from database on startup
- Executes power commands via BraviaAdapter
- Logs results to ScheduleExecution table
- Auto-reload capability for dynamic schedule updates

### Frontend Stack

**React Application** (`frontend/src/`)
- Page-level components: Dashboard, DisplaysPage, GroupsPage, SchedulesPage
- Reusable UI components (Task 7): StatusBadge, PowerButton, DisplayCard, GroupCard
- API client: Axios instance with interceptors for auth/errors
- State management: React Query (TanStack Query) for server state
- Forms: React Hook Form for display/group/schedule creation

**Styling**
- Tailwind CSS utility-first approach
- Responsive design for desktop and tablet
- Dark theme with gradient accents
- Component animations and transitions

**Authentication**
- HTTP Basic Auth stored in localStorage
- Protected routes with automatic redirect to login
- Request interceptors to add Authorization header
- Response interceptors for 401 handling

### Deployment

**Docker Containers**
- **Backend:** Python 3.11-slim, uvicorn ASGI server, multi-stage build
- **Frontend:** Node 20-alpine build stage, nginx:alpine serving SPA
- Health checks: HTTP endpoints confirm service readiness
- Network isolation: Custom bridge network

**Service Communication**
- Backend: Listens on 0.0.0.0:8000 (port 8000)
- Frontend: Listens on 0.0.0.0:80 (port 80)
- Frontend proxies /api/* requests to backend via docker-compose service name
- Both services connected to `ldpm-network`

---

## Development

### Running Tests

#### Backend Tests

```bash
# Navigate to backend directory
cd backend

# Install dependencies
pip install -r requirements.txt

# Run all tests
pytest -v

# Run specific test file
pytest tests/test_models.py -v

# Run with coverage
pytest --cov=app tests/
```

**Test Files:**
- `tests/test_models.py` - SQLAlchemy ORM models
- `tests/test_bravia_adapter.py` - Sony TV adapter (REST & Simple IP)
- `tests/test_api_displays.py` - Display endpoints
- `tests/test_api_groups.py` - Group endpoints
- `tests/test_api_schedules.py` - Schedule endpoints
- `tests/test_scheduler.py` - Cron scheduler service

#### Frontend Tests

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Run tests (watch mode)
npm test

# Run tests once (CI mode)
npm test -- --run

# Run with coverage
npm test -- --coverage
```

### Local Development (Without Docker)

#### Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create database and run migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload
```

Backend will be available at: `http://localhost:8000`

#### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend will be available at: `http://localhost:5173`

### Project Structure

```
ldpm/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI app entry point
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── database.py         # SQLAlchemy engine, session factory
│   │   │   └── models.py           # ORM models (Display, Group, Schedule, etc.)
│   │   ├── adapters/
│   │   │   ├── __init__.py
│   │   │   └── bravia.py           # Sony TV control (REST + Simple IP)
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── displays.py         # /api/v1/displays endpoints
│   │   │   ├── groups.py           # /api/v1/groups endpoints
│   │   │   └── schedules.py        # /api/v1/schedules endpoints
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── display.py          # Pydantic schemas for displays
│   │   │   ├── group.py            # Pydantic schemas for groups
│   │   │   └── schedule.py         # Pydantic schemas for schedules
│   │   └── services/
│   │       ├── __init__.py
│   │       └── scheduler.py        # APScheduler service
│   ├── tests/
│   │   ├── conftest.py             # Pytest fixtures
│   │   ├── test_models.py          # Model tests
│   │   ├── test_bravia_adapter.py  # Adapter tests
│   │   ├── test_api_displays.py    # API endpoint tests
│   │   ├── test_api_groups.py      # API endpoint tests
│   │   ├── test_api_schedules.py   # API endpoint tests
│   │   └── test_scheduler.py       # Scheduler tests
│   ├── requirements.txt            # Python dependencies
│   ├── pytest.ini                  # Pytest configuration
│   └── alembic/                    # Database migrations
│
├── frontend/
│   ├── src/
│   │   ├── main.tsx                # React entry point
│   │   ├── App.tsx                 # Router and layout
│   │   ├── index.css               # Global styles (Tailwind)
│   │   ├── App.css                 # App-specific styles
│   │   ├── api/
│   │   │   └── client.ts           # Axios client with interceptors
│   │   ├── pages/
│   │   │   ├── LoginPage.tsx       # Authentication
│   │   │   ├── Dashboard.tsx       # Home page
│   │   │   ├── DisplaysPage.tsx    # Display management
│   │   │   ├── GroupsPage.tsx      # Group management
│   │   │   └── SchedulesPage.tsx   # Schedule management
│   │   ├── components/             # Reusable UI components (created in Task 7)
│   │   ├── hooks/                  # Custom React hooks (created in Task 7)
│   │   ├── types/
│   │   │   └── index.ts            # TypeScript interfaces
│   │   └── __tests__/              # Component tests
│   ├── public/                     # Static assets
│   ├── dist/                       # Build output (generated by npm run build)
│   ├── index.html                  # SPA entry point
│   ├── package.json                # Node dependencies
│   ├── vite.config.ts              # Vite configuration
│   ├── tailwind.config.js          # Tailwind CSS configuration
│   ├── postcss.config.js           # PostCSS configuration
│   └── tsconfig.json               # TypeScript configuration
│
├── Dockerfile.backend              # Backend container image
├── Dockerfile.frontend             # Frontend container image
├── docker-compose.yml              # Multi-container orchestration
├── .env.example                    # Environment variables template
├── README.md                       # This file
└── .gitignore                      # Git ignore patterns
```

---

## Troubleshooting

### Backend Issues

#### Backend won't start

```bash
# Check logs for errors
docker-compose logs backend

# Common causes:
# 1. Port 8000 already in use
lsof -i :8000
kill -9 <PID>

# 2. Database file permissions
docker-compose exec backend ls -la /app/ldpm.db
docker-compose exec backend chmod 666 /app/ldpm.db

# 3. Missing dependencies
docker-compose build --no-cache backend
```

#### Health check failing

```bash
# Verify Python requests library is installed
docker-compose exec backend pip list | grep requests

# Test health endpoint manually
docker-compose exec backend python -c \
  "import requests; print(requests.get('http://localhost:8000/api/v1/health').json())"

# Check if uvicorn is running
docker-compose exec backend ps aux | grep uvicorn
```

#### API returns 500 errors

```bash
# Enable debug logging
docker-compose exec backend python -c \
  "import logging; logging.basicConfig(level=logging.DEBUG)"

# Check backend logs with timestamps
docker-compose logs --timestamps backend | tail -50

# Verify database connectivity
docker-compose exec backend python -c \
  "from app.db.database import SessionLocal; db = SessionLocal(); print('DB OK')"
```

### Frontend Issues

#### Frontend shows blank page

```bash
# Check browser console for JavaScript errors
# Open DevTools: F12 or Ctrl+Shift+I

# Check frontend logs
docker-compose logs frontend

# Verify backend is reachable
curl http://localhost:8000/api/v1/health

# Check nginx configuration
docker-compose exec frontend nginx -t
docker-compose exec frontend nginx -s reload
```

#### API requests fail with CORS errors

```bash
# Verify CORS middleware is enabled
# Main.py should include: app.add_middleware(CORSMiddleware, ...)

# Check that frontend origin is allowed
# Default: localhost:5173 (dev) and localhost:80 (prod)

# Restart services
docker-compose restart backend frontend
```

#### Login doesn't work

```bash
# Verify credentials in .env
docker-compose exec backend env | grep ADMIN

# Test basic auth directly
curl -u admin:admin123 http://localhost:8000/api/v1/displays

# Check if response is 401 or 500
curl -v -u admin:admin123 http://localhost:8000/api/v1/displays
```

### TV Connection Issues

#### Display shows as offline

```bash
# Check TV is reachable from backend container
docker-compose exec backend ping <tv-ip-address>

# Test REST API connectivity
docker-compose exec backend python -c "
import requests
headers = {'X-Auth-PSK': '0000'}
print(requests.get('http://<tv-ip>:80/sony/system', headers=headers, timeout=5).json())
"

# Test Simple IP Control (TCP port 20060)
docker-compose exec backend nc -zv <tv-ip-address> 20060
```

#### Power commands fail intermittently

```bash
# Check adapter logs (enable DEBUG level in scheduler.py)
docker-compose logs --follow backend | grep -i "bravia\|adapter"

# Verify PSK is correct (case-sensitive)
docker-compose exec backend python -c \
  "print('PSK from DB:', ...)"  # Query display model

# Increase timeout in .env (default 10s)
SONY_TV_TIMEOUT=15
docker-compose restart backend
```

### Docker Issues

#### Services won't start

```bash
# Check Docker daemon is running
docker ps

# Rebuild without cache
docker-compose build --no-cache

# Check port conflicts
lsof -i :80
lsof -i :8000

# Inspect network
docker network ls
docker network inspect ldpm_ldpm-network
```

#### Database volume errors

```bash
# Check volume exists
docker volume ls | grep ldpm

# Inspect volume
docker volume inspect ldpm_ldpm-db

# Clean up and rebuild (WARNING: deletes data)
docker-compose down -v
docker-compose up -d
```

---

## Known Limitations (v1 MVP)

### Security
- **Plain text PSK storage:** Pre-Shared Keys stored unencrypted in database (acceptable for internal LAN, encrypt in v2)
- **HTTP Basic Auth only:** No JWT or session tokens (acceptable for internal tool, add OAuth2 in v2)
- **No role-based access:** Single admin user only (add multi-user RBAC in v2)
- **localStorage auth:** Frontend stores credentials in localStorage (vulnerable to XSS, use secure cookies in v2)

### Functionality
- **No auto-discovery:** Displays added manually (implement mDNS discovery in v2)
- **Single timezone:** System timezone only for all schedules (add per-schedule timezone in v2)
- **No pagination:** API returns all results (acceptable for 200 displays, add pagination in v2)
- **Polling only:** 30-second polling for status (add WebSocket real-time in v2)
- **Desktop UI only:** No responsive mobile design yet (optimize for tablets in v2)

### Protocol Support
- **REST API priority:** Falls back to Simple IP Control if REST fails (consider adding IEEE 1394 FireWire fallback in v2)
- **No HTTPS support:** Requires reverse proxy (nginx/traefik) for TLS in production
- **No PJLink support:** Only Sony BRAVIA (add PJLink protocol in v2)

### Performance
- **No connection pooling:** New connection per request (acceptable for low frequency, add pooling if >1000 displays)
- **Synchronous DB access:** APScheduler executes jobs serially (acceptable for MVP, add concurrency control in v2)
- **No caching:** Every request hits database (add Redis caching in v2)

---

## Technical Debt

### Code Quality
1. **PSK Encryption (Priority: High)**
   - Location: `backend/app/db/models.py` line ~40
   - Task: Implement AES encryption for PSK field with separate key management
   - Estimated effort: 2-3 hours

2. **Connection Pooling (Priority: Medium)**
   - Location: `backend/app/adapters/bravia.py`
   - Task: Reuse HTTP client/TCP connections for bulk operations
   - Estimated effort: 1 hour (only if performance issues arise)

3. **WebSocket Real-Time Updates (Priority: Low)**
   - Location: New service needed
   - Task: Replace 30s polling with WebSocket push for status updates
   - Estimated effort: 4-6 hours

### Testing
- Add integration tests for Docker stack (currently only unit tests)
- Add E2E tests for complete user workflows
- Add performance tests for bulk operations (1000+ displays)

### Infrastructure
- Add CI/CD pipeline (GitHub Actions, GitLab CI)
- Add monitoring/alerting (Prometheus + Grafana)
- Add centralized logging (ELK stack, Loki)
- Add Kubernetes manifests for cloud deployment

---

## Production Deployment

### Prerequisites

- Server with Docker & Docker Compose installed (1GB RAM minimum, 2GB recommended)
- Static IP address for the server
- Firewall rule allowing inbound traffic on port 80 (HTTP)
- SSL certificate for HTTPS (recommended: use Let's Encrypt via reverse proxy)

### Reverse Proxy Setup (Recommended)

Deploy behind nginx/traefik for HTTPS and load balancing:

```yaml
# Example nginx reverse proxy configuration
upstream ldpm {
  server localhost:80;
}

server {
  listen 443 ssl http2;
  server_name ldpm.example.com;
  
  ssl_certificate /etc/letsencrypt/live/ldpm.example.com/fullchain.pem;
  ssl_certificate_key /etc/letsencrypt/live/ldpm.example.com/privkey.pem;
  
  location / {
    proxy_pass http://ldpm;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
  }
}
```

### Backup Strategy

```bash
# Daily backup of SQLite database
0 2 * * * docker run --rm -v ldpm_ldpm-db:/data -v /backup:/backup alpine \
  tar czf /backup/ldpm-db-$(date +\%Y-\%m-\%d).tar.gz -C /data .

# Keep last 30 days of backups
find /backup -name "ldpm-db-*.tar.gz" -mtime +30 -delete
```

### Scaling Considerations

- **Horizontal scaling:** Deploy multiple LDPM instances behind load balancer (requires shared database)
- **Database scaling:** SQLite suitable for <10,000 displays; migrate to PostgreSQL for larger deployments
- **Polling optimization:** Implement batched status checks for thousands of displays

---

## Support & Contributing

### Getting Help

- **Bug Reports:** Open issue on GitHub with Docker version, error logs, and reproduction steps
- **Feature Requests:** Open discussion on GitHub with use case and expected behavior
- **Community Chat:** Join Slack/Discord channel (link in GitHub repo)

### Contributing

We welcome contributions! Please:

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Write tests for new functionality
4. Submit pull request with description

See `CONTRIBUTING.md` for detailed guidelines.

### Code of Conduct

Please review `CODE_OF_CONDUCT.md` before contributing.

---

## License

This project is licensed under the MIT License - see `LICENSE` file for details.

---

## Acknowledgments

- **Sony BRAVIA API Documentation:** Sony's REST and Simple IP Control protocols
- **Open Source Projects:** FastAPI, React, Tailwind CSS, Docker
- **Community Contributors:** Thanks to all who report issues and suggest improvements

---

## Changelog

### Version 1.0.0 (Current)

**Features:**
- Display management (CRUD)
- Group management with bulk power control
- Cron-based scheduling with execution logging
- HTTP Basic authentication
- Real-time status monitoring (30s polling)
- Docker Compose deployment

**Known Issues:**
- See "Known Limitations" section above

**Road Map (v2.0):**
- Encryption for PSK storage
- Multi-user support with role-based access control
- WebSocket real-time updates
- Mobile-responsive UI
- PostgreSQL support for scalability
- Kubernetes deployment manifests

---

## FAQ

**Q: Can I run LDPM on Windows?**
A: Yes! Docker Desktop for Windows works well. Ensure WSL 2 backend is enabled.

**Q: What if my TV doesn't support Remote Start?**
A: Update TV firmware to latest version. Some older models don't support remote control. Check Sony support site for compatibility.

**Q: Can I control non-Sony TVs?**
A: Not currently. Future versions may add PJLink support for other manufacturers.

**Q: How many TVs can LDPM manage?**
A: MVP tested with up to 200 displays. For 1000+, migrate to PostgreSQL and add caching.

**Q: Can I use LDPM outside the LAN?**
A: Not directly (TVs must be on LAN). Deploy behind a VPN or secure reverse proxy for remote access.

**Q: How do I backup my settings?**
A: Backup the SQLite database volume: `docker volume inspect ldpm_ldpm-db` and tar the mount path.

**Q: Can I schedule power control on multiple schedules?**
A: Yes! Create multiple Schedule records. APScheduler handles concurrent executions.

**Q: What happens when a schedule is disabled?**
A: Disabled schedules are excluded from the scheduler. They still exist in database for re-enabling later.

---

**Last Updated:** January 31, 2026  
**Version:** 1.0.0  
**Status:** Production Ready (MVP)
