"""
Game Assignment Cog for Jarvfjallet bot.
Handles random game assignments and user status tracking.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

logger = logging.getLogger(__name__)

class GameAssignment(commands.Cog):
    """Handles game assignment and tracking functionality"""
    
    def __init__(self, bot):
        self.bot = bot
        
    @app_commands.command(name="hit", description="Get a random unassigned game from itch.io")
    @app_commands.describe()
    async def hit(self, interaction: discord.Interaction):
        """Assign a random unassigned game to the user"""
        await interaction.response.defer(thinking=True)
        
        try:
            # Get a random unassigned game
            game = await self.bot.database.get_random_unassigned_game()
            
            if not game:
                embed = discord.Embed(
                    title="🎮 No Games Available",
                    description="Sorry, there are no unassigned games available at the moment!",
                    color=discord.Color.orange()
                )
                await interaction.followup.send(embed=embed)
                return
                
            # Assign the game to the user
            success = await self.bot.database.assign_game_to_user(
                game['id'], 
                str(interaction.user.id), 
                interaction.user.display_name
            )
            
            if not success:
                embed = discord.Embed(
                    title="❌ Assignment Failed",
                    description="Failed to assign the game. Please try again.",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed)
                return
                
            # Create embed with game information
            embed = discord.Embed(
                title=f"🎯 Game Assigned: {game['game_name']}",
                description=game.get('short_text', 'No description available'),
                color=discord.Color.green(),
                url=game['game_url']
            )
            
            # Add fields
            if game.get('dev_name'):
                embed.add_field(name="Developer", value=game['dev_name'], inline=True)
                
            # Platform support
            platforms = []
            if game.get('windows'):
                platforms.append("🪟 Windows")
            if game.get('mac'):
                platforms.append("🍎 macOS") 
            if game.get('linux'):
                platforms.append("🐧 Linux")
                
            if platforms:
                embed.add_field(name="Platforms", value="\n".join(platforms), inline=True)
                
            embed.add_field(name="Host", value=game.get('game_host', 'itch.io'), inline=True)
            
            # Add thumbnail if available
            if game.get('thumb_url'):
                embed.set_thumbnail(url=game['thumb_url'])
                
            embed.set_footer(text=f"Game ID: {game['id']} • Assigned to {interaction.user.display_name}")
            
            # Send both embed and confirmation message
            await interaction.followup.send(embed=embed)
            
            # Also send a DM to the user
            try:
                dm_embed = discord.Embed(
                    title=f"📧 You've been assigned: {game['game_name']}",
                    description=f"Check it out: {game['game_url']}",
                    color=discord.Color.blue()
                )
                await interaction.user.send(embed=dm_embed)
            except discord.Forbidden:
                # User has DMs disabled, that's okay
                pass
                
            logger.info(f"Assigned game {game['id']} ({game['game_name']}) to user {interaction.user.id}")
            
        except Exception as e:
            logger.error(f"Error in hit command: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="An unexpected error occurred. Please try again.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            
    @app_commands.command(name="status", description="Check your assigned games and their status")
    @app_commands.describe(user="Check another user's status (optional)")
    async def status(self, interaction: discord.Interaction, user: Optional[discord.Member] = None):
        """Show user's assigned games with status information"""
        await interaction.response.defer(thinking=True)
        
        try:
            target_user = user if user else interaction.user
            user_id = str(target_user.id)
            username = target_user.display_name
            
            # Get user's games using legacy method for backward compatibility
            games = await self.bot.database.get_user_games_legacy(user_id, username)
            
            if not games:
                embed = discord.Embed(
                    title=f"📋 {target_user.display_name}'s Games",
                    description="No assigned games found.",
                    color=discord.Color.light_gray()
                )
                await interaction.followup.send(embed=embed)
                return
                
            # Create embed
            embed = discord.Embed(
                title=f"📋 {target_user.display_name}'s Assigned Games",
                color=discord.Color.blue()
            )
            
            # Status emojis
            ACTIVE = "▶️"
            WAITING = "⏸"
            DONE = "⏹"
            RECENT = "⏺"
            UNKNOWN = "❓"
            
            # Group games by status
            status_lines = [f"{ACTIVE} **Active**; {WAITING} **Waiting**; {DONE} **Done**\n"]
            
            current_date = datetime.now()
            
            for game in games:
                # Determine status based on dates
                review_date = game.get('review_date')
                assign_date = game.get('assign_date')
                
                # Convert timestamps to datetime if they exist
                review_datetime = None
                assign_datetime = None
                
                if review_date and str(review_date).isdigit():
                    review_datetime = datetime.fromtimestamp(int(review_date) / 1000)
                    
                if assign_date and str(assign_date).isdigit():
                    assign_datetime = datetime.fromtimestamp(int(assign_date) / 1000)
                
                # Determine status emoji and format
                game_line = f"[{game['game_name']}]({game['game_url']}) by {game.get('dev_name', 'Unknown')}"
                
                if review_datetime and review_datetime < current_date:
                    # Review completed
                    status_lines.append(f"{DONE} {game_line}")
                elif assign_datetime and (current_date - assign_datetime).days <= 7:
                    # Recently assigned (within 7 days)
                    status_lines.append(f"{ACTIVE} {game_line}")
                elif not review_date or review_date == '':
                    # Waiting for review
                    status_lines.append(f"{WAITING} {game_line}")
                elif assign_datetime and assign_datetime.date() == current_date.date():
                    # Assigned today
                    status_lines.append(f"{RECENT} {game_line}")
                else:
                    # Unknown status
                    status_lines.append(f"{UNKNOWN} {game_line}")
                    
            # Split into multiple fields if too long
            description = "\n".join(status_lines)
            
            if len(description) > 4096:
                # Split into multiple embeds if needed
                embed.description = description[:4093] + "..."
                embed.add_field(name="Note", value="List truncated due to length. Use `/mystats` for full details.", inline=False)
            else:
                embed.description = description
                
            embed.set_footer(text=f"Total games: {len(games)}")
            
            await interaction.followup.send(embed=embed)
            
            logger.info(f"Status requested for user {target_user.id} by {interaction.user.id}")
            
        except Exception as e:
            logger.error(f"Error in status command: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="An unexpected error occurred. Please try again.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            
    @app_commands.command(name="mystats", description="Get detailed statistics about your assigned games")
    async def mystats(self, interaction: discord.Interaction):
        """Show detailed statistics for the user's games"""
        await interaction.response.defer(thinking=True)
        
        try:
            user_id = str(interaction.user.id)
            username = interaction.user.display_name
            
            # Get user's games
            games = await self.bot.database.get_user_games_legacy(user_id, username)
            
            if not games:
                embed = discord.Embed(
                    title="📊 Your Game Statistics",
                    description="You haven't been assigned any games yet! Use `/hit` to get started.",
                    color=discord.Color.light_gray()
                )
                await interaction.followup.send(embed=embed)
                return
                
            # Calculate statistics
            total_games = len(games)
            completed_games = sum(1 for game in games if game.get('review_date') and str(game['review_date']).isdigit())
            pending_games = total_games - completed_games
            
            # Platform breakdown
            windows_games = sum(1 for game in games if game.get('windows'))
            mac_games = sum(1 for game in games if game.get('mac'))
            linux_games = sum(1 for game in games if game.get('linux'))
            
            # Create embed
            embed = discord.Embed(
                title=f"📊 {interaction.user.display_name}'s Game Statistics",
                color=discord.Color.purple()
            )
            
            # Overview
            embed.add_field(
                name="📈 Overview",
                value=f"**Total Games:** {total_games}\n**Completed:** {completed_games}\n**Pending:** {pending_games}",
                inline=True
            )
            
            # Platform breakdown
            embed.add_field(
                name="💻 Platforms",
                value=f"🪟 Windows: {windows_games}\n🍎 macOS: {mac_games}\n🐧 Linux: {linux_games}",
                inline=True
            )
            
            # Completion rate
            completion_rate = (completed_games / total_games * 100) if total_games > 0 else 0
            embed.add_field(
                name="🎯 Completion Rate",
                value=f"{completion_rate:.1f}%",
                inline=True
            )
            
            # Recent activity (last 5 games)
            recent_games = games[:5]
            recent_list = []
            for game in recent_games:
                status = "✅" if game.get('review_date') and str(game['review_date']).isdigit() else "⏳"
                recent_list.append(f"{status} [{game['game_name']}]({game['game_url']})")
                
            if recent_list:
                embed.add_field(
                    name="🕐 Recent Games",
                    value="\n".join(recent_list),
                    inline=False
                )
                
            embed.set_footer(text=f"Keep up the great work! • User ID: {interaction.user.id}")
            
            await interaction.followup.send(embed=embed)
            
            logger.info(f"Stats requested by user {interaction.user.id}")
            
        except Exception as e:
            logger.error(f"Error in mystats command: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="An unexpected error occurred. Please try again.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            
    @app_commands.command(name="gameinfo", description="Get information about the game database")
    async def gameinfo(self, interaction: discord.Interaction):
        """Show general information about the game database"""
        await interaction.response.defer(thinking=True)
        
        try:
            stats = await self.bot.database.get_game_stats()
            
            embed = discord.Embed(
                title="🎮 Game Database Information",
                color=discord.Color.gold()
            )
            
            embed.add_field(
                name="📊 Database Stats",
                value=f"**Total Games:** {stats['total_games']}\n"
                      f"**Available:** {stats['unassigned_games']}\n"
                      f"**Assigned:** {stats['assigned_games']}\n"
                      f"**Completed:** {stats['completed_reviews']}",
                inline=True
            )
            
            # Calculate percentages
            if stats['total_games'] > 0:
                available_pct = stats['unassigned_games'] / stats['total_games'] * 100
                assigned_pct = stats['assigned_games'] / stats['total_games'] * 100
                completed_pct = stats['completed_reviews'] / stats['total_games'] * 100
                
                embed.add_field(
                    name="📈 Percentages",
                    value=f"**Available:** {available_pct:.1f}%\n"
                          f"**Assigned:** {assigned_pct:.1f}%\n"
                          f"**Completed:** {completed_pct:.1f}%",
                    inline=True
                )
                
            embed.add_field(
                name="🎯 How to Play",
                value="• Use `/hit` to get a random game\n"
                      "• Use `/status` to see your games\n"
                      "• Use `/mystats` for detailed stats\n"
                      "• Complete reviews to help the community!",
                inline=False
            )
            
            embed.set_footer(text="Games sourced from itch.io • Bot by 2mOlaf")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in gameinfo command: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="Failed to retrieve database information.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

async def setup(bot):
    """Setup function for the cog"""
    await bot.add_cog(GameAssignment(bot))
