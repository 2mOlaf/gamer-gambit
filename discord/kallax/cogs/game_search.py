import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import logging
import difflib
from typing import List, Dict, Any, Optional, Tuple

from utils.bgg_api import BGGApiClient
from utils.steam_api import SteamApiClient
from utils.xbox_api import XboxApiClient

logger = logging.getLogger(__name__)

class GameSearchCog(commands.Cog):
    """Game search functionality"""
    
    def __init__(self, bot):
        self.bot = bot
        
    @app_commands.command(name='gg-search', description='Search for games across multiple platforms')
    @app_commands.describe(
        query='Name of the game to search for',
        catalog='Platform to search on (default: all)'
    )
    @app_commands.choices(catalog=[
        app_commands.Choice(name='All Platforms', value='all'),
        app_commands.Choice(name='BoardGameGeek', value='bgg'),
        app_commands.Choice(name='Steam', value='steam'),
        app_commands.Choice(name='Xbox', value='xbox')
    ])
    async def search_game(self, interaction: discord.Interaction, query: str, catalog: str = 'all'):
        """Search for games across multiple platforms"""
        if not query or len(query.strip()) < 2:
            await interaction.response.send_message("❌ Please provide a game name to search for (at least 2 characters)", ephemeral=True)
            return
            
        # Defer response for longer operations
        await interaction.response.defer()
        
        try:
            search_results = []
            
            # Search across platforms based on catalog parameter
            if catalog == 'all' or catalog == 'bgg':
                try:
                    async with BGGApiClient() as bgg:
                        # Include ratings for better search result display
                        bgg_results = await bgg.search_games(query.strip(), include_ratings=True)
                        for result in bgg_results[:5]:  # Limit BGG results when searching all
                            result['platform'] = 'bgg'
                            result['platform_name'] = 'BoardGameGeek'
                            result['platform_emoji'] = '🎲'
                            search_results.append(result)
                except Exception as e:
                    logger.error(f"Error searching BGG: {e}")
                    
            if catalog == 'all' or catalog == 'steam':
                try:
                    async with SteamApiClient() as steam:
                        steam_results = await steam.search_games(query.strip(), 5 if catalog == 'all' else 10)
                        for result in steam_results:
                            result['platform'] = 'steam'
                            result['platform_name'] = 'Steam'
                            result['platform_emoji'] = '🎮'
                            search_results.append(result)
                except Exception as e:
                    logger.error(f"Error searching Steam: {e}")
                    
            if catalog == 'all' or catalog == 'xbox':
                try:
                    async with XboxApiClient() as xbox:
                        xbox_results = await xbox.search_games(query.strip(), 5 if catalog == 'all' else 10)
                        for result in xbox_results:
                            result['platform'] = 'xbox'
                            result['platform_name'] = 'Xbox'
                            result['platform_emoji'] = '🎯'
                            search_results.append(result)
                except Exception as e:
                    logger.error(f"Error searching Xbox: {e}")
                    
            if not search_results:
                platform_text = catalog.upper() if catalog != 'all' else 'any platform'
                await interaction.followup.send(f"❌ No games found matching '{query}' on {platform_text}")
                return
                
            # Limit results to top 10
            search_results = search_results[:10]
            
            # For single platform BGG search with one result, show detailed info
            if catalog == 'bgg' and len(search_results) == 1 and search_results[0]['platform'] == 'bgg':
                await self._show_game_details_interaction(interaction, search_results[0]['bgg_id'])
                return
            
            # Show search results with reactions for selection
            await self._show_multi_platform_search_results(interaction, search_results, query, catalog)
                
        except Exception as e:
            logger.error(f"Error searching for games: {e}")
            await interaction.followup.send("❌ An error occurred while searching. Please try again.")
    
    async def _show_multi_platform_search_results(self, interaction: discord.Interaction, results: List[Dict[str, Any]], original_query: str, catalog: str):
        """Show multi-platform search results with reaction-based selection"""
        
        # Number emojis for selection
        number_emojis = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']
        
        # Create embed with search results
        platform_text = catalog.upper() if catalog != 'all' else 'All Platforms'
        embed = discord.Embed(
            title=f"🎮 Search Results for '{original_query}' ({platform_text})",
            description="React with a number to see detailed information about that game.\n\n🌟 = Most Relevant Result",
            color=discord.Color.blue()
        )
        
        # Sort results by relevance score and mark the most relevant
        scored_results = self._score_search_results(results, original_query, catalog)
        
        for i, (game, relevance_score) in enumerate(scored_results[:10]):
            # Mark the most relevant result
            relevance_indicator = "🌟 " if i == 0 and relevance_score > 0.7 else ""
            
            # Format game title and info based on platform
            if game['platform'] == 'bgg':
                year_str = f" ({game['year_published']})" if game.get('year_published') else ""
                # Add rating if available for enhanced info
                rating_str = f" | ⭐ {game.get('rating', 0):.1f}" if game.get('rating') else ""
                info_text = f"BGG ID: {game['bgg_id']}{rating_str}"
            elif game['platform'] == 'steam':
                year_str = f" ({game['release_date']})" if game.get('release_date') else ""
                price_str = f" | {game.get('price', 'N/A')}" if game.get('price') != 'N/A' else ""
                # Add metacritic score if available
                score_str = f" | 📊 {game.get('metacritic_score')}" if game.get('metacritic_score') else ""
                info_text = f"Steam App ID: {game['app_id']}{price_str}{score_str}"
            elif game['platform'] == 'xbox':
                year_str = f" ({game['release_date']})" if game.get('release_date') else ""
                price_str = f" | {game.get('price', 'N/A')}" if game.get('price') != 'N/A' else ""
                info_text = f"Xbox ID: {game.get('product_id', 'N/A')}{price_str}"
            else:
                year_str = ""
                info_text = "Unknown platform"
            
            embed.add_field(
                name=f"{number_emojis[i]} {relevance_indicator}{game['platform_emoji']} {game['name']}{year_str}",
                value=f"**{game['platform_name']}** - {info_text}",
                inline=False
            )
            
        embed.set_footer(text="React within 60 seconds to select a game")
        
        message = await interaction.followup.send(embed=embed)
        
        # Add reaction buttons
        for i in range(min(len(scored_results), 10)):
            await message.add_reaction(number_emojis[i])
            
        def check(reaction, user):
            return (
                user == interaction.user and
                reaction.message.id == message.id and
                str(reaction.emoji) in number_emojis[:len(scored_results)]
            )
            
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
            
            # Get selected game index from scored results
            selected_index = number_emojis.index(str(reaction.emoji))
            selected_game = scored_results[selected_index][0]  # Get the game from the tuple
            
            # Show detailed info based on platform
            await self._show_platform_game_details(interaction, selected_game)
            
        except asyncio.TimeoutError:
            # Remove reactions on timeout
            try:
                await message.clear_reactions()
                embed.set_footer(text="Selection timed out")
                await message.edit(embed=embed)
            except discord.NotFound:
                pass

    async def _show_platform_game_details(self, interaction: discord.Interaction, selected_game: Dict[str, Any]):
        """Show detailed game information based on platform"""
        try:
            if selected_game['platform'] == 'bgg':
                await self._show_game_details_interaction_followup(interaction, selected_game['bgg_id'])
            elif selected_game['platform'] == 'steam':
                await self._show_steam_game_details(interaction, selected_game)
            elif selected_game['platform'] == 'xbox':
                await self._show_xbox_game_details(interaction, selected_game)
            else:
                await interaction.followup.send("❌ Unsupported platform for detailed view.")
        except Exception as e:
            logger.error(f"Error showing platform game details: {e}")
            await interaction.followup.send("❌ An error occurred while getting game details.")

    async def _show_steam_game_details(self, interaction: discord.Interaction, game_data: Dict[str, Any]):
        """Show detailed Steam game information"""
        try:
            async with SteamApiClient() as steam:
                # Get detailed game info from Steam store
                detailed_game = await steam.get_game_details(game_data['app_id'])
                
                if not detailed_game:
                    detailed_game = game_data  # Fallback to search result data
                
                # Create Steam embed
                embed = discord.Embed(
                    title=detailed_game['name'],
                    url=f"https://store.steampowered.com/app/{detailed_game.get('app_id', game_data['app_id'])}",
                    color=discord.Color.blue()
                )
                
                # Add images
                if detailed_game.get('header_image'):
                    embed.set_image(url=detailed_game['header_image'])
                elif detailed_game.get('capsule_image'):
                    embed.set_thumbnail(url=detailed_game['capsule_image'])
                
                # Game info
                info_lines = []
                if detailed_game.get('release_date'):
                    info_lines.append(f"**Release Date:** {detailed_game['release_date']}")
                if detailed_game.get('developers'):
                    info_lines.append(f"**Developer:** {', '.join(detailed_game['developers'][:2])}")
                if detailed_game.get('publishers'):
                    info_lines.append(f"**Publisher:** {', '.join(detailed_game['publishers'][:2])}")
                if detailed_game.get('price'):
                    info_lines.append(f"**Price:** {detailed_game['price']}")
                
                if info_lines:
                    embed.add_field(name="🎮 Game Info", value="\n".join(info_lines), inline=True)
                
                # Platform info
                platform_lines = []
                platforms = detailed_game.get('platforms', {})
                if platforms.get('windows'):
                    platform_lines.append("🖥️ Windows")
                if platforms.get('mac'):
                    platform_lines.append("🍎 macOS")
                if platforms.get('linux'):
                    platform_lines.append("🐧 Linux")
                
                if platform_lines:
                    embed.add_field(name="💻 Platforms", value="\n".join(platform_lines), inline=True)
                
                # Ratings
                rating_lines = []
                if detailed_game.get('metacritic_score'):
                    rating_lines.append(f"**Metacritic:** {detailed_game['metacritic_score']}/100")
                if detailed_game.get('recommendations'):
                    rating_lines.append(f"**Steam Reviews:** {detailed_game['recommendations']:,}")
                if detailed_game.get('achievements'):
                    rating_lines.append(f"**Achievements:** {detailed_game['achievements']}")
                
                if rating_lines:
                    embed.add_field(name="⭐ Ratings & Features", value="\n".join(rating_lines), inline=False)
                
                # Genres
                if detailed_game.get('genres'):
                    genres_text = ', '.join(detailed_game['genres'][:5])
                    embed.add_field(name="🎭 Genres", value=genres_text, inline=False)
                
                # Description
                if detailed_game.get('description'):
                    desc = detailed_game['description']
                    if len(desc) > 300:
                        desc = desc[:297] + "..."
                    embed.add_field(name="📜 Description", value=desc, inline=False)
                
                embed.set_footer(
                    text=f"Steam App ID: {detailed_game.get('app_id', game_data['app_id'])}",
                    icon_url="https://store.steampowered.com/favicon.ico"
                )
                
                await interaction.followup.send(embed=embed)
                
        except Exception as e:
            logger.error(f"Error showing Steam game details: {e}")
            await interaction.followup.send("❌ An error occurred while getting Steam game details.")

    async def _show_xbox_game_details(self, interaction: discord.Interaction, game_data: Dict[str, Any]):
        """Show detailed Xbox game information"""
        try:
            # For now, show basic info from search results as Xbox API is limited
            embed = discord.Embed(
                title=game_data['name'],
                color=discord.Color.green()
            )
            
            # Add image if available
            if game_data.get('image_url'):
                embed.set_thumbnail(url=game_data['image_url'])
            
            # Basic info
            info_lines = []
            if game_data.get('release_date'):
                info_lines.append(f"**Release Date:** {game_data['release_date']}")
            if game_data.get('price'):
                info_lines.append(f"**Price:** {game_data['price']}")
            if game_data.get('rating'):
                info_lines.append(f"**Rating:** {game_data['rating']}")
            
            if info_lines:
                embed.add_field(name="🎯 Game Info", value="\n".join(info_lines), inline=True)
            
            # Platforms
            if game_data.get('platforms'):
                platforms_text = ', '.join(game_data['platforms'])
                embed.add_field(name="💻 Platforms", value=platforms_text, inline=True)
            
            # Description
            if game_data.get('description'):
                desc = game_data['description']
                if len(desc) > 300:
                    desc = desc[:297] + "..."
                embed.add_field(name="📜 Description", value=desc, inline=False)
            
            embed.add_field(
                name="📎 Note", 
                value="Detailed Xbox game information requires additional API access. This shows basic search result data.",
                inline=False
            )
            
            embed.set_footer(
                text=f"Xbox Product ID: {game_data.get('product_id', 'N/A')}",
                icon_url="https://assets.xboxservices.com/assets/XboxOne/favicon.ico"
            )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error showing Xbox game details: {e}")
            await interaction.followup.send("❌ An error occurred while getting Xbox game details.")

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
    
    def _score_search_results(self, results: List[Dict[str, Any]], query: str, catalog: str) -> List[Tuple[Dict[str, Any], float]]:
        """Score and sort search results by relevance"""
        scored_results = []
        query_lower = query.lower().strip()
        
        for result in results:
            score = 0.0
            name_lower = result.get('name', '').lower()
            
            # Exact match gets highest score
            if name_lower == query_lower:
                score += 1.0
            # Start with query gets high score
            elif name_lower.startswith(query_lower):
                score += 0.9
            # Contains query gets good score
            elif query_lower in name_lower:
                score += 0.8
            # Use similarity ratio for fuzzy matching
            else:
                similarity = difflib.SequenceMatcher(None, query_lower, name_lower).ratio()
                score += similarity * 0.7
            
            # Platform-specific bonuses
            if catalog == 'bgg' and result.get('platform') == 'bgg':
                score += 0.1
                # BGG games with higher ratings get bonus
                if result.get('rating'):
                    score += min(result['rating'] / 10 * 0.1, 0.1)
            elif catalog == 'steam' and result.get('platform') == 'steam':
                score += 0.1
            elif catalog == 'xbox' and result.get('platform') == 'xbox':
                score += 0.1
            elif catalog == 'all':
                # For multi-platform search, slightly favor BGG for board games
                if result.get('platform') == 'bgg':
                    score += 0.05
            
            # Year bonus (more recent games get slight bonus)
            if result.get('year_published'):
                year = result['year_published']
                if isinstance(year, str) and year.isdigit():
                    year = int(year)
                if isinstance(year, int) and year > 2000:
                    # Bonus for games from 2000 onwards, max 0.1
                    year_bonus = min((year - 2000) / 200, 0.1)
                    score += year_bonus
            
            scored_results.append((result, score))
        
        # Sort by score (highest first)
        scored_results.sort(key=lambda x: x[1], reverse=True)
        return scored_results
    
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
