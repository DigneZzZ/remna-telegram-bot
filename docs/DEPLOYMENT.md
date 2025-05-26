# 🚀 Production Deployment Guide

This guide covers deploying the Remnawave Admin Bot using Docker containers from GitHub Container Registry (GHCR).

## 📋 Prerequisites

- Docker and Docker Compose installed
- GitHub repository with GHCR access
- Remnawave API credentials
- Telegram Bot token

## 🔧 Quick Setup

### 1. Download Production Files

```bash
# Download the production compose file
curl -O https://raw.githubusercontent.com/dignezzz/remna-telegram-bot/main/docker-compose-prod.yml

# Download environment template
curl -O https://raw.githubusercontent.com/dignezzz/remna-telegram-bot/main/.env.production
```

### 2. Configure Environment

```bash
# Copy and edit environment file
cp .env.production .env
nano .env  # Edit with your actual values
```

### 3. Deploy

```bash
# Pull and start the bot
docker-compose -f docker-compose-prod.yml up -d

# Check logs
docker-compose -f docker-compose-prod.yml logs -f
```

## 🔐 Environment Configuration

Create a `.env` file with the following variables:

```env
# Required
API_BASE_URL=https://your-remnawave-api.com
REMNAWAVE_API_TOKEN=your_api_token
TELEGRAM_BOT_TOKEN=your_bot_token
ADMIN_USER_IDS=123456789,987654321

# Optional
LOG_LEVEL=INFO
```

## 🤖 GitHub Actions Deployment

The repository includes automated CI/CD workflows:

### Workflow Files

1. **`.github/workflows/docker-publish.yml`** - Builds and publishes Docker images
2. **`.github/workflows/deploy.yml`** - Handles deployment (requires configuration)

### Automatic Triggers

- **Push to main/master**: Builds and publishes `latest` tag
- **Git tags (v*)**: Builds and publishes version-specific tags
- **Pull requests**: Builds for testing (doesn't publish)

### Manual Deployment

```bash
# Using GitHub CLI
gh workflow run deploy.yml -f image_tag=latest

# Or use the GitHub web interface
```

## 📦 Docker Images

Images are available at: `ghcr.io/dignezzz/remna-telegram-bot`

### Available Tags

- `latest` - Latest stable version from main branch
- `v2.0.0` - Specific version tags
- `main` - Latest development version

### Image Features

- Multi-architecture support (AMD64, ARM64)
- Non-root user for security
- Health checks included
- Optimized for production use

## 🛠️ Deployment Scripts

### Linux/macOS (Bash)

```bash
# Make executable
chmod +x deploy.sh

# Deploy latest version
./deploy.sh

# Deploy specific version
./deploy.sh v2.0.0

# Deploy with custom environment
./deploy.sh latest staging
```

### Windows (PowerShell)

```powershell
# Deploy latest version
.\deploy.ps1

# Deploy specific version
.\deploy.ps1 -Tag "v2.0.0"

# Deploy with custom environment
.\deploy.ps1 -Tag "latest" -Environment "staging"
```

## 📊 Monitoring

### Health Checks

The container includes built-in health checks:

```bash
# Check container health
docker-compose -f docker-compose-prod.yml ps

# View health check logs
docker inspect remna-telegram-bot --format='{{.State.Health.Status}}'
```

### Logs

```bash
# View real-time logs
docker-compose -f docker-compose-prod.yml logs -f

# View specific service logs
docker-compose -f docker-compose-prod.yml logs -f remna-bot

# View last 100 lines
docker-compose -f docker-compose-prod.yml logs --tail=100
```

### Resource Usage

```bash
# View container stats
docker stats remna-telegram-bot

# View detailed info
docker inspect remna-telegram-bot
```

## 🔄 Updates

### Automated Updates

1. Push changes to main branch
2. GitHub Actions builds new image
3. Pull and restart container:

```bash
docker-compose -f docker-compose-prod.yml pull
docker-compose -f docker-compose-prod.yml up -d
```

### Manual Updates

```bash
# Update to specific version
docker-compose -f docker-compose-prod.yml down
docker pull ghcr.io/dignezzz/remna-telegram-bot:v2.1.0
# Edit docker-compose-prod.yml to use new tag
docker-compose -f docker-compose-prod.yml up -d
```

## 🚨 Troubleshooting

### Common Issues

#### Image Pull Errors
```bash
# Login to GHCR (if private repo)
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin
```

#### Container Won't Start
```bash
# Check logs for errors
docker-compose -f docker-compose-prod.yml logs

# Check environment variables
docker-compose -f docker-compose-prod.yml config
```

#### Permission Issues
```bash
# Fix log directory permissions
sudo chown -R 1000:1000 ./logs
```

### Rollback

```bash
# Stop current version
docker-compose -f docker-compose-prod.yml down

# Use previous image tag
docker pull ghcr.io/dignezzz/remna-telegram-bot:v1.9.0
# Update compose file and restart
docker-compose -f docker-compose-prod.yml up -d
```

## 📝 Best Practices

### Security

1. Use non-root user (included in image)
2. Keep API tokens in environment variables
3. Regularly update base images
4. Monitor container resources

### Performance

1. Set appropriate resource limits
2. Use health checks for monitoring
3. Configure log rotation
4. Monitor disk usage for logs

### Maintenance

1. Regular backups of configuration
2. Monitor for security updates
3. Test deployment in staging first
4. Keep rollback plan ready

## 📞 Support

For issues with deployment:

1. Check logs first: `docker-compose logs`
2. Verify environment configuration
3. Check GitHub Issues for known problems
4. Contact maintainers if needed

---

**📦 Image**: `ghcr.io/dignezzz/remna-telegram-bot:latest`  
**🔗 Repository**: `https://github.com/dignezzz/remna-telegram-bot`  
**📖 Documentation**: See main README.md for bot usage
