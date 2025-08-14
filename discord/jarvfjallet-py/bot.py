# Jarvfjallet Discord Bot - Itch.io Game Assignment Bot
# Modernized Python version based on Kallax architecture

import asyncio
import logging
import os
import time
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
from aiohttp import web
import aiohttp

from utils.database import Database

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('jarvfjallet.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Global bot instance for health check
bot_instance = None

class JarvajalletBot(commands.Bot):
    """Main bot class for Jarvfjallet - The Itch.io Game Assignment Bot"""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        
        super().__init__(
            command_prefix=os.getenv('COMMAND_PREFIX', '!'),
            intents=intents,
            description="Jarvfjallet - Your Itch.io Game Assignment Bot"
        )
        
        self.database = None
        self.synced = False
        self.startup_time = time.time()
        self.health_server = None
        self.essential_cogs = ['game_assignment']  # Essential cogs loaded at startup
        self.lazy_cogs = []  # No lazy loading needed for this simple bot
        self._cogs_loaded = set()
        
    async def setup_hook(self):
        """Setup hook called when bot is starting up"""
        # Initialize database with lazy loading
        db_path = os.getenv('DATABASE_PATH', './data/jarvfjallet.db')
        self.database = Database(db_path)
        
        # Import existing JSON data if database is empty
        await self.import_legacy_data()
        
        # Start health check server
        await self.start_health_server()
        
        # Load essential cogs at startup
        await self.load_essential_cogs()
        
        logger.info(f"Bot setup completed successfully in {time.time() - self.startup_time:.2f}s")
        
    async def import_legacy_data(self):
        """Import data from legacy JSON files if database is empty"""
        try:
            if not await self.database.has_games():
                # Try to import from the production JSON file
                json_file = Path('./data/itch_pak.json')
                if json_file.exists():
                    logger.info("Importing legacy game data from JSON file...")
                    await self.database.import_from_json(str(json_file))
                    logger.info("Legacy data import completed")
                else:
                    logger.warning("No legacy JSON file found, starting with empty database")
        except Exception as e:
            logger.error(f"Error importing legacy data: {e}")
            
    async def start_health_server(self):
        """Start health check HTTP server"""
        try:
            app = web.Application()
            app.router.add_get('/health', self.health_check)
            app.router.add_get('/metrics', self.metrics)
            
            runner = web.AppRunner(app)
            await runner.setup()
            
            port = int(os.getenv('HEALTH_CHECK_PORT', '8080'))
            site = web.TCPSite(runner, '0.0.0.0', port)
            await site.start()
            
            self.health_server = runner
            logger.info(f"Health check server started on port {port}")
        except Exception as e:
            logger.warning(f"Failed to start health check server: {e}")
            
    async def health_check(self, request):
        """Health check endpoint"""
        uptime = time.time() - self.startup_time
        status = {
            'status': 'healthy',
            'bot_ready': self.is_ready(),
            'uptime_seconds': round(uptime, 2),
            'guilds': len(self.guilds) if self.is_ready() else 0,
            'latency_ms': round(self.latency * 1000, 2) if self.is_ready() else None,
            'cogs_loaded': list(self._cogs_loaded),
            'database_ready': self.database._initialized if self.database else False
        }
        return web.json_response(status)
        
    async def metrics(self, request):
        """Metrics endpoint for monitoring"""
        if not self.is_ready():
            return web.json_response({'error': 'Bot not ready'}, status=503)
            
        # Get game statistics from database
        game_stats = await self.database.get_game_stats() if self.database else {}
        
        metrics = {
            'uptime': time.time() - self.startup_time,
            'guilds': len(self.guilds),
            'commands_registered': len(self.tree.get_commands()),
            'cogs_loaded': len(self._cogs_loaded),
            'database_connections': 1 if self.database and self.database._initialized else 0,
            'total_games': game_stats.get('total_games', 0),
            'assigned_games': game_stats.get('assigned_games', 0),
            'unassigned_games': game_stats.get('unassigned_games', 0),
            'completed_reviews': game_stats.get('completed_reviews', 0)
        }
        return web.json_response(metrics)
        
    async def load_essential_cogs(self):
        """Load only essential cogs at startup for faster boot"""
        cogs_dir = Path(__file__).parent / 'cogs'
        
        for cog_name in self.essential_cogs:
            cog_file = cogs_dir / f'{cog_name}.py'
            if cog_file.exists():
                try:
                    full_cog_name = f'cogs.{cog_name}'
                    await self.load_extension(full_cog_name)
                    self._cogs_loaded.add(cog_name)
                    logger.info(f"Loaded essential cog: {full_cog_name}")
                except Exception as e:
                    logger.error(f"Failed to load essential cog {full_cog_name}: {e}")
                    
    async def on_ready(self):
        """Called when bot is ready"""
        logger.info(f'{self.user} has connected to Discord!')
        logger.info(f'Bot is in {len(self.guilds)} guilds')
        
        # List all guilds for debugging
        for guild in self.guilds:
            logger.info(f'Guild: {guild.name} (ID: {guild.id})')
        
        # Sync slash commands (only once)
        if not self.synced:
            try:
                # Log all commands in the tree
                all_commands = self.tree.get_commands()
                logger.info(f"Commands in tree before sync: {len(all_commands)}")
                for cmd in all_commands:
                    logger.info(f"  - {cmd.name}: {cmd.description}")
                
                guild_id = os.getenv('DISCORD_GUILD_ID')
                if guild_id:
                    # Sync to specific guild (instant)
                    guild = discord.Object(id=int(guild_id))
                    synced = await self.tree.sync(guild=guild)
                    logger.info(f"Synced {len(synced)} command(s) to guild {guild_id}")
                    for cmd in synced:
                        logger.info(f"  Synced: {cmd.name}")
                else:
                    # Sync globally (takes up to 1 hour)
                    synced = await self.tree.sync()
                    logger.info(f"Synced {len(synced)} command(s) globally (may take up to 1 hour to appear)")
                    for cmd in synced:
                        logger.info(f"  Synced: {cmd.name}")
                self.synced = True
            except Exception as e:
                logger.error(f"Failed to sync commands: {e}")
        
        # Set bot activity
        activity = discord.Game(name="Itch.io Games | /hit for random game")
        await self.change_presence(activity=activity)
        
    async def on_command_error(self, ctx, error):
        """Global command error handler"""
        if isinstance(error, commands.CommandNotFound):
            return
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Missing required argument: {error.param}")
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"⏰ Command on cooldown. Try again in {error.retry_after:.2f} seconds.")
        else:
            logger.error(f"Command error: {error}")
            await ctx.send("❌ An unexpected error occurred. Please try again.")

async def main():
    """Main function to start the bot"""
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        logger.error("DISCORD_TOKEN not found in environment variables")
        return
        
    bot = JarvajalletBot()
    global bot_instance
    bot_instance = bot
    
    try:
        logger.info("Starting Jarvfjallet Discord Bot...")
        start_time = time.time()
        await bot.start(token)
    except KeyboardInterrupt:
        logger.info("Bot shutdown requested")
    except Exception as e:
        logger.error(f"Bot startup failed: {e}")
    finally:
        logger.info("Cleaning up resources...")
        
        # Close health server
        if bot.health_server:
            try:
                await bot.health_server.cleanup()
                logger.info("Health check server stopped")
            except Exception as e:
                logger.warning(f"Error stopping health server: {e}")
        
        # Close database
        if bot.database:
            try:
                await bot.database.close()
                logger.info("Database connection closed")
            except Exception as e:
                logger.warning(f"Error closing database: {e}")
                
        # Close bot
        try:
            await bot.close()
            logger.info("Bot closed successfully")
        except Exception as e:
            logger.warning(f"Error closing bot: {e}")

if __name__ == "__main__":
    asyncio.run(main())
