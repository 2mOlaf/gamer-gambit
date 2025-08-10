import asyncio
import logging
import os
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

from utils.database import Database

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('kallax.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class KallaxBot(commands.Bot):
    """Main bot class for Kallax - The Gaming Discord Bot"""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.members = True
        
        super().__init__(
            command_prefix=os.getenv('COMMAND_PREFIX', '!'),
            intents=intents,
            description="Kallax - Your Gaming Companion Bot"
        )
        
        self.database = None
        self.synced = False
        
    async def setup_hook(self):
        """Setup hook called when bot is starting up"""
        # Initialize database
        db_path = os.getenv('DATABASE_PATH', './data/kallax.db')
        self.database = Database(db_path)
        await self.database.initialize()
        
        # Load all cogs
        await self.load_cogs()
        
        logger.info("Bot setup completed successfully")
        
    async def load_cogs(self):
        """Load all cog modules"""
        cogs_dir = Path(__file__).parent / 'cogs'
        
        for cog_file in cogs_dir.glob('*.py'):
            if cog_file.name.startswith('_'):
                continue
                
            cog_name = f'cogs.{cog_file.stem}'
            try:
                await self.load_extension(cog_name)
                logger.info(f"Loaded cog: {cog_name}")
            except Exception as e:
                logger.error(f"Failed to load cog {cog_name}: {e}")
                
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
        activity = discord.Game(name="Board Games | /gg-search <game>")
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
        
    bot = KallaxBot()
    
    try:
        await bot.start(token)
    except KeyboardInterrupt:
        logger.info("Bot shutdown requested")
    finally:
        await bot.close()

if __name__ == "__main__":
    asyncio.run(main())
