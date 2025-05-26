# 🔧 GitHub Repository Setup Guide

This guide covers setting up the GitHub repository for automated CI/CD deployment of the Remnawave Admin Bot.

## 📋 Prerequisites

- GitHub account
- Repository: `dignezzz/remna-telegram-bot`
- GitHub Container Registry access
- Understanding of GitHub Actions

## 🔐 Repository Settings

### 1. Enable GitHub Packages

1. Go to repository **Settings** → **General**
2. Scroll to **Features** section
3. Ensure **Packages** is enabled
4. Set package visibility to **Public** or **Private** as needed

### 2. Configure Actions Permissions

1. Go to **Settings** → **Actions** → **General**
2. Set **Actions permissions** to:
   - ✅ Allow all actions and reusable workflows
3. Set **Workflow permissions** to:
   - ✅ Read and write permissions
   - ✅ Allow GitHub Actions to create and approve pull requests

### 3. Set Repository Secrets (if needed)

If you need custom deployment secrets:

1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Add repository secrets:
   ```
   DEPLOY_HOST=your-server-ip
   DEPLOY_USER=your-username
   DEPLOY_KEY=your-ssh-private-key
   DEPLOY_WEBHOOK_URL=https://your-webhook-url
   DEPLOY_WEBHOOK_TOKEN=your-webhook-token
   ```

## 🚀 Initial Setup

### 1. Create Repository

```bash
# Create new repository on GitHub
# Repository name: remna-telegram-bot
# Owner: dignezzz
# Visibility: Public (for GHCR free tier)
```

### 2. Push Code

```bash
# Clone your bot code
git clone <your-source-repo>
cd remna-telegram-bot

# Add GitHub remote
git remote add origin https://github.com/dignezzz/remna-telegram-bot.git

# Push to GitHub
git push -u origin main
```

### 3. Verify Workflows

After pushing, check:

1. **Actions tab** - Workflows should appear
2. **Packages tab** - Docker images will appear after first build
3. **Releases tab** - Will populate when you create tags

## 🔄 Automated Workflows

### Available Workflows

1. **docker-publish.yml** - Builds and publishes Docker images
2. **deploy.yml** - Handles deployment (configurable)
3. **release.yml** - Creates GitHub releases with assets

### Trigger Events

| Workflow | Trigger | Description |
|----------|---------|-------------|
| `docker-publish.yml` | Push to main, tags `v*`, PRs | Builds Docker images |
| `deploy.yml` | After successful build, manual | Deploys to production |
| `release.yml` | Push tags `v*` | Creates GitHub releases |

## 📦 Package Registry (GHCR)

### Automatic Configuration

The workflows automatically:
- ✅ Login to `ghcr.io` using `GITHUB_TOKEN`
- ✅ Build multi-architecture images (AMD64, ARM64)
- ✅ Push to `ghcr.io/dignezzz/remna-telegram-bot`
- ✅ Tag images with version numbers and `latest`

### Image Access

Images will be available at:
```
ghcr.io/dignezzz/remna-telegram-bot:latest
ghcr.io/dignezzz/remna-telegram-bot:v2.0.0
ghcr.io/dignezzz/remna-telegram-bot:main
```

### Package Visibility

For public packages (free):
1. Go to **Packages** tab in repository
2. Click on your package
3. **Package settings** → **Change visibility** → **Public**

## 🏷️ Creating Releases

### Automatic Release Process

1. **Create and push a tag:**
   ```bash
   git tag v2.0.0
   git push origin v2.0.0
   ```

2. **GitHub Actions will:**
   - Build Docker image with version tag
   - Create GitHub release
   - Upload deployment assets
   - Extract changelog notes

### Manual Release

1. Go to **Releases** → **Create a new release**
2. Choose tag version (or create new)
3. Generate release notes or write custom ones
4. Publish release

## 🔧 Customizing Deployment

### Option 1: Server Deployment

Uncomment and configure in `.github/workflows/deploy.yml`:

```yaml
- name: Deploy to server
  uses: appleboy/ssh-action@v0.1.7
  with:
    host: ${{ secrets.DEPLOY_HOST }}
    username: ${{ secrets.DEPLOY_USER }}
    key: ${{ secrets.DEPLOY_KEY }}
    script: |
      cd /path/to/your/deployment
      docker-compose -f docker-compose-prod.yml pull
      docker-compose -f docker-compose-prod.yml up -d --remove-orphans
```

### Option 2: Webhook Deployment

Uncomment and configure webhook section:

```yaml
- name: Trigger deployment webhook
  run: |
    curl -X POST "${{ secrets.DEPLOY_WEBHOOK_URL }}" \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer ${{ secrets.DEPLOY_WEBHOOK_TOKEN }}" \
      -d '{"image_tag": "${{ steps.image_tag.outputs.tag }}", "service": "remna-telegram-bot"}'
```

## 📊 Monitoring

### Build Status

- Check **Actions** tab for workflow status
- Failed builds will show error details
- Successful builds create packages and releases

### Package Status

- **Packages** tab shows available Docker images
- Download statistics and vulnerability scans
- Version history and tags

### Security

GitHub automatically:
- ✅ Scans Docker images for vulnerabilities
- ✅ Provides security advisories
- ✅ Updates dependency alerts

## 🛠️ Development Workflow

### Recommended Git Flow

1. **Feature Development:**
   ```bash
   git checkout -b feature/new-feature
   # Make changes
   git commit -m "Add new feature"
   git push origin feature/new-feature
   # Create PR
   ```

2. **Testing:**
   - PR triggers build workflow
   - Review Docker build logs
   - Test functionality

3. **Release:**
   ```bash
   git checkout main
   git merge feature/new-feature
   git tag v2.1.0
   git push origin main --tags
   ```

### Branch Protection

Recommended settings for `main` branch:
1. **Settings** → **Branches**
2. Add rule for `main`
3. Configure:
   - ✅ Require a pull request before merging
   - ✅ Require status checks to pass
   - ✅ Require branches to be up to date
   - ✅ Include administrators

## 🚨 Troubleshooting

### Common Issues

#### Package Registry Permission Denied
```bash
# Ensure GITHUB_TOKEN has packages:write permission
# Check workflow permissions in repository settings
```

#### Docker Build Failures
```bash
# Check Dockerfile syntax
# Verify all COPY paths exist
# Check for large files in context
```

#### Workflow Not Triggering
```bash
# Verify workflow file syntax (YAML)
# Check trigger conditions (branch names, paths)
# Ensure workflows are enabled in repository
```

### Debug Steps

1. **Check Actions logs** - Detailed error information
2. **Validate YAML** - Use online YAML validators
3. **Test locally** - Run Docker builds locally first
4. **Check permissions** - Verify repository and package permissions

## 📞 Support

### GitHub Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitHub Packages Documentation](https://docs.github.com/en/packages)
- [Container Registry Guide](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)

### Community

- GitHub Issues for project-specific problems
- GitHub Discussions for questions and ideas
- Stack Overflow for general GitHub Actions questions

---

**🎯 After completing this setup, your repository will have:**
- ✅ Automated Docker image builds
- ✅ Multi-architecture support
- ✅ Automated releases with assets
- ✅ Production-ready deployment pipeline
- ✅ Security scanning and monitoring
