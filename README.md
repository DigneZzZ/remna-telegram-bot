# Remnawave Admin Bot

Telegram bot for managing Remnawave VPN proxy service with enhanced mobile-friendly interface.

## ✨ Features

### Core Management
- 👥 **User Management** - Complete lifecycle management with smart search
- 🖥️ **Node Management** - Server monitoring and control
- 📊 **System Statistics** - Real-time performance metrics
- 🌐 **Host Management** - Host configuration and monitoring
- 🔌 **Inbound Management** - Connection endpoint management
- 🔄 **Bulk Operations** - Mass user management operations
- 🔐 **HWID Device Management** - Hardware ID device tracking

### 📱 Mobile-Optimized Interface
- **User-Friendly Navigation** - Name-based selections instead of technical UUIDs
- **Smart Pagination** - Compact lists optimized for mobile screens
- **Intuitive Search** - Multiple search options with auto-completion
- **Responsive Design** - Optimized for both mobile and desktop Telegram clients
- **Fast Performance** - Efficient loading with lazy pagination

## 🚀 Recent Updates (v2.0)

### Major UI/UX Improvements
- ✅ **SelectionHelper System** - Universal pagination and selection interface
- ✅ **Mobile-First Design** - Compact lists with 6-8 items per page
- ✅ **Smart Callbacks** - User-friendly name-based navigation
- ✅ **Enhanced Error Handling** - Better error messages and recovery
- ✅ **Unified Interface** - Consistent design across all modules
- ✅ **CI/CD Pipeline** - Automated Docker builds and deployment
- ✅ **Multi-Architecture** - AMD64 and ARM64 Docker images
- ✅ **Production Ready** - Complete deployment infrastructure

### Technical Improvements  
- ✅ **Full Async/Await** - Complete migration from synchronous to asynchronous operations
- ✅ **API Compatibility** - 100% compatibility with Remnawave API v1.6.2 (59 endpoints verified)
- ✅ **Improved Performance** - aiohttp client for better concurrency
- ✅ **Better Logging** - Enhanced debugging and monitoring capabilities

## 📋 Installation

### Prerequisites
- Python 3.8+
- Telegram Bot Token
- Remnawave API access

### Quick Setup
1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd remnawave-admin-bot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   Create a `.env` file with your credentials:
   ```env
   API_BASE_URL=https://your-remnawave-api.com
   REMNAWAVE_API_TOKEN=your_api_token_here
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   ADMIN_USER_IDS=123456789,987654321
   ```

4. **Run the bot**
   ```bash
   python main.py
   ```

### Docker Deployment

#### Development
```bash
# Clone and setup
git clone https://github.com/dignezzz/remna-telegram-bot.git
cd remna-telegram-bot
cp .env.example .env
# Edit .env with your credentials

# Build and run
docker-compose up -d
```

#### Production (from GHCR)
```bash
# Download production files
curl -O https://raw.githubusercontent.com/dignezzz/remna-telegram-bot/main/docker-compose-prod.yml
curl -O https://raw.githubusercontent.com/dignezzz/remna-telegram-bot/main/.env.production

# Setup environment
cp .env.production .env
# Edit .env with your credentials

# Deploy
docker compose -f docker-compose-prod.yml up -d
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

#### Features
- 📋 **Server Overview** - Real-time status with visual indicators
- 🔄 **Control Operations** - Enable, disable, restart servers
- 📊 **Performance Metrics** - Traffic usage and online users
- 🔧 **Bulk Operations** - Manage multiple servers simultaneously

#### Status Indicators
- 🟢 **Online & Active** - Server is running normally
- 🔴 **Offline/Disabled** - Server needs attention
- 📈 **Traffic Display** - Used/Total bandwidth with formatting

### 🔌 Inbound Management

#### Features
- 📋 **Connection Points** - Manage proxy endpoints
- 🔄 **Bulk User Operations** - Add/remove from all users
- 🖥️ **Node Distribution** - Deploy to all servers
- 📊 **Usage Statistics** - Track user and node connections

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
docker-compose up -d

# Check logs
docker-compose logs -f

# Update
git pull
docker-compose down
docker-compose up -d --build
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

## 📞 Support

For issues, questions, or feature requests:
- 📋 **Issues**: Use GitHub Issues for bug reports
- 💬 **Discussions**: Community support and questions
- 📖 **Documentation**: Check this README and code comments

**Version**: 2.0  
**Last Updated**: May 2025  
**Compatibility**: Remnawave API v1.6.2
