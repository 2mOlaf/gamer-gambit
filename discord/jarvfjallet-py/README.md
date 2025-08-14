# Jarvfjallet - Discord Itch.io Game Assignment Bot

Jarvfjallet is a modernized Discord bot for assigning random games from itch.io to users for review. This is a complete Python rewrite of the original Node.js bot, following modern best practices and the architecture of the Kallax bot.

## Features

### 🎮 Game Assignment
- **Random Assignment**: Get a random unassigned game from the itch.io database
- **Status Tracking**: View your assigned games with completion status
- **User Statistics**: Detailed stats about your gaming assignments
- **Database Info**: View overall database statistics

### 🤖 Modern Bot Features
- **Slash Commands**: Modern Discord command interface
- **Rich Embeds**: Beautiful, informative message displays
- **Health Monitoring**: Built-in health check endpoints
- **Database Migration**: Automatic import from legacy JSON files
- **Error Handling**: Graceful error handling with user-friendly messages

## Commands

### Primary Commands
- `/hit` - Get a random unassigned game from itch.io
- `/status [@user]` - Check assigned games and their status (optional: check another user)
- `/mystats` - Get detailed statistics about your assigned games
- `/gameinfo` - View database statistics and how-to information

## Quick Setup

### Local Development
```bash
# Clone and setup
cd discord/jarvfjallet-py
cp .env.example .env
# Edit .env with your Discord bot token
pip install -r requirements.txt
python bot.py
```

### Production Deployment
See [k8s/README.md](k8s/README.md) for Kubernetes deployment instructions.

## Data Migration

The bot automatically imports data from legacy JSON files on first startup:
- Looks for `./data/itch_pak.json` (production data)
- Converts JSON structure to SQLite database
- Preserves all user assignments and game metadata
- Maintains backward compatibility with existing user data

## Database Schema

### Games Table
Stores all game information from itch.io:
- Game metadata (name, URL, developer, description)
- Platform support (Windows, macOS, Linux)
- Assignment status (reviewer, dates, review URLs)

### User Assignments Table
Tracks detailed assignment history:
- User ID and username
- Assignment and completion timestamps
- Review URLs and status

## Bot Permissions

The bot requires these Discord permissions:
- Send Messages
- Use Slash Commands
- Embed Links
- Send Messages in Threads (optional)

## Architecture

Built following the Kallax bot architecture pattern:
- **Modular cogs** for command organization
- **Async database operations** with aiosqlite
- **Health check endpoints** for monitoring
- **Proper logging** and error handling
- **Environment-based configuration**

## Project Structure

```
jarvfjallet-py/
├── bot.py              # Main bot entry point
├── requirements.txt    # Python dependencies
├── .env.example       # Environment configuration template
├── Dockerfile         # Container configuration
├── data/              # Database and imported data
├── cogs/              # Discord command modules
│   └── game_assignment.py # Game assignment functionality
├── utils/             # Utility modules
│   └── database.py    # Database operations and JSON import
├── k8s/               # Kubernetes deployment configs
└── .github/workflows/ # CI/CD automation
```

## Development

### Database Operations
The database utility supports:
- Lazy initialization
- Legacy JSON import
- User assignment tracking
- Game statistics
- Proper connection management

### Adding Commands
New commands can be added to the `game_assignment.py` cog or new cogs can be created following the discord.py cog pattern.

## CI/CD Pipeline

Jarvfjallet uses GitHub Actions for automated deployment:
- **Production**: Triggered on pushes to `main` branch
- **Test**: Triggered on pushes to `test` branch
- **Self-hosted runner** for Kubernetes access
- **Automatic pod restarts** with health verification

## Deployment Environments

### Production (`gamer-gambit` namespace)
- **Trigger**: Push to `main` branch
- **Image**: `ghcr.io/2molaf/jarvfjallet-discord-bot:main`
- **Secrets**: `jarvfjallet-config`

### Test (`gamer-gambit-test` namespace)
- **Trigger**: Push to `test` branch  
- **Image**: `ghcr.io/2molaf/jarvfjallet-discord-bot:test`
- **Secrets**: `jarvfjallet-config` (test namespace)

## Migration from Node.js Version

This Python version maintains full compatibility with the existing data:
1. **Automatic import** of existing `itch_pak.json` files
2. **Preserved user assignments** and game metadata
3. **Same command functionality** with improved user experience
4. **Enhanced status tracking** and statistics

## Contributing

This is a personal project, but suggestions and feedback are welcome!

## License

This project is for personal/community use.

## Acknowledgments

- Original Jarvfjallet Node.js bot concept
- Itch.io for their excellent game platform
- The indie gaming community for inspiration
- Kallax bot architecture for the modernization pattern
