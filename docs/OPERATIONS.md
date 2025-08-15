# Operations Guide

This guide covers the operational aspects of running the Best Friend AI Companion application in production.

## System Requirements

### Minimum Requirements
- **CPU**: 4 cores (2.4 GHz)
- **RAM**: 8 GB
- **Storage**: 50 GB SSD
- **Network**: 100 Mbps

### Recommended Requirements
- **CPU**: 8+ cores (3.0 GHz)
- **RAM**: 16+ GB
- **Storage**: 100+ GB NVMe SSD
- **Network**: 1 Gbps

### Software Requirements
- **OS**: Linux (Ubuntu 20.04+, CentOS 8+, RHEL 8+)
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **OpenSSL**: 1.1.1+

## Monitoring & Logging

### Health Checks

Monitor the application health endpoint:
```bash
# Check overall health
curl -k https://your-domain/healthz/

# Expected response:
{
  "status": "healthy",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "ollama": "healthy",
    "tts": "healthy"
  }
}
```

### Log Monitoring

View application logs:
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f web
docker compose logs -f nginx
docker compose logs -f db

# Follow logs with timestamps
docker compose logs -f --timestamps web
```

### Resource Monitoring

Monitor system resources:
```bash
# Container stats
docker stats

# System resources
htop
iotop
nethogs

# Disk usage
df -h
docker system df
```

## Backup & Recovery

### Database Backups

#### Automated Backup Script
Create `/usr/local/bin/backup-bestfriend.sh`:
```bash
#!/bin/bash

# Configuration
BACKUP_DIR="/opt/backups/bestfriend"
RETENTION_DAYS=30
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="bestfriend_db_${DATE}.sql"

# Create backup directory
mkdir -p $BACKUP_DIR

# Perform backup
docker compose exec -T db pg_dump -U bestfriend bestfriend > "$BACKUP_DIR/$BACKUP_FILE"

# Compress backup
gzip "$BACKUP_DIR/$BACKUP_FILE"

# Remove old backups
find $BACKUP_DIR -name "*.sql.gz" -mtime +$RETENTION_DAYS -delete

# Log backup
echo "$(date): Database backup completed: $BACKUP_FILE.gz" >> /var/log/bestfriend-backup.log
```

Make it executable and add to crontab:
```bash
chmod +x /usr/local/bin/backup-bestfriend.sh

# Add to crontab (daily at 2 AM)
crontab -e
0 2 * * * /usr/local/bin/backup-bestfriend.sh
```

#### Manual Backup
```bash
# Create backup
docker compose exec -T db pg_dump -U bestfriend bestfriend > backup_$(date +%Y%m%d_%H%M%S).sql

# Compress backup
gzip backup_*.sql
```

#### Restore Database
```bash
# Stop application
docker compose down

# Restore from backup
gunzip -c backup_20240101_120000.sql.gz | docker compose exec -T db psql -U bestfriend bestfriend

# Start application
docker compose up -d
```

### Volume Backups

#### Backup Volumes
```bash
# Create backup directory
mkdir -p /opt/backups/volumes

# Backup PostgreSQL data
docker run --rm -v bestfriend_postgres_data:/data -v /opt/backups/volumes:/backup \
  alpine tar czf /backup/postgres_$(date +%Y%m%d).tar.gz -C /data .

# Backup Redis data
docker run --rm -v bestfriend_redis_data:/data -v /opt/backups/volumes:/backup \
  alpine tar czf /backup/redis_$(date +%Y%m%d).tar.gz -C /data .

# Backup OpenTTS data
docker run --rm -v bestfriend_opentts_data:/data -v /opt/backups/volumes:/backup \
  alpine tar czf /backup/opentts_$(date +%Y%m%d).tar.gz -C /data .
```

#### Restore Volumes
```bash
# Stop application
docker compose down

# Remove existing volumes
docker volume rm bestfriend_postgres_data bestfriend_redis_data bestfriend_opentts_data

# Restore PostgreSQL
docker run --rm -v bestfriend_postgres_data:/data -v /opt/backups/volumes:/backup \
  alpine tar xzf /backup/postgres_20240101.tar.gz -C /data

# Restore Redis
docker run --rm -v bestfriend_redis_data:/data -v /opt/backups/volumes:/backup \
  alpine tar xzf /backup/redis_20240101.tar.gz -C /data

# Restore OpenTTS
docker run --rm -v bestfriend_opentts_data:/data -v /opt/backups/volumes:/backup \
  alpine tar xzf /backup/opentts_20240101.tar.gz -C /data

# Start application
docker compose up -d
```

## Performance Tuning

### Database Optimization

#### PostgreSQL Tuning
Create `postgresql.conf` optimizations:
```sql
-- Memory settings
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB

-- Connection settings
max_connections = 100
shared_preload_libraries = 'pg_stat_statements'

-- Logging
log_statement = 'all'
log_duration = on
log_min_duration_statement = 1000

-- pgvector settings
vector_cache_size = 256MB
```

#### Database Maintenance
```bash
# Run maintenance tasks
docker compose exec db psql -U bestfriend bestfriend -c "VACUUM ANALYZE;"
docker compose exec db psql -U bestfriend bestfriend -c "REINDEX DATABASE bestfriend;"

# Monitor table sizes
docker compose exec db psql -U bestfriend bestfriend -c "
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"
```

### Redis Optimization

#### Redis Configuration
```bash
# Create custom redis.conf
cat > redis.conf << EOF
maxmemory 512mb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
EOF

# Update docker-compose.yml to use custom config
volumes:
  - ./redis.conf:/usr/local/etc/redis/redis.conf
```

### Application Tuning

#### Gunicorn Configuration
Update `docker/web.Dockerfile`:
```dockerfile
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--worker-class", "gevent", "--worker-connections", "1000", "--timeout", "120", "--keep-alive", "2", "--max-requests", "1000", "--max-requests-jitter", "100", "app:create_app()"]
```

#### Nginx Optimization
Update `nginx/default.conf`:
```nginx
# Gzip compression
gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;

# Client caching
location ~* \.(css|js|png|jpg|jpeg|gif|ico|svg)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}

# Proxy buffering
proxy_buffering on;
proxy_buffer_size 4k;
proxy_buffers 8 4k;
```

## Security Hardening

### SSL/TLS Configuration

#### Let's Encrypt Setup
```bash
# Install certbot
apt update && apt install certbot

# Get certificate
certbot certonly --standalone -d yourdomain.com

# Copy certificates
cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem certs/cert.pem
cp /etc/letsencrypt/live/yourdomain.com/privkey.pem certs/key.pem

# Set permissions
chmod 600 certs/key.pem
chmod 644 certs/cert.pem

# Restart nginx
docker compose restart nginx
```

#### Auto-renewal
```bash
# Test renewal
certbot renew --dry-run

# Add to crontab
crontab -e
0 12 * * * /usr/bin/certbot renew --quiet && docker compose restart nginx
```

### Firewall Configuration

#### UFW Setup
```bash
# Enable UFW
ufw enable

# Allow SSH
ufw allow ssh

# Allow HTTP/HTTPS
ufw allow 80
ufw allow 443

# Allow internal Docker network
ufw allow from 172.16.0.0/12

# Show status
ufw status
```

### Access Control

#### Admin IP Whitelisting
Update `nginx/default.conf`:
```nginx
# Allow admin access only from specific IPs
location /admin {
    allow 192.168.1.100;
    allow 10.0.0.50;
    deny all;
    
    proxy_pass http://web;
    # ... other proxy settings
}
```

## Troubleshooting

### Common Issues

#### Database Connection Issues
```bash
# Check database status
docker compose exec db pg_isready -U bestfriend

# Check logs
docker compose logs db

# Test connection
docker compose exec db psql -U bestfriend -d bestfriend -c "SELECT 1;"
```

#### Memory Issues
```bash
# Check memory usage
docker stats

# Check system memory
free -h

# Check swap
swapon --show

# Restart services
docker compose restart
```

#### SSL Certificate Issues
```bash
# Check certificate validity
openssl x509 -in certs/cert.pem -text -noout

# Check certificate expiration
openssl x509 -in certs/cert.pem -noout -dates

# Test SSL connection
openssl s_client -connect yourdomain.com:443 -servername yourdomain.com
```

### Performance Issues

#### Slow Response Times
```bash
# Check database performance
docker compose exec db psql -U bestfriend bestfriend -c "
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
"

# Check slow queries
docker compose exec db psql -U bestfriend bestfriend -c "
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
WHERE mean_time > 1000
ORDER BY mean_time DESC;
"
```

#### High Memory Usage
```bash
# Check Redis memory
docker compose exec redis redis-cli info memory

# Check PostgreSQL memory
docker compose exec db psql -U bestfriend bestfriend -c "
SELECT name, setting, unit, context
FROM pg_settings
WHERE name LIKE '%memory%';
"
```

### Recovery Procedures

#### Complete System Recovery
```bash
# Stop all services
docker compose down

# Backup current state
cp -r . ../bestfriend-backup-$(date +%Y%m%d_%H%M%S)

# Restore from backup
cp -r ../bestfriend-backup-20240101_120000/* .

# Start services
docker compose up -d

# Run migrations
docker compose exec web flask db upgrade
```

#### Data Recovery
```bash
# Stop application
docker compose down

# Restore database
gunzip -c backup_20240101_120000.sql.gz | docker compose exec -T db psql -U bestfriend bestfriend

# Restore volumes if needed
# (see volume backup/restore section above)

# Start application
docker compose up -d

# Verify data
docker compose exec web flask shell
```

## Maintenance Schedule

### Daily Tasks
- [ ] Check health endpoint
- [ ] Review error logs
- [ ] Monitor resource usage
- [ ] Verify backup completion

### Weekly Tasks
- [ ] Review performance metrics
- [ ] Check disk usage
- [ ] Update system packages
- [ ] Review security logs

### Monthly Tasks
- [ ] Database maintenance (VACUUM, ANALYZE)
- [ ] SSL certificate renewal check
- [ ] Performance review and tuning
- [ ] Security audit

### Quarterly Tasks
- [ ] Full system backup
- [ ] Disaster recovery test
- [ ] Performance benchmarking
- [ ] Security updates

## Support & Escalation

### First Level Support
- Check application logs
- Verify service status
- Review recent changes
- Check system resources

### Second Level Support
- Database performance analysis
- Network configuration review
- Security incident response
- Performance optimization

### Third Level Support
- Vendor support (if applicable)
- Architecture review
- Custom development
- Advanced troubleshooting

### Emergency Contacts
- **System Administrator**: [Contact Info]
- **Database Administrator**: [Contact Info]
- **Security Team**: [Contact Info]
- **Vendor Support**: [Contact Info]

## Documentation

### Required Documentation
- [ ] System architecture diagram
- [ ] Network topology
- [ ] Backup procedures
- [ ] Recovery procedures
- [ ] Contact information
- [ ] Escalation procedures

### Maintenance Records
- [ ] Change logs
- [ ] Incident reports
- [ ] Performance metrics
- [ ] Security audits
- [ ] Backup verification logs
