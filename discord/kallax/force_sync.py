#!/usr/bin/env python3
"""
Force Discord slash command sync - Run this to manually sync all bot commands with Discord.
This should resolve missing command issues.
"""

import asyncio
import discord
import os
import sys
from discord.ext import commands
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def force_sync_commands():
    """Force sync all Discord slash commands"""
    
    print("🔄 Starting forced command sync...")
    
    # Get bot token
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("❌ DISCORD_TOKEN not found in environment variables")
        return False
    
    # Create bot instance
    intents = discord.Intents.default()
    intents.message_content = True
    
    bot = commands.Bot(command_prefix="!sync_", intents=intents)
    sync_successful = False
    
    @bot.event
    async def on_ready():
        nonlocal sync_successful
        
        print(f"🤖 Connected as {bot.user}")
        print(f"📊 Bot is in {len(bot.guilds)} guilds")
        
        try:
            # Load all cogs first
            print("📦 Loading cogs...")
            
            from cogs.game_search import GameSearchCog
            from cogs.user_profiles import UserProfilesCog
            
            await bot.add_cog(GameSearchCog(bot))
            await bot.add_cog(UserProfilesCog(bot))
            
            print("✅ Cogs loaded successfully")
            
            # Check commands in tree
            all_commands = bot.tree.get_commands()
            print(f"🌳 Commands in tree: {len(all_commands)}")
            
            command_names = []
            for cmd in all_commands:
                command_names.append(cmd.name)
                print(f"   - {cmd.name}: {cmd.description}")
            
            # Verify our key commands are present
            key_commands = ["gg-search", "gg-random", "gg-profile", "gg-collection"]
            missing_commands = [cmd for cmd in key_commands if cmd not in command_names]
            
            if missing_commands:
                print(f"❌ Missing commands: {missing_commands}")
                return
            else:
                print(f"✅ All key commands present in tree")
            
            # Force sync commands
            guild_id = os.getenv("DISCORD_GUILD_ID")
            
            if guild_id:
                print(f"🏰 Syncing to guild {guild_id} (instant)...")
                guild = discord.Object(id=int(guild_id))
                synced = await bot.tree.sync(guild=guild)
                print(f"✅ Successfully synced {len(synced)} commands to guild")
            else:
                print("🌍 Syncing globally (may take up to 1 hour to appear)...")
                synced = await bot.tree.sync()
                print(f"✅ Successfully synced {len(synced)} commands globally")
            
            # List synced commands
            for cmd in synced:
                print(f"   ✅ {cmd.name}")
            
            sync_successful = True
            print("🎉 Command sync completed successfully!")
            
        except Exception as e:
            print(f"❌ Error during sync: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            await bot.close()
    
    try:
        await bot.start(token)
        return sync_successful
    except Exception as e:
        print(f"❌ Bot startup error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Discord Command Force Sync Tool")
    print("=" * 50)
    asyncio.run(force_sync_commands())
