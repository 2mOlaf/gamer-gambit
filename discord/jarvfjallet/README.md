# Jarvfjallet - Discord Bot

Jarvfjallet is a general-purpose Discord bot for gaming communities.

## Status

🚧 **Currently inactive** - This bot is not currently deployed or in active development.

## Files

- **`node/`** - Node.js bot application code
- **`Dockerfile`** - Container configuration
- **`docker-compose.yaml`** - Local development setup
- **`run.sh`** - Bot startup script

## Development

### Local Setup
```bash
cd node
npm install
# Configure auth.json with your Discord bot token
npm start
```

### Docker Setup
```bash
docker-compose up -d
```

## Configuration

Copy `node/auth.json.example` to `node/auth.json` and add your Discord bot token.

## Future Plans

This bot is planned for future development as a general gaming bot to complement Kallax's board gaming focus.

---

**Note**: Currently, focus is on the [Kallax bot](../kallax/) which is actively maintained and deployed.
