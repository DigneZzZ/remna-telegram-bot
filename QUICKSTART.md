# 🚀 Quick Start Guide - Remnawave Admin Bot

## Prerequisites
- Python 3.8 or higher
- Telegram Bot Token (from @BotFather)
- Remnawave API access credentials

## 1. Setup Environment

### Clone Repository
```bash
git clone <repository-url>
cd remnawave-admin-bot
```

### Create Virtual Environment (Recommended)
```bash
python -m venv venv

# Activate virtual environment
# Windows:
.\venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

## 2. Configuration

### Create Environment File
```bash
cp .env.example .env
```

### Edit Configuration
Open `.env` file and fill in your credentials:
```env
API_BASE_URL=https://your-remnawave-api.com
REMNAWAVE_API_TOKEN=your_actual_api_token
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
ADMIN_USER_IDS=your_telegram_user_id
```

### Get Your Telegram User ID
1. Message @userinfobot on Telegram
2. Copy your user ID number
3. Add it to `ADMIN_USER_IDS` in .env file

## 3. Run the Bot

### Development Mode
```bash
python main.py
```

### Production with Docker
```bash
docker compose up -d
```

## 4. First Use

1. **Start the bot** - Send `/start` to your bot
2. **Main menu** - You'll see the main control panel
3. **Test functionality** - Try browsing users or nodes
4. **Enjoy** - The mobile-optimized interface!

## 🔧 Troubleshooting

### Common Issues

**Bot not responding**
- Check TELEGRAM_BOT_TOKEN is correct
- Verify your user ID is in ADMIN_USER_IDS
- Check bot logs for errors

**API connection failed**
- Verify API_BASE_URL is correct and reachable
- Check REMNAWAVE_API_TOKEN is valid
- Ensure API server is running

**Permission denied**
- Make sure your Telegram user ID is in ADMIN_USER_IDS
- Check if the bot token has proper permissions

### Check Logs
```bash
# If running directly
python main.py

# If running with Docker
docker compose logs -f
```

## 📱 Mobile Usage Tips

- **Use pagination** - Navigate through long lists with page buttons
- **Tap names** - Click on user/server names instead of UUIDs  
- **Quick actions** - Most common actions are one tap away
- **Search smartly** - Use partial names for faster finding

## 🎯 Next Steps

1. **Explore features** - Try user management, server monitoring
2. **Customize settings** - Adjust pagination sizes if needed
3. **Set up monitoring** - Configure log collection for production
4. **Backup configuration** - Save your .env file securely

---

Need help? Check the main [README.md](README.md) for detailed documentation.
