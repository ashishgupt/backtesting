# 🚀 Portfolio Backtesting System - Production Deployment Guide

## 📋 Overview
Complete production deployment guide for the AI-powered portfolio backtesting system with Claude integration.

## 🏗️ Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     Nginx       │───▶│   FastAPI       │───▶│  PostgreSQL     │
│  (Load Balancer)│    │   (Python)      │    │ (TimescaleDB)   │
│  Port 80/443    │    │   Port 8000     │    │   Port 5432     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
    Web UI + API            Claude Integration      Time-Series Data
```

## 🚦 Prerequisites

### System Requirements
- Docker 20.10+ and Docker Compose 2.0+
- 4GB RAM minimum (8GB recommended)
- 20GB disk space minimum
- Ubuntu 20.04+ or similar Linux distribution

### Domain Setup (Optional)
- Domain name pointing to your server
- SSL certificate (Let's Encrypt recommended)

## ⚡ Quick Start

### 1. Clone and Setup
```bash
# Clone repository
git clone <your-repo-url> portfolio-system
cd portfolio-system

# Copy production environment
cp .env.production .env

# Generate secure secret key
openssl rand -hex 32
# Update SECRET_KEY in .env with generated value
```

### 2. Database Configuration
```bash
# Update database passwords in .env
# POSTGRES_PASSWORD=your-secure-password
# DATABASE_URL=postgresql://portfolio_user:your-secure-password@db:5432/backtesting
```

### 3. Deploy System
```bash
# Build and start all services
docker-compose up -d

# Check service health
docker-compose ps
docker-compose logs -f api

# Initialize database with historical data
docker-compose exec api python load_historical_data.py
```

### 4. Verify Deployment
```bash
# Health check
curl http://localhost/health

# Test API
curl http://localhost/api/data/assets

# Test Claude integration
curl -X POST http://localhost/api/chat/recommend \
  -H "Content-Type: application/json" \
  -d '{"message": "I want a balanced portfolio"}'
```

## 🔧 Configuration

### Environment Variables (.env)
```bash
# Database
DATABASE_URL=postgresql://user:pass@db:5432/backtesting
POSTGRES_USER=portfolio_user
POSTGRES_PASSWORD=secure_password_here
POSTGRES_DB=backtesting

# API
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false
LOG_LEVEL=info

# Security
SECRET_KEY=your-super-secret-key-64-chars-minimum
CORS_ORIGINS=https://your-domain.com,https://www.your-domain.com

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=3600
```

### Nginx Configuration (nginx.conf)
- Rate limiting: 10 req/s for API, 5 req/s for chat
- Security headers enabled
- SSL termination (if configured)
- Static file serving for web UI

### Docker Services
- **nginx**: Reverse proxy and load balancer
- **api**: FastAPI application with Claude integration  
- **db**: PostgreSQL 16 with TimescaleDB extension

## 🔒 Security Checklist

### Database Security
- [ ] Change default passwords in `.env`
- [ ] Use strong passwords (16+ characters)
- [ ] Enable SSL connections in production
- [ ] Restrict database access to application only

### Application Security
- [ ] Generate unique SECRET_KEY
- [ ] Configure CORS_ORIGINS for your domain
- [ ] Enable HTTPS in production
- [ ] Set up fail2ban for SSH protection

### Network Security
- [ ] Configure firewall (UFW/iptables)
- [ ] Close unnecessary ports
- [ ] Use private networks for containers
- [ ] Set up monitoring and alerting

## 📊 Monitoring

### Health Checks
```bash
# System health
docker-compose ps

# Application health
curl http://localhost/health

# Database health
docker-compose exec db pg_isready -U portfolio_user

# Logs
docker-compose logs -f api
docker-compose logs -f db
docker-compose logs -f nginx
```

### Performance Metrics
- API response times (target: <2s)
- Database query performance
- Memory and CPU usage
- Disk space monitoring

## 🔄 Maintenance

### Backup Strategy
```bash
# Database backup
docker-compose exec db pg_dump -U portfolio_user backtesting > backup_$(date +%Y%m%d).sql

# Automated backup script
#!/bin/bash
docker-compose exec db pg_dump -U portfolio_user backtesting | gzip > /backups/portfolio_$(date +%Y%m%d_%H%M).sql.gz
find /backups -name "portfolio_*.sql.gz" -mtime +30 -delete
```

### Updates and Upgrades
```bash
# Update application
git pull origin main
docker-compose build --no-cache
docker-compose up -d

# Update dependencies
docker-compose exec api pip install -r requirements.txt

# Database migrations (if needed)
docker-compose exec api alembic upgrade head
```

### Data Refresh
```bash
# Refresh market data (daily)
docker-compose exec api python load_historical_data.py

# Clear cached results (if needed)
docker-compose exec db psql -U portfolio_user -d backtesting -c "TRUNCATE portfolio_snapshots;"
```

## 🌐 SSL/HTTPS Setup

### Let's Encrypt with Certbot
```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Generate certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Update nginx.conf for HTTPS redirect
# Certbot will automatically modify configuration
```

### Manual SSL Certificate
```bash
# Update nginx.conf with SSL configuration
server {
    listen 443 ssl http2;
    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    # ... rest of configuration
}
```

## ⚙️ Advanced Configuration

### Custom Domain Setup
1. Update CORS_ORIGINS in `.env`
2. Configure nginx server_name
3. Set up SSL certificates
4. Update API_BASE in web UI JavaScript

### Multi-Instance Deployment
```yaml
# docker-compose.yml additions
services:
  api:
    deploy:
      replicas: 3
    # ... rest of configuration
```

### Performance Optimization
- Enable Redis caching for expensive calculations
- Use connection pooling for database
- Implement CDN for static assets
- Enable gzip compression in nginx

## 🚨 Troubleshooting

### Common Issues

**Database Connection Failed**
```bash
# Check database status
docker-compose logs db
docker-compose exec db pg_isready

# Verify credentials
docker-compose exec db psql -U portfolio_user -d backtesting
```

**API Not Responding**
```bash
# Check API logs
docker-compose logs api

# Verify service is running
docker-compose exec api curl http://localhost:8000/health

# Check database connectivity
docker-compose exec api python -c "from src.models.database import SessionLocal; print('DB OK')"
```

**Web UI Not Loading**
```bash
# Check nginx logs
docker-compose logs nginx

# Verify static files are mounted
docker-compose exec nginx ls -la /usr/share/nginx/html/

# Test direct API access
curl http://localhost:8000/health
```

### Log Analysis
```bash
# Real-time logs
docker-compose logs -f --tail=100

# Error filtering
docker-compose logs api 2>&1 | grep ERROR

# Performance monitoring
docker stats
```

## 📈 Scaling Considerations

### Vertical Scaling
- Increase container resource limits
- Add more CPU/RAM to server
- Optimize database queries

### Horizontal Scaling
- Multiple API instances behind load balancer
- Database read replicas
- Separate caching layer (Redis)

### Database Optimization
- Partition large tables by date
- Optimize queries with proper indexes
- Regular VACUUM and ANALYZE operations

## 🎯 Performance Benchmarks

### Target Metrics
- **API Response Time**: <2 seconds for backtesting
- **Chat Response Time**: <1 second for recommendations
- **Concurrent Users**: 50+ simultaneous users
- **Availability**: 99.9% uptime target

### Load Testing
```bash
# Install testing tools
pip install locust

# Run load test
locust -f tests/load_test.py --host=http://localhost
```

## ✅ Production Checklist

### Pre-Deployment
- [ ] Security review completed
- [ ] Performance testing passed
- [ ] Backup strategy implemented
- [ ] Monitoring configured
- [ ] SSL certificates installed
- [ ] Documentation updated

### Post-Deployment
- [ ] Health checks passing
- [ ] Historical data loaded
- [ ] Claude integration tested
- [ ] User acceptance testing completed
- [ ] Performance monitoring active
- [ ] Backup schedule verified

---

*🔄 Last Updated: Session 3 - Production Deployment Ready*

## 📞 Support
For issues or questions:
1. Check logs: `docker-compose logs`
2. Review troubleshooting section
3. Verify configuration settings
4. Test individual components
