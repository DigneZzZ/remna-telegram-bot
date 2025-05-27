# Remnawave Admin Bot

Professional Telegram bot for managing Remnawave VPN proxy service with production-ready features and mobile-optimized interface.

[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)](https://github.com/dignezzz/remna-telegram-bot/pkgs/container/remna-telegram-bot)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg?style=for-the-badge)](LICENSE)

## 👤 Author

This bot was created by the author of 
- [openode.xyz](https://openode.xyz)
- [neonode.cc](https://neonode.cc)
- [Github - DigneZzZ](https://github.com/DigneZzZ)

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

1. **Create project directory and download configuration**
   ```bash
   sudo mkdir -p /opt/remna-bot
   cd /opt/remna-bot
   curl -o .env https://raw.githubusercontent.com/dignezzz/remna-telegram-bot/main/.env.example
   curl -o docker-compose.yml https://raw.githubusercontent.com/dignezzz/remna-telegram-bot/main/docker-compose-prod.yml
   ```

2. **Configure environment**
   ```bash
   # Edit .env with your actual values
   nano .env
   ```

3. **Deploy the bot**
   ```bash
   docker compose up -d
   ```

4. **View logs**
   ```bash
   docker compose logs -f
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
   nano .env
   ```

3. **Run**
   ```bash
   python main.py
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

### 🎛️ Dashboard Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `DASHBOARD_SHOW_SYSTEM_STATS` | Show CPU, RAM, uptime info | `true` |
| `DASHBOARD_SHOW_SERVER_INFO` | Show server/inbound statistics | `true` |
| `DASHBOARD_SHOW_USERS_COUNT` | Show user count and status breakdown | `true` |
| `DASHBOARD_SHOW_NODES_COUNT` | Show node count and online status | `true` |
| `DASHBOARD_SHOW_TRAFFIC_STATS` | Show real-time traffic monitoring | `true` |
| `DASHBOARD_SHOW_UPTIME` | Show system uptime information | `true` |

### 🔍 Search Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `ENABLE_PARTIAL_SEARCH` | Allow partial name matching in search | `true` |
| `SEARCH_MIN_LENGTH` | Minimum characters for search queries | `2` |



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

### 🔍 Enhanced Search Features
- **Partial Name Search** - Find users by partial username matches
- **Description Search** - Search within user descriptions  
- **Telegram ID Search** - Direct search by Telegram user ID
- **Simplified Interface** - Reduced from 6 to 3 intuitive search options
- **Multi-result Display** - Smart handling of multiple search results

### ⚙️ Configurable Dashboard
- **System Statistics** - Toggle CPU, RAM, uptime display
- **Server Information** - Control server and node statistics visibility
- **Traffic Monitoring** - Enable/disable real-time traffic stats
- **User Analytics** - Show/hide user count and status breakdown
- **Customizable Sections** - Fine-tune what information appears on main screen

### API Compatibility
- ✅ **Remnawave API v1.6.5** - Full compatibility verified
- ✅ **59 API Endpoints** - All methods tested and working
- ✅ **Async Architecture** - Non-blocking operations for better performance


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

**Version**: 2.0  
**Last Updated**: May 2025  

