# Deployment Guide

This guide covers deploying the Best Friend AI Companion application.

## Prerequisites

- Docker and Docker Compose
- Git
- OpenSSL (for SSL certificates)
- At least 4GB RAM and 10GB disk space

## Quick Deployment

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Best-Friend
   ```

2. **Run the deployment script**
   ```bash
   ./deploy.sh
   ```

3. **Access the application**
   - Open https://localhost in your browser
   - Accept the self-signed certificate warning
   - Login with default credentials: admin@bestfriend.local / admin123

## Manual Deployment

### 1. Environment Setup

Copy the environment template:
```bash
cp env.example .env
```

Edit `.env` with your configuration:
```bash
# Flask Configuration
FLASK_ENV=production
SECRET_KEY=your-secret-key-here
FERNET_KEY=your-fernet-key-here

# Database
DATABASE_URL=postgresql://bestfriend:bestfriend@db:5432/bestfriend

# Redis
REDIS_URL=redis://redis:6379/0

# Ollama Configuration
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=llama3.1:8b
EMBED_MODEL=nomic-embed-text

# TTS Configuration
TTS_URL=http://opentts:5500
TTS_VOICE=en_US-amy-low
```

### 2. SSL Certificates

Generate self-signed certificates:
```bash
mkdir -p certs
openssl req -x509 -newkey rsa:4096 -keyout certs/key.pem -out certs/cert.pem -days 365 -nodes -subj "/C=US/ST=State/L=City/O=BestFriend/CN=localhost"
```

For production, use valid SSL certificates:
```bash
# Copy your certificates
cp your-cert.pem certs/cert.pem
cp your-key.pem certs/key.pem
```

### 3. Start Services

```bash
# Build and start all services
docker compose up -d --build

# Check service status
docker compose ps

# View logs
docker compose logs -f
```

### 4. Database Setup

```bash
# Run migrations
docker compose exec web flask db upgrade

# Create admin user
docker compose exec web flask create-admin
```

## Production Deployment

### 1. Security Considerations

- Change default credentials immediately
- Use strong, unique passwords
- Configure firewall rules
- Set up monitoring and logging
- Regular backups

### 2. Environment Variables

For production, ensure these are properly set:
```bash
FLASK_ENV=production
SECRET_KEY=<strong-random-key>
FERNET_KEY=<32-byte-base64-key>
ADMIN_EMAIL=<your-admin-email>
ADMIN_PASSWORD=<strong-password>
```

### 3. SSL Configuration

Replace self-signed certificates with valid ones:
```bash
# Let's Encrypt (example)
certbot certonly --standalone -d yourdomain.com
cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem certs/cert.pem
cp /etc/letsencrypt/live/yourdomain.com/privkey.pem certs/key.pem
```

### 4. Reverse Proxy (Optional)

For additional security, use a reverse proxy like Traefik:

```yaml
# docker-compose.override.yml
version: '3.8'
services:
  nginx:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.bestfriend.rule=Host(`yourdomain.com`)"
      - "traefik.http.routers.bestfriend.tls=true"
      - "traefik.http.services.bestfriend.loadbalancer.server.port=443"
```

## Monitoring

### Health Checks

Check application health:
```bash
curl https://localhost/healthz/
```

### Logs

View application logs:
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f web
docker compose logs -f nginx
docker compose logs -f db
```

### Metrics

Monitor resource usage:
```bash
# Container stats
docker stats

# Disk usage
docker system df
```

## Backup and Recovery

### Database Backup

```bash
# Create backup
docker compose exec db pg_dump -U bestfriend bestfriend > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore backup
docker compose exec -T db psql -U bestfriend bestfriend < backup_file.sql
```

### Volume Backup

```bash
# Backup volumes
docker run --rm -v bestfriend_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz -C /data .

# Restore volumes
docker run --rm -v bestfriend_postgres_data:/data -v $(pwd):/backup alpine tar xzf /backup/postgres_backup.tar.gz -C /data
```

## Troubleshooting

### Common Issues

1. **Port conflicts**
   ```bash
   # Check what's using the ports
   netstat -tulpn | grep :80
   netstat -tulpn | grep :443
   ```

2. **Database connection issues**
   ```bash
   # Check database status
   docker compose exec db pg_isready -U bestfriend
   ```

3. **SSL certificate issues**
   ```bash
   # Verify certificate
   openssl x509 -in certs/cert.pem -text -noout
   ```

### Service Restart

```bash
# Restart specific service
docker compose restart web

# Restart all services
docker compose restart
```

### Complete Reset

```bash
# Stop and remove everything
docker compose down -v

# Rebuild and start
docker compose up -d --build
```

## Scaling

### Horizontal Scaling

For high availability, consider:
- Load balancer (HAProxy, Nginx)
- Database clustering (PostgreSQL with streaming replication)
- Redis clustering
- Multiple application instances

### Resource Limits

Adjust resource limits in docker-compose.yml:
```yaml
services:
  web:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
```

## Updates

### Application Updates

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker compose down
docker compose up -d --build

# Run migrations
docker compose exec web flask db upgrade
```

### Dependency Updates

```bash
# Update requirements
pip install --upgrade -r requirements.txt

# Rebuild container
docker compose build --no-cache web
docker compose up -d web
```

## Support

For deployment issues:
1. Check the logs: `docker compose logs -f`
2. Verify configuration: `docker compose config`
3. Check health endpoint: `curl https://localhost/healthz/`
4. Review this documentation
5. Open an issue on GitHub
