import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import logging
from typing import List, Dict, Any, Optional

from utils.bgg_api import BGGApiClient

logger = logging.getLogger(__name__)

class GameSearchCog(commands.Cog):
    """Game search functionality"""
    
    def __init__(self, bot):
        self.bot = bot
        
    @app_commands.command(name='gg-search', description='Search for board games on BoardGameGeek')
    @app_commands.describe(query='Name of the board game to search for')
    async def search_game(self, interaction: discord.Interaction, query: str):
        """Search for board games on BoardGameGeek"""
        if not query or len(query.strip()) < 2:
            await interaction.response.send_message("❌ Please provide a game name to search for (at least 2 characters)", ephemeral=True)
            return
            
        # Defer response for longer operations
        await interaction.response.defer()
        
        try:
            async with BGGApiClient() as bgg:
                # Search for games
                search_results = await bgg.search_games(query.strip())
                
                if not search_results:
                    await interaction.followup.send(f"❌ No games found matching '{query}'")
                    return
                    
                # Limit results to top 10
                search_results = search_results[:10]
                
                # If only one result, show detailed info
                if len(search_results) == 1:
                    await self._show_game_details_interaction(interaction, search_results[0]['bgg_id'])
                    return
                    
                # Show search results with reactions for selection
                await self._show_search_results_interaction(interaction, search_results, query)
                
        except Exception as e:
            logger.error(f"Error searching for games: {e}")
            await interaction.followup.send("❌ An error occurred while searching. Please try again.")
    
    async def _show_search_results_interaction(self, interaction: discord.Interaction, results: List[Dict[str, Any]], original_query: str):
        """Show search results with reaction-based selection for interactions"""
        
        # Number emojis for selection
        number_emojis = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']
        
        # Create embed with search results
        embed = discord.Embed(
            title=f"🎲 Search Results for '{original_query}'",
            description="React with a number to see detailed information about that game.",
            color=discord.Color.blue()
        )
        
        for i, game in enumerate(results[:10]):
            year_str = f" ({game['year_published']})" if game['year_published'] else ""
            embed.add_field(
                name=f"{number_emojis[i]} {game['name']}{year_str}",
                value=f"BGG ID: {game['bgg_id']}",
                inline=False
            )
            
        embed.set_footer(text="React within 60 seconds to select a game")
        
        message = await interaction.followup.send(embed=embed)
        
        # Add reaction buttons
        for i in range(min(len(results), 10)):
            await message.add_reaction(number_emojis[i])
            
        def check(reaction, user):
            return (
                user == interaction.user and
                reaction.message.id == message.id and
                str(reaction.emoji) in number_emojis[:len(results)]
            )
            
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
            
            # Get selected game index
            selected_index = number_emojis.index(str(reaction.emoji))
            selected_game = results[selected_index]
            
            # Show detailed info
            await self._show_game_details_interaction_followup(interaction, selected_game['bgg_id'])
            
        except asyncio.TimeoutError:
            # Remove reactions on timeout
            try:
                await message.clear_reactions()
                embed.set_footer(text="Selection timed out")
                await message.edit(embed=embed)
            except discord.NotFound:
                pass
                
    async def _show_game_details_interaction(self, interaction: discord.Interaction, game_id: int):
        """Show detailed game information for slash command interaction"""
        try:
            async with BGGApiClient() as bgg:
                # Get detailed game info
                games = await bgg.get_game_details([game_id])
                
                if not games:
                    await interaction.followup.send("❌ Could not retrieve game details.")
                    return
                    
                game = games[0]
                
                # Cache the game data
                await self.bot.database.cache_game(game)
                
                # Create detailed embed
                embed = await self._create_game_embed(game)
                await interaction.followup.send(embed=embed)
                
        except Exception as e:
            logger.error(f"Error getting game details: {e}")
            await interaction.followup.send("❌ An error occurred while getting game details.")
    
    async def _show_game_details_interaction_followup(self, interaction: discord.Interaction, game_id: int):
        """Show detailed game information as a followup to existing interaction"""
        try:
            async with BGGApiClient() as bgg:
                # Get detailed game info
                games = await bgg.get_game_details([game_id])
                
                if not games:
                    await interaction.followup.send("❌ Could not retrieve game details.")
                    return
                    
                game = games[0]
                
                # Cache the game data
                await self.bot.database.cache_game(game)
                
                # Create detailed embed
                embed = await self._create_game_embed(game)
                await interaction.followup.send(embed=embed)
                
        except Exception as e:
            logger.error(f"Error getting game details: {e}")
            await interaction.followup.send("❌ An error occurred while getting game details.")
                
    async def _create_game_embed(self, game: Dict[str, Any]) -> discord.Embed:
        """Create a rich embed with game information"""
        
        # Main embed
        embed = discord.Embed(
            title=game['name'],
            url=f"https://boardgamegeek.com/boardgame/{game['bgg_id']}",
            color=discord.Color.green()
        )
        
        # Add thumbnail image
        if game.get('thumbnail_url'):
            embed.set_thumbnail(url=game['thumbnail_url'])
            
        # Add main image
        if game.get('image_url'):
            embed.set_image(url=game['image_url'])
            
        # Basic info
        info_lines = []
        if game.get('year_published'):
            info_lines.append(f"**Year:** {game['year_published']}")
            
        if game.get('min_players') and game.get('max_players'):
            if game['min_players'] == game['max_players']:
                info_lines.append(f"**Players:** {game['min_players']}")
            else:
                info_lines.append(f"**Players:** {game['min_players']} - {game['max_players']}")
                
        if game.get('playing_time'):
            info_lines.append(f"**Play Time:** {game['playing_time']} min")
        elif game.get('min_playtime') and game.get('max_playtime'):
            info_lines.append(f"**Play Time:** {game['min_playtime']} - {game['max_playtime']} min")
            
        if game.get('min_age'):
            info_lines.append(f"**Min Age:** {game['min_age']}+")
            
        if info_lines:
            embed.add_field(name="📋 Game Info", value="\n".join(info_lines), inline=True)
            
        # Ratings
        rating_lines = []
        if game.get('rating'):
            rating_lines.append(f"**BGG Rating:** {game['rating']:.1f}/10")
            
        if game.get('rating_count'):
            rating_lines.append(f"**Ratings:** {game['rating_count']:,}")
            
        if game.get('weight'):
            weight_desc = self._get_weight_description(game['weight'])
            rating_lines.append(f"**Complexity:** {game['weight']:.1f}/5 ({weight_desc})")
            
        if rating_lines:
            embed.add_field(name="⭐ Ratings", value="\n".join(rating_lines), inline=True)
            
        # Player recommendations
        if game.get('suggested_players'):
            rec_lines = []
            for players, rec in game['suggested_players'].items():
                if rec == 'Best':
                    rec_lines.append(f"**{players}:** 🌟 {rec}")
                elif rec == 'Recommended':
                    rec_lines.append(f"**{players}:** ✅ {rec}")
                    
            if rec_lines:
                embed.add_field(name="👥 Best Player Counts", value="\n".join(rec_lines[:5]), inline=False)
        
        # Description (truncated)
        if game.get('description'):
            desc = game['description']
            if len(desc) > 300:
                desc = desc[:297] + "..."
            embed.add_field(name="📖 Description", value=desc, inline=False)
            
        # Footer
        embed.set_footer(
            text=f"BGG ID: {game['bgg_id']} | Use /gg-collection <username> to see someone's collection",
            icon_url="https://cf.geekdo-static.com/images/logos/navbar-logo-bgg-b2.svg"
        )
        
        return embed
    
    @staticmethod
    def _get_weight_description(weight: float) -> str:
        """Get human readable complexity description"""
        if weight < 1.5:
            return "Light"
        elif weight < 2.5:
            return "Light-Medium"
        elif weight < 3.5:
            return "Medium"
        elif weight < 4.5:
            return "Medium-Heavy"
        else:
            return "Heavy"
            
    @app_commands.command(name='gg-random', description='Get a random popular board game')
    async def random_game(self, interaction: discord.Interaction):
        """Get a random popular board game"""
        await interaction.response.defer()
        
        try:
            # For now, we'll use a simple approach with top games
            # In a full implementation, you'd want to implement proper filtering
            
            # Get a random game from BGG's hot list or top games
            # This is a simplified version - you'd want to expand this
            
            popular_game_ids = [
                174430,  # Gloomhaven
                12333,   # Twilight Struggle
                233078,  # Twilight Imperium 4
                167791,  # Terraforming Mars
                220308,  # Gaia Project
                161936,  # Pandemic Legacy: Season 1
                182028,  # Through the Ages: A New Story
                187645,  # Star Wars: Rebellion
                115746,  # War of the Ring (second edition)
                36218,   # Dominant Species
            ]
            
            import random
            selected_id = random.choice(popular_game_ids)
            
            await self._show_game_details_interaction(interaction, selected_id)
            
        except Exception as e:
            logger.error(f"Error getting random game: {e}")
            await interaction.followup.send("❌ An error occurred while finding a random game.")

async def setup(bot):
    await bot.add_cog(GameSearchCog(bot))
