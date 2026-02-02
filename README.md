# LudwigOne API

KI-gestützte Dokumentenverarbeitungs-Plattform für automatische Analyse, Kategorisierung und Strukturierung von TAR-Archiven und PDF-Dateien.

## Features

### Flow 1: TAR Archive Processing
- TAR-Archive entpacken
- Dokumente extrahieren (Text/Vision)
- Automatische Kategorisierung
- Intelligente Umbenennung
- Neues strukturiertes Archiv erstellen
- XML-Insight-Report

### Flow 2: PDF Splitting & Merging
- PDFs in Seiten zerlegen
- Seiten extrahieren und kategorisieren
- Intelligentes Zusammenführen verwandter Seiten
- Strukturiertes Output-Archiv
- XML-Insight-Report

## Technology Stack

- **Backend:** Python FastAPI
- **Database:** PostgreSQL 16
- **Orchestration:** Temporal
- **Document Processing:** PyMuPDF, pypdf, python-docx, Pillow
- **LLM:** Mistral API + Ollama Fallback
- **Frontend:** React 18 + TypeScript + ShadCN/ui

## Quick Start

### Prerequisites
- Docker & Docker Compose
- At least 8GB RAM
- 10GB disk space

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd ludwigone
```

2. Create `.env` file from example:
```bash
cp .env.example .env
```

3. Edit `.env` and set required values:
```bash
# Required
POSTGRES_PASSWORD=<secure_password>
SECRET_KEY=<random_secret_key_min_32_chars>
MISTRAL_API_KEY=<your_mistral_api_key>
```

4. Start all services:
```bash
docker-compose up -d
```

5. Verify services are running:
```bash
docker-compose ps
```

### Services & Ports

- **API:** http://localhost:8000
  - Docs: http://localhost:8000/docs
  - Health: http://localhost:8000/health
- **Frontend:** http://localhost:3000
- **Dashboard:** http://localhost:3001
- **Temporal UI:** http://localhost:8080
- **PostgreSQL:** localhost:5432

### Optional: Run with Ollama

```bash
docker-compose --profile ollama up -d
```

Then set in `.env`:
```bash
USE_OLLAMA=true
```

## Architecture

```
User/Admin → Frontend/Dashboard → FastAPI API
                                      ↓
                            Temporal Workflows
                                      ↓
                    ┌─────────────────┼─────────────────┐
                    ↓                 ↓                 ↓
              PostgreSQL         Mistral API       Worker Pool
```

## Development

### Backend Development

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run API locally
python -m app.main

# Run worker locally
python -m app.worker
```

### Database Migrations

```bash
cd backend

# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Run dev server
npm run dev

# Build for production
npm run build
```

## API Documentation

Full API documentation available at: http://localhost:8000/docs

### Key Endpoints

#### User Endpoints
- `POST /api/v1/jobs/tar-upload` - Upload TAR archive
- `POST /api/v1/jobs/pdf-upload` - Upload PDF
- `GET /api/v1/jobs` - List all jobs
- `GET /api/v1/jobs/{id}` - Job status & progress
- `GET /api/v1/jobs/{id}/download` - Download result archive
- `GET /api/v1/jobs/{id}/insight` - Get insight XML

#### Admin Endpoints
- `/api/v1/admin/categories` - Manage categories
- `/api/v1/admin/prompts` - Manage prompt templates
- `/api/v1/admin/config` - System configuration
- `/api/v1/admin/analytics` - Usage analytics

## Configuration

### Environment Variables

See `.env.example` for all available configuration options.

Key settings:
- `MISTRAL_API_KEY` - Mistral API key (required)
- `UPLOAD_MAX_SIZE_MB` - Max upload size (default: 500)
- `MAX_CONCURRENT_VISION_CALLS` - Concurrent Vision API calls (default: 5)
- `VISION_API_MAX_RETRIES` - Max retries for Vision API (default: 5)
- `OUTPUT_RETENTION_DAYS` - Days to keep outputs (default: 7)

### Database Configuration

All runtime configuration stored in `system_config` table.
Editable via Admin Dashboard or API.

### Prompt Templates

LLM prompts customizable via Admin Dashboard.
Templates for:
- Vision extraction
- Categorization (Flow 1 & 2)
- Merge decisions (Flow 2)
- Filename generation
- Insight generation

## Workflows

### TAR Processing Workflow

1. Extract TAR archive
2. Process documents in parallel (max 5)
   - Extract text/images
   - Call Vision API with retry
3. Categorize and rename (parallel)
4. Generate insight report
5. Build output archive
6. Send email notification

### PDF Splitting Workflow

1. Split PDF into pages
2. Process pages in parallel (max 5)
3. Categorize pages (sequential)
4. Merge related pages (sequential comparison)
5. Assign filenames (parallel)
6. Generate insight report
7. Build output archive
8. Send email notification

## Monitoring

### Temporal UI
Access at http://localhost:8080 to:
- View running workflows
- Check workflow history
- Debug failed executions
- Monitor worker health

### API Logs
```bash
docker-compose logs -f api
```

### Worker Logs
```bash
docker-compose logs -f worker
```

### Database Access
```bash
docker-compose exec postgres psql -U ludwigone -d ludwigone
```

## Testing

```bash
cd backend

# Run tests
pytest

# With coverage
pytest --cov=app --cov-report=html

# Integration tests
pytest tests/integration/
```

## Troubleshooting

### Vision API Timeouts
- Check `VISION_API_TIMEOUT_SECONDS` setting
- Reduce `MAX_CONCURRENT_VISION_CALLS`
- Check Temporal UI for retry attempts
- Review `api_call_logs` table

### Database Connection Issues
- Verify PostgreSQL is running: `docker-compose ps postgres`
- Check credentials in `.env`
- Verify network: `docker network ls`

### Worker Not Processing
- Check worker logs: `docker-compose logs worker`
- Verify Temporal connection
- Check task queue in Temporal UI

## Production Deployment

### Security Checklist
- [ ] Change all default passwords
- [ ] Generate secure `SECRET_KEY`
- [ ] Enable HTTPS/TLS
- [ ] Configure firewall rules
- [ ] Set up backup strategy
- [ ] Configure log rotation
- [ ] Review `ALLOWED_ORIGINS`

### Performance Tuning
- Increase worker replicas for high load
- Adjust `MAX_CONCURRENT_VISION_CALLS` based on API limits
- Configure PostgreSQL connection pooling
- Use CDN for frontend assets

### Monitoring
- Set up health check monitoring
- Configure alerting for failed workflows
- Monitor API call logs for rate limits
- Track database size and performance

## License

[Your License Here]

## Support

For issues and questions:
- GitHub Issues: [Repository Issues URL]
- Email: info@stefanai.de
