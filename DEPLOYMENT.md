# LudwigOne - Deployment Guide

## ✅ Implementation Complete

All backend TODOs are resolved and both frontends are ready!

## 🚀 Quick Start

### 1. Create Environment File

```bash
cp .env.example .env
```

Edit `.env` and set these **required** values:

```bash
# Generate a secure password
POSTGRES_PASSWORD=your_secure_postgres_password_here

# Generate a random secret key (run: openssl rand -hex 32)
SECRET_KEY=your_32_char_secret_key_here

# Already set in .env.example:
MISTRAL_API_KEY=cVaOcc6VhIjeF4kmpouVKZUJh8zW97mM
SMTP_PASSWORD=$6^&Rc3A^a&9VHx
```

### 2. Start All Services

```bash
./start.sh
```

This will:
- ✅ Validate environment variables
- ✅ Start PostgreSQL with auto-initialization
- ✅ Start Temporal server
- ✅ Start API backend
- ✅ Start 2x workers
- ✅ Start user frontend
- ✅ Start admin dashboard
- ✅ Check service health

### 3. Access Services

After ~30 seconds, services will be available:

- **User Frontend:** http://localhost:3000
- **Admin Dashboard:** http://localhost:3001
- **API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **Temporal UI:** http://localhost:8080

## 📋 Service Overview

| Service | Port | Purpose | Status Check |
|---------|------|---------|--------------|
| PostgreSQL | 5432 | Database | `docker-compose exec postgres pg_isready` |
| Temporal | 7233 | Workflow Engine | http://localhost:8080 |
| Temporal UI | 8080 | Workflow Monitoring | http://localhost:8080 |
| API | 8000 | Backend API | http://localhost:8000/health |
| Worker (x2) | - | Temporal Workers | `docker-compose logs worker` |
| Frontend | 3000 | User Interface | http://localhost:3000 |
| Dashboard | 3001 | Admin Interface | http://localhost:3001 |

## 🧪 Testing the System

### Test Flow 1: TAR Processing

```bash
# 1. Create a test TAR archive
mkdir test_docs
echo "Test document 1" > test_docs/doc1.txt
echo "Test document 2" > test_docs/doc2.txt
tar -czf test.tar.gz test_docs/

# 2. Upload via API
curl -X POST "http://localhost:8000/api/v1/jobs/tar-upload" \
  -F "file=@test.tar.gz"

# Response:
# {
#   "job_id": "uuid-here",
#   "message": "TAR archive uploaded successfully"
# }

# 3. Check status
curl "http://localhost:8000/api/v1/jobs/{job-id}"

# 4. Or use the frontend at http://localhost:3000
```

### Test Flow 2: PDF Splitting

```bash
# 1. Upload a PDF via frontend or API
curl -X POST "http://localhost:8000/api/v1/jobs/pdf-upload" \
  -F "file=@document.pdf"

# 2. Monitor in Temporal UI: http://localhost:8080
# 3. Download results when complete
```

## 📊 Monitor Workflows

Open Temporal UI: http://localhost:8080

You can see:
- ✅ Running workflows
- ✅ Workflow history
- ✅ Activity execution details
- ✅ Retry attempts
- ✅ Error logs

## 🔧 Admin Dashboard Features

Access: http://localhost:3001

### Overview Page
- System statistics
- Recent jobs
- Active categories

### Categories Management
- ✅ Create/Edit/Delete categories
- ✅ Change colors and ordering
- ✅ Activate/deactivate categories

### Configuration
- ✅ View all system settings
- ✅ Update configuration values
- ✅ Toggle secret visibility
- ✅ Email and API settings

## 🛠️ Development Mode

### Backend Development

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run API locally
python -m app.main

# Run worker locally
python -m app.worker
```

### Frontend Development

```bash
cd frontend
npm install
npm run dev
# Frontend runs at http://localhost:3000
```

### Dashboard Development

```bash
cd dashboard
npm install
npm run dev
# Dashboard runs at http://localhost:3001
```

## 📝 View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f worker
docker-compose logs -f postgres

# With timestamps
docker-compose logs -f --timestamps api
```

## 🛑 Stop Services

```bash
# Stop all services
./stop.sh

# Or manually
docker-compose down

# Remove volumes (deletes all data!)
docker-compose down -v
```

## 🔍 Troubleshooting

### API Won't Start

```bash
# Check logs
docker-compose logs api

# Common issues:
# - Database connection failed: Check POSTGRES_PASSWORD
# - Temporal connection failed: Wait 30s for Temporal to start
```

### Worker Not Processing

```bash
# Check worker logs
docker-compose logs worker

# Verify Temporal connection
docker-compose logs temporal

# Restart workers
docker-compose restart worker
```

### Frontend Build Failed

```bash
# Rebuild frontend
docker-compose build frontend
docker-compose up -d frontend
```

### Database Connection Issues

```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Connect to database
docker-compose exec postgres psql -U ludwigone -d ludwigone

# Check tables
\dt

# Exit psql
\q
```

### Vision API Timeouts

If you experience Vision API timeouts:

1. Edit `.env`:
```bash
VISION_API_TIMEOUT_SECONDS=600  # Increase timeout
MAX_CONCURRENT_VISION_CALLS=3   # Reduce concurrent calls
```

2. Restart workers:
```bash
docker-compose restart worker
```

## 🔐 Security Checklist

Before production deployment:

- [ ] Change `POSTGRES_PASSWORD` to a strong password
- [ ] Generate new `SECRET_KEY` with `openssl rand -hex 32`
- [ ] Review `ALLOWED_ORIGINS` in `.env`
- [ ] Enable HTTPS/TLS
- [ ] Set up firewall rules
- [ ] Configure backup strategy
- [ ] Review email credentials
- [ ] Set up monitoring/alerting

## 📈 Performance Tuning

### For High Load

1. **Scale Workers:**
```yaml
# In docker-compose.yml
worker:
  deploy:
    replicas: 4  # Increase from 2
```

2. **Adjust Concurrency:**
```bash
# In .env
MAX_CONCURRENT_VISION_CALLS=8  # Increase if API allows
```

3. **Database Optimization:**
```bash
# Increase connection pool in config.py
pool_size=20
max_overflow=40
```

### For Large Files

```bash
# In .env
UPLOAD_MAX_SIZE_MB=1000  # Increase limit
VISION_API_TIMEOUT_SECONDS=600  # Increase timeout
```

## 🎯 What's Working

✅ **Backend:**
- All API endpoints functional
- Both workflows implemented
- Email notifications working
- Temporal integration complete
- Database schema finalized

✅ **Frontend:**
- Upload interface with drag & drop
- Job listing with real-time updates
- Job detail with progress tracking
- Download buttons for results

✅ **Dashboard:**
- Overview with statistics
- Category management (CRUD)
- Configuration editor
- Secret management

## 📞 Support

If you encounter issues:

1. Check logs: `docker-compose logs -f`
2. Verify services: `docker-compose ps`
3. Check Temporal UI: http://localhost:8080
4. Review API docs: http://localhost:8000/docs

---

**Your system is ready to use! 🎉**

Start by uploading a document at http://localhost:3000
