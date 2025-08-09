# Kallax - Discord Gaming Bot

Kallax is a comprehensive Discord bot designed for gaming communities, with a focus on board gaming through BoardGameGeek (BGG) integration. Named after the popular IKEA shelf system beloved by board gamers for organizing their collections.

## Features

### 🎲 Game Search & Discovery
- **Game Search**: Search BoardGameGeek's extensive database of board games
- **Detailed Game Info**: Rich embeds with images, ratings, player counts, complexity, and descriptions
- **Random Game**: Discover new games from curated popular selections
- **Interactive Selection**: React-based game selection from search results

### 👤 User Profile Management
- **Multi-Platform Profiles**: Support for BGG, Steam, and Xbox profiles
- **Profile Validation**: Automatic BGG username validation
- **Easy Setup**: Simple commands to set and display gaming profiles

### 📚 Collection Display
- **BGG Collections**: Display user collections with pagination
- **Multiple Collection Types**: Own, Wishlist, For Trade, Want to Buy
- **Active Links**: Direct links to BGG collection pages
- **Collection Summary**: Overview with counts for each collection type
- **User Ratings**: Show personal ratings alongside games

### 🎮 Gaming History
- **Recent Plays**: Display recent game plays from BGG
- **Detailed Play Info**: Players, scores, duration, location, and comments
- **Play Statistics**: Track gaming activity and patterns

### 🤖 Bot Features
- **Slash Commands**: Modern Discord command interface
- **Rich Embeds**: Beautiful, informative message displays
- **Rate Limiting**: Proper API rate limiting to respect BGG's servers
- **Error Handling**: Graceful error handling with user-friendly messages
- **Caching**: Game data caching for improved performance

## Planned Features

### 📊 Weekly Stats (Coming Soon)
- Automated weekly gaming statistics posts
- Per-user configuration for stats channels
- Gaming trends and insights

### 🎯 Enhanced Game Discovery
- Advanced filtering for random game selection
- Recommendation engine based on user preferences
- Game night planning tools

## Setup

### Prerequisites
- Python 3.8 or higher
- Discord bot token (create at https://discord.com/developers/applications)
- Discord server with appropriate permissions

### Installation

1. **Clone the repository**
   ```bash
   cd "\\urdarbrunnr.gradin.lan\Projects\GitHub\2mOlaf\gamer-gambit\discord\kallax"
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and add your Discord bot token and other configuration.

4. **Run the bot**
   ```bash
   python bot.py
   ```

### Environment Configuration

Copy `.env.example` to `.env` and configure:

```env
# Required
DISCORD_TOKEN=your_discord_bot_token_here

# Optional
DISCORD_GUILD_ID=your_guild_id_here
DATABASE_PATH=./data/kallax.db
COMMAND_PREFIX=!
```

## Commands

### Game Search
- `!search <game name>` - Search for board games
- `!random` - Get a random popular board game

### User Profiles  
- `!profile` - Show your gaming profile
- `!profile set <platform> <username>` - Set platform username
- `!profile show [@user]` - Show another user's profile

### Collections
- `!collection [username] [type]` - Show BGG collection
- `!plays [username] [limit]` - Show recent plays

### Available Platforms
- **bgg**: BoardGameGeek username
- **steam**: Steam ID
- **xbox**: Xbox Gamertag

### Collection Types
- **own**: Games you own
- **wishlist**: Games on your wishlist  
- **fortrade**: Games for trade
- **want**: Games you want to buy

## Bot Permissions

The bot requires the following Discord permissions:
- Send Messages
- Use External Emojis
- Add Reactions
- Embed Links
- Read Message History

## Project Structure

```
kallax/
├── bot.py              # Main bot entry point
├── requirements.txt    # Python dependencies
├── .env.example       # Environment configuration template
├── data/              # Database and cache files
├── cogs/              # Discord command modules
│   ├── game_search.py # Game search functionality
│   └── user_profiles.py # User profile management
└── utils/             # Utility modules
    ├── database.py    # Database operations
    └── bgg_api.py     # BoardGameGeek API client
```

## BGG API Integration

Kallax integrates with BoardGameGeek's XML API v2 to provide:
- Game search and detailed information
- User collection data
- Play history and statistics
- Proper rate limiting and error handling

## Database

Uses SQLite for local data storage:
- User profiles and gaming platform links
- Game data caching for improved performance
- Server configuration settings
- Future: Play tracking and statistics

## Contributing

This is a personal project, but suggestions and feedback are welcome!

## License

This project is for personal/community use. BoardGameGeek data is used according to their terms of service.

## Acknowledgments

- BoardGameGeek for their excellent API and game database
- The board gaming community for inspiration
- IKEA for the Kallax shelf system that inspired the name 📦
