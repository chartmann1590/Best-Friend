# Configuration Guide

This document provides configuration options for the Best Friend AI Companion application.

## Environment Variables

### Core Settings
```bash
FLASK_ENV=production                    # development, production, testing
SECRET_KEY=your-secret-key-here        # Flask secret key
FERNET_KEY=your-fernet-key-here        # Encryption key
DATABASE_URL=postgresql://user:pass@host:port/dbname
REDIS_URL=redis://localhost:6379/0
```

### AI Services
```bash
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
EMBED_MODEL=nomic-embed-text
TTS_URL=http://localhost:5500
TTS_VOICE=en_US-amy-low
STT_LANGUAGE=en
```

### Security
```bash
RATE_LIMIT_PER_IP=100
RATE_LIMIT_PER_USER=50
ADMIN_EMAIL=admin@bestfriend.local
ADMIN_PASSWORD=admin123
```

## Docker Compose

### Basic Configuration
```yaml
version: '3.8'
services:
  web:
    build: ./docker
    environment:
      - FLASK_ENV=production
      - DATABASE_URL=postgresql://bestfriend:bestfriend@db:5432/bestfriend
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis

  nginx:
    build: ./docker
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx:/etc/nginx/conf.d
      - ./certs:/etc/nginx/certs

  db:
    image: pgvector/pgvector:pg15
    environment:
      - POSTGRES_DB=bestfriend
      - POSTGRES_USER=bestfriend
      - POSTGRES_PASSWORD=bestfriend

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

volumes:
  redis_data:
```

## User Settings

### Profile Configuration
```json
{
  "name": "John Doe",
  "timezone": "America/New_York",
  "bio": "AI enthusiast",
  "preferences": {
    "theme": "dark",
    "notifications": true
  }
}
```

### AI Configuration
```json
{
  "ollama_url": "http://ollama:11434",
  "ollama_model": "llama3.1:8b",
  "personality": "You are a helpful AI companion...",
  "temperature": 0.7
}
```

### Voice Settings
```json
{
  "tts_url": "http://opentts:5500",
  "tts_voice": "en_US-amy-low",
  "speaking_rate": 1.0,
  "pitch": 1.0
}
```

## Validation

### Check Configuration
```bash
# Validate Docker Compose
docker compose config

# Test database connection
docker compose exec db psql -U bestfriend -d bestfriend -c "SELECT 1;"

# Test Redis connection
docker compose exec redis redis-cli ping

# Check application health
curl -k https://localhost/healthz/
```

### Common Issues
- **Database**: Check PostgreSQL logs with `docker compose logs db`
- **Redis**: Check Redis logs with `docker compose logs redis`
- **SSL**: Regenerate certificates with `./deploy.sh`
- **Memory**: Monitor with `docker stats`
