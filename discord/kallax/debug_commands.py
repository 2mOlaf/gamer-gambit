#!/usr/bin/env python3
"""
Debug script to check Discord slash command registration and help troubleshoot command visibility issues.
"""

import asyncio
import discord
import os
from discord.ext import commands
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def debug_commands():
    """Debug Discord slash command registration"""
    
    # Get bot token
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print("❌ DISCORD_TOKEN not found in environment variables")
        return
    
    # Create minimal bot instance for testing
    intents = discord.Intents.default()
    intents.message_content = True
    
    bot = commands.Bot(command_prefix='!debug_', intents=intents)
    
    @bot.event
    async def on_ready():
        print(f"🤖 Bot connected as {bot.user}")
        print(f"📊 Bot is in {len(bot.guilds)} guilds:")
        
        for guild in bot.guilds:
            print(f"   - {guild.name} (ID: {guild.id})")
        
        # Check app commands in tree
        print(f"\n🌳 Commands in tree: {len(bot.tree.get_commands())}")
        all_commands = bot.tree.get_commands()
        for cmd in all_commands:
            print(f"   - {cmd.name}: {cmd.description}")
        
        # Check if guild-specific sync is configured
        guild_id = os.getenv('DISCORD_GUILD_ID')
        print(f"\n🏰 Guild ID in env: {guild_id}")
        
        if guild_id:
            try:
                guild = discord.Object(id=int(guild_id))
                # Get synced commands for guild
                synced_commands = await bot.tree.fetch_commands(guild=guild)
                print(f"📋 Synced commands in guild {guild_id}: {len(synced_commands)}")
                for cmd in synced_commands:
                    print(f"   - {cmd.name}: {cmd.description}")
            except Exception as e:
                print(f"❌ Error checking guild commands: {e}")
        else:
            try:
                # Get global synced commands
                synced_commands = await bot.tree.fetch_commands()
                print(f"🌍 Global synced commands: {len(synced_commands)}")
                for cmd in synced_commands:
                    print(f"   - {cmd.name}: {cmd.description}")
            except Exception as e:
                print(f"❌ Error checking global commands: {e}")
        
        # Load and check our cogs
        print(f"\n📦 Loading cogs for command inspection...")
        try:
            from cogs.game_search import GameSearchCog
            from cogs.user_profiles import UserProfilesCog
            
            # Add cogs
            await bot.add_cog(GameSearchCog(bot))
            await bot.add_cog(UserProfilesCog(bot))
            
            print(f"✅ Cogs loaded successfully")
            print(f"🌳 Commands in tree after cog loading: {len(bot.tree.get_commands())}")
            
            updated_commands = bot.tree.get_commands()
            for cmd in updated_commands:
                print(f"   - {cmd.name}: {cmd.description}")
                
        except Exception as e:
            print(f"❌ Error loading cogs: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"\n🔄 Attempting command sync...")
        
        try:
            if guild_id:
                # Sync to specific guild (instant)
                guild = discord.Object(id=int(guild_id))
                synced = await bot.tree.sync(guild=guild)
                print(f"✅ Synced {len(synced)} commands to guild {guild_id}")
                for cmd in synced:
                    print(f"   - {cmd.name}")
            else:
                # Sync globally (takes up to 1 hour)
                synced = await bot.tree.sync()
                print(f"✅ Synced {len(synced)} commands globally")
                for cmd in synced:
                    print(f"   - {cmd.name}")
                    
        except Exception as e:
            print(f"❌ Error syncing commands: {e}")
            import traceback
            traceback.print_exc()
        
        # Close bot
        await bot.close()
    
    try:
        await bot.start(token)
    except Exception as e:
        print(f"❌ Error starting bot: {e}")

if __name__ == "__main__":
    print("🔍 Discord Command Debug Tool")
    print("=" * 50)
    asyncio.run(debug_commands())
