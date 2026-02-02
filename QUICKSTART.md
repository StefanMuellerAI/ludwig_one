# LudwigOne - Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Prerequisites
- Docker & Docker Compose installed
- At least 8GB RAM
- 10GB free disk space

### Step 1: Clone & Configure

```bash
# Navigate to project
cd /Users/davinci_kollektiv/Documents/LO_Test

# Copy environment file
cp .env.example .env

# Edit .env and set these required values:
# - POSTGRES_PASSWORD (choose a secure password)
# - SECRET_KEY (generate with: openssl rand -hex 32)
# - MISTRAL_API_KEY (already set: cVaOcc6VhIjeF4kmpouVKZUJh8zW97mM)
```

### Step 2: Start Services

```bash
# Start all services
./start.sh

# OR with Ollama (if you want local LLM):
./start.sh ollama
```

### Step 3: Verify Services

Wait ~30 seconds, then check:

- ✅ API Health: http://localhost:8000/health
- ✅ API Docs: http://localhost:8000/docs
- ✅ Temporal UI: http://localhost:8080

### Step 4: Test the API

#### Upload a TAR Archive (Flow 1):

```bash
curl -X POST "http://localhost:8000/api/v1/jobs/tar-upload" \
  -F "file=@/path/to/your/archive.tar.gz"
```

#### Upload a PDF (Flow 2):

```bash
curl -X POST "http://localhost:8000/api/v1/jobs/pdf-upload" \
  -F "file=@/path/to/your/document.pdf"
```

#### Check Job Status:

```bash
curl "http://localhost:8000/api/v1/jobs/{job-id}"
```

#### Download Result:

```bash
curl "http://localhost:8000/api/v1/jobs/{job-id}/download" \
  --output result.tar.gz
```

## 📊 Monitor Workflows

Open Temporal UI: http://localhost:8080

- View running workflows
- Check retry attempts
- Debug errors
- Monitor worker health

## 🔧 Manage Categories

```bash
# List categories
curl "http://localhost:8000/api/v1/admin/categories"

# Create category
curl -X POST "http://localhost:8000/api/v1/admin/categories" \
  -H "Content-Type: application/json" \
  -d '{"name": "Verträge", "description": "Vertragsunterlagen", "color": "#FF5733"}'

# Update category
curl -X PUT "http://localhost:8000/api/v1/admin/categories/{id}" \
  -H "Content-Type: application/json" \
  -d '{"display_order": 1}'
```

## 🔍 View Logs

```bash
# API logs
docker-compose logs -f api

# Worker logs
docker-compose logs -f worker

# Database logs
docker-compose logs -f postgres

# All services
docker-compose logs -f
```

## 🛑 Stop Services

```bash
./stop.sh

# Or remove all data:
docker-compose down -v
```

## 🐛 Troubleshooting

### API not starting?
```bash
docker-compose logs api
# Check for database connection errors
```

### Worker not processing?
```bash
docker-compose logs worker
# Verify Temporal connection
```

### Database issues?
```bash
docker-compose exec postgres psql -U ludwigone -d ludwigone
# Check database is initialized
```

### Vision API timeouts?
```bash
# Adjust in .env:
VISION_API_TIMEOUT_SECONDS=600
MAX_CONCURRENT_VISION_CALLS=3
```

## 📚 Next Steps

1. **Frontend Development**: Build React UI in `frontend/`
2. **Email Notifications**: Configure SMTP in `.env`
3. **Customize Prompts**: Use Admin API to update prompt templates
4. **Add More Categories**: Tailor to your use case
5. **Integrate Ollama**: Use `./start.sh ollama` for local LLM

## 📖 Full Documentation

See [README.md](README.md) for complete documentation.

## 🆘 Support

- GitHub Issues: [Repository URL]
- Email: info@stefanai.de
- Temporal UI: http://localhost:8080

---

**Happy Processing! 🎉**
