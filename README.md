# Remnawave Admin Bot

Professional Telegram bot for managing Remnawave VPN proxy service with production-ready features and mobile-optimized interface.

[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)](https://github.com/dignezzz/remna-telegram-bot/pkgs/container/remna-telegram-bot)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg?style=for-the-badge)](LICENSE)

## ✨ Features

### 🎛️ Complete Management Suite
- 👥 **User Management** - Full lifecycle with smart search and bulk operations
- 🖥️ **Server Management** - Node control, monitoring, restart, and statistics  
- 📊 **System Statistics** - Real-time server metrics with Docker-aware resource monitoring
- 🌐 **Host Management** - Connection endpoint configuration
- 🔌 **Inbound Management** - Color-coded protocol status with enhanced UI
- 🔄 **Bulk Operations** - Mass user operations (reset, delete, update)
- 📜 **Certificate Management** - Easy certificate display and node security management
- 📈 **Real-time Traffic** - Live download/upload speeds and bandwidth monitoring

### 📱 Mobile-First Interface
- **Smart Navigation** - User-friendly name-based selections
- **Optimized Pagination** - 6-8 items per page for mobile screens
- **Multi-Search Options** - Search by username, UUID, email, Telegram ID, tags
- **Real-time Updates** - Live traffic statistics and server status
- **Responsive Design** - Perfect for both mobile and desktop Telegram

### 🚀 Production Features
- **Docker Ready** - Multi-architecture support (AMD64/ARM64)
- **Health Monitoring** - Built-in health checks and logging
- **Security First** - Admin authorization and secure API communication
- **Auto-Recovery** - Robust error handling and graceful failures
- **Performance Optimized** - Async operations and efficient API calls

## 🔧 Quick Start

### Docker Deployment (Recommended)

1. **Download production configuration**
   ```bash
   curl -O https://raw.githubusercontent.com/dignezzz/remna-telegram-bot/main/docker-compose-prod.yml
   curl -O https://raw.githubusercontent.com/dignezzz/remna-telegram-bot/main/.env.example
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your actual values
   ```

3. **Deploy**
   ```bash
   docker compose -f docker-compose-prod.yml up -d
   ```

### Manual Installation

1. **Clone and setup**
   ```bash
   git clone https://github.com/dignezzz/remna-telegram-bot.git
   cd remna-telegram-bot
   pip install -r requirements.txt
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

3. **Run**
   ```bash
   python main.py
   ```

#### Using Deployment Scripts

**Windows (PowerShell):**
```powershell
# Deploy latest version
.\deploy.ps1

# Deploy specific version
.\deploy.ps1 -Tag "v2.0.0"
```

**Linux/macOS (Bash):**
```bash
# Make executable and deploy
chmod +x deploy.sh
./deploy.sh latest
```

#### Using Makefile
```bash
# Development
make setup    # Setup environment
make dev      # Start development container

# Production
make prod-pull    # Pull latest image
make prod-deploy  # Deploy to production
make prod-logs    # View logs
```

## 🐳 Docker Images

Images are automatically built and published to GitHub Container Registry:

- **Registry**: `ghcr.io/dignezzz/remna-telegram-bot`
- **Tags**: `latest`, `v2.0.0`, `main`, etc.
- **Architectures**: AMD64, ARM64
- **Security**: Non-root user, minimal attack surface

### Image Features
- ✅ Multi-stage build for smaller size
- ✅ Non-root user for security
- ✅ Health checks included
- ✅ Optimized for production
- ✅ Comprehensive logging

## 🔧 Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `API_BASE_URL` | Base URL for the Remnawave API | `https://api.remnawave.com` |
| `REMNAWAVE_API_TOKEN` | Your Remnawave API token | `your_secret_token` |
| `TELEGRAM_BOT_TOKEN` | Your Telegram bot token | `123456:ABC-DEF1234...` |
| `ADMIN_USER_IDS` | Comma-separated admin user IDs | `123456789,987654321` |

## 🔧 Troubleshooting

### Bot Not Responding?

If your bot starts but doesn't respond to messages, the most common issue is **incorrect ADMIN_USER_IDS configuration**.

#### Quick Fix:
1. **Get your Telegram ID**:
   ```bash
   # Temporarily run ID bot to get your Telegram ID
   echo "TELEGRAM_BOT_TOKEN=your_bot_token" > .env
   docker compose -f docker-compose-debug.yml --profile id-bot up --build
   ```
   Send any message to the bot - it will show your ID.

2. **Update .env file**:
   ```bash
   ADMIN_USER_IDS=your_actual_telegram_id
   ```

3. **Restart with debug logging**:
   ```bash
   docker compose -f docker-compose-debug.yml --profile debug up --build
   ```

#### Common Issues:
- ❌ **ADMIN_USER_IDS empty or wrong** - Bot rejects all users
- ❌ **Spaces in ADMIN_USER_IDS** - Use `123,456` not `123, 456`
- ❌ **Missing .env file** - Environment variables not loaded
- ❌ **Wrong Telegram ID format** - Must be numeric user ID, not @username

#### Debug Files:
- 📋 [Quick Debug Guide](docs/QUICK_DEBUG.md) - Step-by-step debugging guide
- 🔍 [Troubleshooting Guide](docs/TROUBLESHOOTING.md) - Detailed problem resolution
- 🐛 `docker-compose-debug.yml` - Debug configurations

For detailed troubleshooting, see [Troubleshooting Guide](docs/TROUBLESHOOTING.md).

## 📖 Usage Guide

### Getting Started
1. **Start the bot** - Send `/start` command to your bot
2. **Main Menu** - Navigate through intuitive menu options
3. **Search & Select** - Use name-based selections instead of UUIDs
4. **Mobile Optimized** - Enjoy paginated lists perfect for mobile devices

### 👥 User Management

#### Features
- 📋 **View Users** - Paginated list with search capabilities
- 🔍 **Smart Search** - Search by username, UUID, Telegram ID, email, or tag
- ➕ **Create Users** - Step-by-step user creation wizard
- ✏️ **Edit Details** - Modify user information with validation
- 🔄 **Status Control** - Enable/disable users instantly
- 📊 **Traffic Management** - Reset usage statistics
- 🔐 **HWID Management** - Track and manage hardware devices
- 📈 **Statistics** - View detailed user analytics

#### New Mobile Features
- **Compact Lists** - 8 users per page for easy browsing
- **Name-Based Selection** - Click on user names instead of UUIDs
- **Quick Actions** - One-tap access to common operations
- **Smart Pagination** - Navigate large user lists efficiently

### 🖥️ Node Management

#### Enhanced Features
- 📋 **Server Overview** - Real-time status with visual indicators
- 🔄 **Control Operations** - Enable, disable, restart servers (fixed endpoints)
- 📊 **Performance Metrics** - Traffic usage and online users
- 🔧 **Bulk Operations** - Manage multiple servers simultaneously
- 📜 **Certificate Display** - Easy certificate viewing and management
- 📈 **Real-time Statistics** - Enhanced stats with fallback for reliable data

#### Certificate Management
- 🔑 **One-Click Display** - View node certificates instantly
- 🔐 **Secure Access** - Direct certificate access from node menu
- 📋 **Clean Interface** - Optimized certificate presentation
- 🔄 **Quick Navigation** - Easy return to node management

#### Status Indicators
- 🟢 **Online & Active** - Server is running normally
- 🔴 **Offline/Disabled** - Server needs attention
- 📈 **Traffic Display** - Used/Total bandwidth with formatting

### 🔌 Inbound Management

#### Enhanced Features
- 📋 **Connection Points** - Manage proxy endpoints with visual status
- 🔄 **Bulk User Operations** - Add/remove from all users
- 🖥️ **Node Distribution** - Deploy to all servers
- 📊 **Usage Statistics** - Track user and node connections
- 🎨 **Color-Coded Status** - 🟢 Enabled / 🔴 Disabled visual indicators
- 🔄 **Improved UI** - Enhanced inbound selection with clear status display

#### Status Display Enhancements
- **Visual Indicators** - Clear color coding for quick status recognition
- **Smart Selection** - Default exclusion for all inbounds during node creation
- **User-Friendly Labels** - Easy-to-understand status descriptions
- **Optimized Navigation** - Streamlined inbound management workflow

#### Two View Modes
- **Simple View** - Basic information for quick overview
- **Detailed View** - Complete statistics with user/node counts

### 🔄 Bulk Operations

#### Available Operations
- 📊 **Reset All Traffic** - Clear usage statistics for all users
- 🗑️ **Cleanup Inactive** - Remove users who haven't used the service
- ⏰ **Remove Expired** - Delete users with expired subscriptions
- 🔄 **Mass Updates** - Apply changes to multiple users

#### Safety Features
- ⚠️ **Confirmation Prompts** - Prevent accidental bulk operations
- 📋 **Operation Reports** - Detailed feedback on completed actions
- 🔙 **Easy Cancellation** - Cancel operations before execution

## 🏗️ Technical Architecture

### Project Structure
```
remnawave-admin-bot/
├── main.py                    # Application entry point
├── requirements.txt           # Python dependencies
├── docker-compose.yml        # Container orchestration
├── modules/
│   ├── config.py             # Configuration constants
│   ├── api/                  # API client modules
│   │   ├── client.py         # Async HTTP client
│   │   ├── users.py          # User management API
│   │   ├── nodes.py          # Node management API
│   │   ├── inbounds.py       # Inbound management API
│   │   └── ...               # Other API modules
│   ├── handlers/             # Telegram bot handlers
│   │   ├── user_handlers.py  # User interface logic
│   │   ├── node_handlers.py  # Node interface logic
│   │   └── ...               # Other handlers
│   └── utils/                # Utility modules
│       ├── selection_helpers.py  # UI helper utilities
│       ├── formatters.py         # Data formatting
│       └── auth.py               # Authentication
```

### Key Technologies
- **Python 3.8+** - Core language
- **python-telegram-bot** - Telegram API interface
- **aiohttp** - Async HTTP client for API calls
- **Docker** - Containerized deployment

### API Compatibility
- ✅ **Remnawave API v1.6.2** - Full compatibility verified
- ✅ **59 API Endpoints** - All methods tested and working
- ✅ **Async Architecture** - Non-blocking operations for better performance

## 🚀 Development & Deployment

### Development Setup
```bash
# Clone and setup
git clone <repository>
cd remnawave-admin-bot
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials

# Run in development
python main.py
```

### Production Deployment
```bash
# Using Docker
docker compose up -d

# Check logs
docker compose logs -f

# Update
git pull
docker compose down
docker compose up -d --build
```

## 📊 Performance Features

### Mobile Optimization
- **Compact Pagination** - 6-8 items per page
- **Fast Loading** - Lazy loading with efficient queries
- **Memory Efficient** - Minimal data caching
- **Responsive** - Works on all screen sizes

### Scalability
- **Async Operations** - Handle multiple users simultaneously
- **Efficient API Usage** - Optimized request patterns
- **Error Recovery** - Graceful handling of API failures
- **Logging** - Comprehensive monitoring and debugging

## 🔒 Security & Access Control

### Authentication
- **Telegram User ID** verification
- **Admin-only Access** - Configurable admin user list
- **API Token** security
- **Environment Variables** - Secure credential storage

### Best Practices
- No sensitive data in code
- Secure API communication
- Input validation and sanitization
- Error handling without data exposure

## 📈 Monitoring & Logging

### Available Logs
- **API Requests** - All Remnawave API interactions
- **User Actions** - Telegram bot usage tracking
- **Error Tracking** - Detailed error information
- **Performance Metrics** - Response times and usage patterns

### Log Configuration
Logs are structured for easy parsing and monitoring:
```python
# Example log entry
2025-05-26 10:30:45 - INFO - User 123456789 listed users (page 1)
2025-05-26 10:30:46 - DEBUG - API call: GET /users (200ms)
```

## 🤝 Contributing

### Development Guidelines
1. Follow existing code structure
2. Add tests for new features  
3. Update documentation
4. Use type hints
5. Follow PEP 8 style guide

### Feature Requests
- Open an issue with detailed description
- Include use case and expected behavior
- Consider mobile device compatibility

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Remnawave Team** - For the excellent VPN service API
- **python-telegram-bot** - For the robust Telegram bot framework
- **Community Contributors** - For feedback and improvements

---

## 📚 Documentation

### Development & Deployment
- 📋 [Quick Start Guide](docs/QUICKSTART.md) - Fast setup instructions
- 🚀 [Deployment Guide](docs/DEPLOYMENT.md) - Production deployment
- ✅ [Deployment Checklist](docs/DEPLOYMENT_CHECKLIST.md) - Pre-deployment verification
- 🐳 [Docker Setup Guide](docs/DOCKER_CICD_SUMMARY.md) - Container deployment details
- 🔧 [Docker Fixes](docs/DOCKER_COMPOSE_FIXES.md) - Common Docker issues

### Project Management
- 📝 [Project Status](docs/PROJECT_STATUS.md) - Current development status
- 📑 [Start Here](docs/START_HERE.md) - New developer onboarding
- 📈 [Changelog](docs/CHANGELOG.md) - Version history and updates
- 🎯 [UI Improvements Report](docs/UI_IMPROVEMENTS_REPORT.md) - Recent UI enhancements
- ✅ [Final Completion Report](docs/FINAL_COMPLETION_REPORT.md) - Project completion summary

### Technical References
- 📊 [Current Status](docs/CURRENT_STATUS.md) - Real-time project state
- 🔍 [Diagnosis Report](docs/DIAGNOSIS_COMPLETE.md) - Technical analysis
- ⚙️ [GitHub Setup](docs/GITHUB_SETUP.md) - Repository configuration

## 📞 Support

For issues, questions, or feature requests:
- 📋 **Issues**: Use GitHub Issues for bug reports
- 💬 **Discussions**: Community support and questions
- 📖 **Documentation**: Check this README and code comments

**Version**: 2.0  
**Last Updated**: May 2025  
**Compatibility**: Remnawave API v1.6.2
