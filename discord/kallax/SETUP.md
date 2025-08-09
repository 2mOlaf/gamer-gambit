# Quick Setup Guide

## Getting Your Bot Running in 5 Minutes

### 1. Create Discord Bot
1. Go to https://discord.com/developers/applications
2. Click "New Application", give it a name (e.g., "Kallax")  
3. Go to "Bot" section, click "Add Bot"
4. Copy the bot token (keep this secure!)
5. Under "Privileged Gateway Intents", enable "Message Content Intent"

### 2. Invite Bot to Server
1. In your application, go to "OAuth2" > "URL Generator"
2. Select scopes: `bot`
3. Select permissions:
   - Send Messages
   - Use External Emojis  
   - Add Reactions
   - Embed Links
   - Read Message History
4. Copy the generated URL and open it to invite the bot

### 3. Configure Bot
1. Copy `.env.example` to `.env`
2. Edit `.env` and add your Discord bot token:
   ```
   DISCORD_TOKEN=your_bot_token_here
   ```

### 4. Run the Bot
**Windows:** Double-click `run_bot.bat`
**Manual:** Run `python bot.py`

### 5. Test Commands
In Discord, try:
- `!search wingspan` - Search for a game
- `!profile set bgg your_bgg_username` - Set your BGG profile
- `!collection` - View your BGG collection
- `!help` - See all commands

## Troubleshooting

### "Module not found" errors
Run: `pip install -r requirements.txt`

### Bot doesn't respond
- Check the bot token in `.env`
- Ensure bot has proper permissions
- Check bot is online in your server

### BGG API errors
- BGG API can be slow, wait a few seconds and try again
- Some BGG usernames might not exist or have private collections

## Commands Quick Reference

| Command | Description |
|---------|-------------|
| `!search <game>` | Search for board games |
| `!random` | Random popular game |
| `!profile set bgg <username>` | Set BGG username |
| `!profile` | Show your profile |
| `!collection [user] [type]` | Show BGG collection |
| `!plays [user] [limit]` | Show recent plays |

Collection types: `own`, `wishlist`, `fortrade`, `want`

## Need Help?

Check the full README.md for detailed documentation and features.
