import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import logging
from typing import Dict, Any, Optional, List
import json

from utils.bgg_api import BGGApiClient
from utils.steam_api import SteamApiClient
from utils.xbox_api import XboxApiClient

logger = logging.getLogger(__name__)

class UserProfilesCog(commands.Cog):
    """User profile management and collection display"""
    
    def __init__(self, bot):
        self.bot = bot
        
    @app_commands.command(name='gg-profile', description='Show your gaming profile')
    async def profile_show(self, interaction: discord.Interaction):
        """Show your gaming profile"""
        await interaction.response.defer()
        await self._show_profile_interaction(interaction, interaction.user.id)
            
    @app_commands.command(name='gg-profile-set', description='Set your profile information for gaming platforms')
    @app_commands.describe(
        platform='Gaming platform (bgg, steam, xbox)',
        username='Your username on that platform'
    )
    @app_commands.choices(platform=[
        app_commands.Choice(name='BoardGameGeek', value='bgg'),
        app_commands.Choice(name='Steam', value='steam'),
        app_commands.Choice(name='Xbox', value='xbox')
    ])
    async def set_profile(self, interaction: discord.Interaction, platform: str, username: str):
        """Set your profile information for various gaming platforms"""
        await interaction.response.defer()
        
        platform = platform.lower()
        valid_platforms = {'bgg': 'bgg_username', 'steam': 'steam_id', 'xbox': 'xbox_gamertag'}
        
        if platform not in valid_platforms:
            await interaction.followup.send(f"❌ Invalid platform. Valid options: {', '.join(valid_platforms.keys())}")
            return
            
        username = username.strip()
        if not username:
            await interaction.followup.send("❌ Please provide a valid username")
            return
            
        # Input sanitization for security
        if len(username) > 100:  # Reasonable length limit
            await interaction.followup.send("❌ Username too long (max 100 characters)")
            return
            
        # Basic validation against malicious input
        import re
        if not re.match(r'^[a-zA-Z0-9._-]+$', username) and platform in ['steam', 'xbox']:
            await interaction.followup.send(f"❌ Invalid characters in {platform} username. Use only letters, numbers, dots, underscores, and hyphens.")
            return
            
        # Validate platform username by checking if it exists
        if platform == 'bgg':
            try:
                async with BGGApiClient() as bgg:
                    collection = await bgg.get_user_collection(username, ['own'])
                    # If no exception and we get a response (even empty), user exists
                    
            except Exception as e:
                logger.error(f"BGG validation error: {e}")
                await interaction.followup.send(f"❌ Could not find BGG user '{username}'. Please check the username and try again.")
                return
        
        elif platform == 'steam':
            try:
                async with SteamApiClient() as steam:
                    # Try to resolve Steam ID and get profile
                    steam_id = await steam.get_steam_id(username)
                    if not steam_id:
                        await interaction.followup.send(f"❌ Could not find Steam user '{username}'. Please check the Steam ID or custom URL and try again.")
                        return
                    
                    profile = await steam.get_user_profile(steam_id)
                    if not profile:
                        await interaction.followup.send(f"❌ Could not access Steam profile for '{username}'. Profile may be private.")
                        return
                    
                    # Update username to the resolved Steam ID for storage
                    username = steam_id
                    
            except Exception as e:
                logger.error(f"Steam validation error: {e}")
                await interaction.followup.send(f"❌ Error validating Steam profile '{username}'. Please try again.")
                return
        
        elif platform == 'xbox':
            try:
                async with XboxApiClient() as xbox:
                    # Try to search for the gamertag
                    profile = await xbox.search_gamertag(username)
                    if not profile:
                        await interaction.followup.send(f"❌ Could not find Xbox gamertag '{username}'. Please check the gamertag and try again.")
                        return
                        
            except Exception as e:
                logger.error(f"Xbox validation error: {e}")
                await interaction.followup.send(f"❌ Error validating Xbox gamertag '{username}'. Please try again.")
                return
        
        # Update user profile
        profile_data = {valid_platforms[platform]: username}
        logger.info(f"Setting {platform} profile for user {interaction.user.id} to {username}")
        
        try:
            success = await self.bot.database.update_user_profile(interaction.user.id, **profile_data)
            logger.info(f"Update result: {success}")
            if success:
                await interaction.followup.send(f"✅ {platform.upper()} profile set to: **{username}**")
            else:
                # Create profile if update failed
                logger.info(f"Update failed, creating new profile for user {interaction.user.id}")
                success = await self.bot.database.create_user_profile(interaction.user.id, **profile_data)
                logger.info(f"Create result: {success}")
                if success:
                    await interaction.followup.send(f"✅ Profile created! {platform.upper()} username set to: **{username}**")
                else:
                    await interaction.followup.send("❌ Failed to update profile. Please try again.")
        except Exception as e:
            logger.error(f"Error updating profile: {e}")
            await interaction.followup.send("❌ An error occurred while updating your profile.")
    
    @app_commands.command(name='gg-profile-show', description="Show a user's gaming profile")
    @app_commands.describe(user='User whose profile to show (defaults to you)')
    async def show_profile(self, interaction: discord.Interaction, user: discord.Member = None):
        """Show a user's profile information"""
        await interaction.response.defer()
        target_user = user or interaction.user
        await self._show_profile_interaction(interaction, target_user.id, target_user)
        
    async def _show_profile_interaction(self, interaction: discord.Interaction, discord_id: int, discord_user: discord.Member = None):
        """Internal method to show user profile for interactions"""
        try:
            profile = await self.bot.database.get_user_profile(discord_id)
            
            if not profile:
                if discord_id == interaction.user.id:
                    await interaction.followup.send("❌ You don't have a profile yet. Use `/gg-profile-set` to get started!")
                else:
                    username = discord_user.display_name if discord_user else "User"
                    await interaction.followup.send(f"❌ {username} doesn't have a profile set up yet.")
                return
                
            # Create profile embed
            embed = discord.Embed(
                title=f"🎮 Gaming Profile",
                color=discord.Color.blue()
            )
            
            if discord_user:
                embed.set_author(
                    name=discord_user.display_name,
                    icon_url=discord_user.display_avatar.url
                )
                
            # Add platform information
            platforms = []
            if profile.get('bgg_username'):
                platforms.append(f"🎲 **BGG:** [{profile['bgg_username']}](https://boardgamegeek.com/user/{profile['bgg_username']})")
            if profile.get('steam_id'):
                platforms.append(f"🎮 **Steam:** {profile['steam_id']}")
            if profile.get('xbox_gamertag'):
                platforms.append(f"🎯 **Xbox:** {profile['xbox_gamertag']}")
                
            if platforms:
                embed.add_field(name="Gaming Platforms", value="\n".join(platforms), inline=False)
            else:
                embed.add_field(name="Gaming Platforms", value="*No platforms configured*", inline=False)
                
            # Weekly stats status
            stats_status = "✅ Enabled" if profile.get('weekly_stats_enabled') else "❌ Disabled"
            embed.add_field(name="Weekly Stats", value=stats_status, inline=True)
            
            embed.set_footer(text="Use /gg-profile-set to update your profile")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error showing profile: {e}")
            await interaction.followup.send("❌ An error occurred while retrieving the profile.")
    
    @app_commands.command(name='gg-collection', description='Show BGG collection for a user')
    @app_commands.describe(
        username='BGG username (defaults to your profile)',
        collection_type='Type of collection to show'
    )
    @app_commands.choices(collection_type=[
        app_commands.Choice(name='Owned Games', value='own'),
        app_commands.Choice(name='Wishlist', value='wishlist'),
        app_commands.Choice(name='For Trade', value='fortrade'),
        app_commands.Choice(name='Want to Buy', value='want')
    ])
    async def show_collection(self, interaction: discord.Interaction, username: str = None, collection_type: str = "own"):
        """Show BGG collection for a user"""
        await interaction.response.defer()
        
        # If no username provided, try to get from user's profile
        if not username:
            profile = await self.bot.database.get_user_profile(interaction.user.id)
            if not profile or not profile.get('bgg_username'):
                await interaction.followup.send("❌ Please specify a BGG username or set your profile with `/gg-profile-set`")
                return
            username = profile['bgg_username']
            
        collection_type = collection_type.lower()
        valid_types = ['own', 'wishlist', 'fortrade', 'want']
        
        if collection_type not in valid_types:
            collection_type = 'own'
            
        try:
            async with BGGApiClient() as bgg:
                collection = await bgg.get_user_collection(username, [collection_type])
                
                if not collection:
                    type_name = collection_type.replace('fortrade', 'for trade').title()
                    await interaction.followup.send(f"❌ No games found in {username}'s {type_name} collection")
                    return
                    
                await self._show_collection_pages_interaction(interaction, collection, username, collection_type)
                
        except Exception as e:
            logger.error(f"Error getting collection: {e}")
            await interaction.followup.send(f"❌ Could not retrieve collection for user '{username}'. Please check the username.")
    
    async def _show_collection_pages_interaction(self, interaction: discord.Interaction, collection: List[Dict], username: str, collection_type: str):
        """Show collection with pagination for interactions"""
        if not collection:
            return
            
        # Sort by name
        collection.sort(key=lambda x: x['name'])
        
        # Pagination setup
        items_per_page = 15
        pages = [collection[i:i + items_per_page] for i in range(0, len(collection), items_per_page)]
        current_page = 0
        
        def create_embed(page_items, page_num):
            type_name = collection_type.replace('fortrade', 'for trade').title()
            embed = discord.Embed(
                title=f"🎲 {username}'s {type_name} Collection",
                description=f"Page {page_num + 1} of {len(pages)} • {len(collection)} total games",
                color=discord.Color.green(),
                url=f"https://boardgamegeek.com/collection/user/{username}?{collection_type}=1"
            )
            
            # Create collection summary with links
            summary_links = []
            collection_counts = {
                'own': len([g for g in collection if g.get('own')]),
                'wishlist': len([g for g in collection if g.get('wishlist')]), 
                'fortrade': len([g for g in collection if g.get('fortrade')]),
                'want': len([g for g in collection if g.get('want')])
            }
            
            for ctype, count in collection_counts.items():
                if count > 0:
                    type_display = ctype.replace('fortrade', 'for trade').title()
                    url = f"https://boardgamegeek.com/collection/user/{username}?{ctype}=1"
                    summary_links.append(f"[{type_display}: {count}]({url})")
                    
            if summary_links:
                embed.add_field(name="📊 Collection Summary", value=" • ".join(summary_links), inline=False)
            
            # Add games for current page
            game_list = []
            for i, game in enumerate(page_items):
                game_num = page_num * items_per_page + i + 1
                year_str = f" ({game['year_published']})" if game['year_published'] else ""
                
                # Add rating if available
                rating_str = ""
                if game.get('rating') and game['rating'] > 0:
                    rating_str = f" ⭐{game['rating']:.1f}"
                    
                game_line = f"{game_num}. **{game['name']}**{year_str}{rating_str}"
                game_list.append(game_line)
                
            if game_list:
                embed.add_field(name="Games", value="\n".join(game_list), inline=False)
                
            embed.set_footer(
                text=f"Use reactions to navigate • BGG Collection",
                icon_url="https://cf.geekdo-static.com/images/logos/navbar-logo-bgg-b2.svg"
            )
            
            return embed
        
        # Send initial embed
        embed = create_embed(pages[current_page], current_page)
        message = await interaction.followup.send(embed=embed)
        
        # Only add reactions if there are multiple pages
        if len(pages) > 1:
            reactions = ['⬅️', '➡️']
            for reaction in reactions:
                await message.add_reaction(reaction)
                
            def check(reaction, user):
                return (
                    user == interaction.user and
                    reaction.message.id == message.id and
                    str(reaction.emoji) in reactions
                )
                
            while True:
                try:
                    reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
                    
                    if str(reaction.emoji) == '⬅️' and current_page > 0:
                        current_page -= 1
                    elif str(reaction.emoji) == '➡️' and current_page < len(pages) - 1:
                        current_page += 1
                    else:
                        # Remove invalid reaction
                        try:
                            await message.remove_reaction(reaction.emoji, user)
                        except discord.NotFound:
                            pass
                        continue
                        
                    # Update embed
                    embed = create_embed(pages[current_page], current_page)
                    await message.edit(embed=embed)
                    
                    # Remove user reaction
                    try:
                        await message.remove_reaction(reaction.emoji, user)
                    except discord.NotFound:
                        pass
                        
                except asyncio.TimeoutError:
                    # Remove reactions on timeout
                    try:
                        await message.clear_reactions()
                    except discord.NotFound:
                        pass
                    break
    
    async def _show_collection_pages(self, ctx, collection: List[Dict], username: str, collection_type: str):
        """Show collection with pagination"""
        if not collection:
            return
            
        # Sort by name
        collection.sort(key=lambda x: x['name'])
        
        # Pagination setup
        items_per_page = 15
        pages = [collection[i:i + items_per_page] for i in range(0, len(collection), items_per_page)]
        current_page = 0
        
        def create_embed(page_items, page_num):
            type_name = collection_type.replace('fortrade', 'for trade').title()
            embed = discord.Embed(
                title=f"🎲 {username}'s {type_name} Collection",
                description=f"Page {page_num + 1} of {len(pages)} • {len(collection)} total games",
                color=discord.Color.green(),
                url=f"https://boardgamegeek.com/collection/user/{username}?{collection_type}=1"
            )
            
            # Create collection summary with links
            summary_links = []
            collection_counts = {
                'own': len([g for g in collection if g.get('own')]),
                'wishlist': len([g for g in collection if g.get('wishlist')]), 
                'fortrade': len([g for g in collection if g.get('fortrade')]),
                'want': len([g for g in collection if g.get('want')])
            }
            
            for ctype, count in collection_counts.items():
                if count > 0:
                    type_display = ctype.replace('fortrade', 'for trade').title()
                    url = f"https://boardgamegeek.com/collection/user/{username}?{ctype}=1"
                    summary_links.append(f"[{type_display}: {count}]({url})")
                    
            if summary_links:
                embed.add_field(name="📊 Collection Summary", value=" • ".join(summary_links), inline=False)
            
            # Add games for current page
            game_list = []
            for i, game in enumerate(page_items):
                game_num = page_num * items_per_page + i + 1
                year_str = f" ({game['year_published']})" if game['year_published'] else ""
                
                # Add rating if available
                rating_str = ""
                if game.get('rating') and game['rating'] > 0:
                    rating_str = f" ⭐{game['rating']:.1f}"
                    
                game_line = f"{game_num}. **{game['name']}**{year_str}{rating_str}"
                game_list.append(game_line)
                
            if game_list:
                embed.add_field(name="Games", value="\n".join(game_list), inline=False)
                
            embed.set_footer(
                text=f"Use reactions to navigate • BGG Collection",
                icon_url="https://cf.geekdo-static.com/images/logos/navbar-logo-bgg-b2.svg"
            )
            
            return embed
        
        # Send initial embed
        embed = create_embed(pages[current_page], current_page)
        message = await ctx.send(embed=embed)
        
        # Only add reactions if there are multiple pages
        if len(pages) > 1:
            reactions = ['⬅️', '➡️']
            for reaction in reactions:
                await message.add_reaction(reaction)
                
            def check(reaction, user):
                return (
                    user == ctx.author and
                    reaction.message.id == message.id and
                    str(reaction.emoji) in reactions
                )
                
            while True:
                try:
                    reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
                    
                    if str(reaction.emoji) == '⬅️' and current_page > 0:
                        current_page -= 1
                    elif str(reaction.emoji) == '➡️' and current_page < len(pages) - 1:
                        current_page += 1
                    else:
                        # Remove invalid reaction
                        try:
                            await message.remove_reaction(reaction.emoji, user)
                        except discord.NotFound:
                            pass
                        continue
                        
                    # Update embed
                    embed = create_embed(pages[current_page], current_page)
                    await message.edit(embed=embed)
                    
                    # Remove user reaction
                    try:
                        await message.remove_reaction(reaction.emoji, user)
                    except discord.NotFound:
                        pass
                        
                except asyncio.TimeoutError:
                    # Remove reactions on timeout
                    try:
                        await message.clear_reactions()
                    except discord.NotFound:
                        pass
                    break
                    
    @app_commands.command(name='gg-plays', description='Show recent game plays from BGG')
    @app_commands.describe(
        username='BGG username (defaults to your profile)',
        limit='Number of recent plays to show (1-50)'
    )
    async def show_recent_plays(self, interaction: discord.Interaction, username: str = None, limit: int = 10):
        """Show recent game plays from BGG"""
        await interaction.response.defer()
        
        # If no username provided, try to get from user's profile
        if not username:
            profile = await self.bot.database.get_user_profile(interaction.user.id)
            if not profile or not profile.get('bgg_username'):
                await interaction.followup.send("❌ Please specify a BGG username or set your profile with `/gg-profile-set`")
                return
            username = profile['bgg_username']
            
        limit = max(1, min(limit, 50))  # Limit between 1 and 50
        
        try:
            async with BGGApiClient() as bgg:
                plays_data = await bgg.get_user_plays(username, page=1)
                plays = plays_data.get('plays', [])[:limit]
                
                if not plays:
                    await interaction.followup.send(f"❌ No recent plays found for user '{username}'")
                    return
                    
                await self._show_plays_embed_interaction(interaction, plays, username, plays_data.get('total', 0))
                
        except Exception as e:
            logger.error(f"Error getting plays: {e}")
            await interaction.followup.send(f"❌ Could not retrieve plays for user '{username}'. Please check the username.")
                
    async def _show_plays_embed_interaction(self, interaction: discord.Interaction, plays: List[Dict], username: str, total_plays: int):
        """Show plays in a rich embed for interactions"""
        embed = discord.Embed(
            title=f"🎮 Recent Plays for {username}",
            description=f"Showing {len(plays)} of {total_plays} total plays",
            color=discord.Color.purple(),
            url=f"https://boardgamegeek.com/plays/bydate/user/{username}"
        )
        
        for i, play in enumerate(plays[:10], 1):
            # Format play information
            game_name = play.get('game_name', 'Unknown Game')
            play_date = play.get('date', 'Unknown Date')
            duration = play.get('length', 0)
            
            play_info = [f"📅 {play_date}"]
            
            if duration and duration > 0:
                hours = duration // 60
                minutes = duration % 60
                if hours > 0:
                    play_info.append(f"⏱️ {hours}h {minutes}m")
                else:
                    play_info.append(f"⏱️ {minutes}m")
                    
            # Add players info
            players = play.get('players', [])
            if players:
                player_info = []
                for player in players[:4]:  # Limit to first 4 players
                    player_name = player.get('name', 'Unknown')
                    if player.get('win'):
                        player_name += " 🏆"
                    if player.get('score'):
                        player_name += f" ({player['score']})"
                    player_info.append(player_name)
                    
                if len(players) > 4:
                    player_info.append(f"... +{len(players) - 4} more")
                    
                play_info.append(f"👥 {', '.join(player_info)}")
                
            # Add location if available
            if play.get('location'):
                play_info.append(f"📍 {play['location']}")
                
            # Add comments if available (truncated)
            if play.get('comments'):
                comment = play['comments'][:100]
                if len(play['comments']) > 100:
                    comment += "..."
                play_info.append(f"💬 {comment}")
                
            embed.add_field(
                name=f"{i}. {game_name}",
                value="\n".join(play_info),
                inline=False
            )
            
        embed.set_footer(
            text="BGG Plays Data",
            icon_url="https://cf.geekdo-static.com/images/logos/navbar-logo-bgg-b2.svg"
        )
        
        await interaction.followup.send(embed=embed)
    
    @app_commands.command(name='gg-steam-games', description='Show Steam game library for a user')
    @app_commands.describe(
        steam_id='Steam ID or custom URL (defaults to your profile)',
        limit='Number of games to show (1-50)'
    )
    async def show_steam_games(self, interaction: discord.Interaction, steam_id: str = None, limit: int = 20):
        """Show Steam game library for a user"""
        await interaction.response.defer()
        
        # If no steam_id provided, try to get from user's profile
        if not steam_id:
            profile = await self.bot.database.get_user_profile(interaction.user.id)
            if not profile or not profile.get('steam_id'):
                await interaction.followup.send("❌ Please specify a Steam ID or set your profile with `/gg-profile-set`")
                return
            steam_id = profile['steam_id']
            
        limit = max(1, min(limit, 50))  # Limit between 1 and 50
        
        try:
            async with SteamApiClient() as steam:
                # Resolve Steam ID if needed
                resolved_steam_id = await steam.get_steam_id(steam_id)
                if not resolved_steam_id:
                    await interaction.followup.send(f"❌ Could not find Steam user '{steam_id}'")
                    return
                
                # Get user profile and games
                profile = await steam.get_user_profile(resolved_steam_id)
                games = await steam.get_user_games(resolved_steam_id)
                
                if not profile:
                    await interaction.followup.send(f"❌ Could not access Steam profile. Profile may be private.")
                    return
                    
                if not games:
                    await interaction.followup.send(f"❌ No games found for Steam user '{profile['profile_name']}'. Library may be private.")
                    return
                    
                await self._show_steam_games_embed(interaction, games[:limit], profile)
                
        except Exception as e:
            logger.error(f"Error getting Steam games: {e}")
            await interaction.followup.send(f"❌ Could not retrieve Steam games for user '{steam_id}'. Please check the Steam ID.")
    
    @app_commands.command(name='gg-steam-recent', description='Show recently played Steam games')
    @app_commands.describe(
        steam_id='Steam ID or custom URL (defaults to your profile)',
        limit='Number of recent games to show (1-20)'
    )
    async def show_steam_recent(self, interaction: discord.Interaction, steam_id: str = None, limit: int = 10):
        """Show recently played Steam games"""
        await interaction.response.defer()
        
        # If no steam_id provided, try to get from user's profile
        if not steam_id:
            profile = await self.bot.database.get_user_profile(interaction.user.id)
            if not profile or not profile.get('steam_id'):
                await interaction.followup.send("❌ Please specify a Steam ID or set your profile with `/gg-profile-set`")
                return
            steam_id = profile['steam_id']
            
        limit = max(1, min(limit, 20))  # Limit between 1 and 20
        
        try:
            async with SteamApiClient() as steam:
                # Resolve Steam ID if needed
                resolved_steam_id = await steam.get_steam_id(steam_id)
                if not resolved_steam_id:
                    await interaction.followup.send(f"❌ Could not find Steam user '{steam_id}'")
                    return
                
                # Get user profile and recent games
                profile = await steam.get_user_profile(resolved_steam_id)
                recent_games = await steam.get_recent_games(resolved_steam_id, limit)
                
                if not profile:
                    await interaction.followup.send(f"❌ Could not access Steam profile. Profile may be private.")
                    return
                    
                if not recent_games:
                    await interaction.followup.send(f"❌ No recent games found for Steam user '{profile['profile_name']}'")
                    return
                    
                await self._show_steam_recent_embed(interaction, recent_games, profile)
                
        except Exception as e:
            logger.error(f"Error getting recent Steam games: {e}")
            await interaction.followup.send(f"❌ Could not retrieve recent Steam games for user '{steam_id}'. Please check the Steam ID.")
    
    @app_commands.command(name='gg-xbox-games', description='Show Xbox game library for a user')
    @app_commands.describe(
        gamertag='Xbox gamertag (defaults to your profile)',
        limit='Number of games to show (1-50)'
    )
    async def show_xbox_games(self, interaction: discord.Interaction, gamertag: str = None, limit: int = 20):
        """Show Xbox game library for a user"""
        await interaction.response.defer()
        
        # If no gamertag provided, try to get from user's profile
        if not gamertag:
            profile = await self.bot.database.get_user_profile(interaction.user.id)
            if not profile or not profile.get('xbox_gamertag'):
                await interaction.followup.send("❌ Please specify an Xbox gamertag or set your profile with `/gg-profile-set`")
                return
            gamertag = profile['xbox_gamertag']
            
        limit = max(1, min(limit, 50))  # Limit between 1 and 50
        
        try:
            async with XboxApiClient() as xbox:
                # Get user profile and games
                profile = await xbox.get_user_profile(gamertag)
                games = await xbox.get_user_games(gamertag, limit)
                
                if not profile:
                    await interaction.followup.send(f"❌ Could not find Xbox gamertag '{gamertag}'")
                    return
                    
                if not games:
                    await interaction.followup.send(f"❌ No games found for Xbox user '{profile['display_name']}'. Profile may be private or have no games.")
                    return
                    
                await self._show_xbox_games_embed(interaction, games, profile)
                
        except Exception as e:
            logger.error(f"Error getting Xbox games: {e}")
            await interaction.followup.send(f"❌ Could not retrieve Xbox games for user '{gamertag}'. Please check the gamertag.")
    
    @app_commands.command(name='gg-xbox-recent', description='Show recently played Xbox games')
    @app_commands.describe(
        gamertag='Xbox gamertag (defaults to your profile)',
        limit='Number of recent games to show (1-20)'
    )
    async def show_xbox_recent(self, interaction: discord.Interaction, gamertag: str = None, limit: int = 10):
        """Show recently played Xbox games"""
        await interaction.response.defer()
        
        # If no gamertag provided, try to get from user's profile
        if not gamertag:
            profile = await self.bot.database.get_user_profile(interaction.user.id)
            if not profile or not profile.get('xbox_gamertag'):
                await interaction.followup.send("❌ Please specify an Xbox gamertag or set your profile with `/gg-profile-set`")
                return
            gamertag = profile['xbox_gamertag']
            
        limit = max(1, min(limit, 20))  # Limit between 1 and 20
        
        try:
            async with XboxApiClient() as xbox:
                # Get user profile and recent games
                profile = await xbox.get_user_profile(gamertag)
                recent_games = await xbox.get_recent_games(gamertag, limit)
                
                if not profile:
                    await interaction.followup.send(f"❌ Could not find Xbox gamertag '{gamertag}'")
                    return
                    
                if not recent_games:
                    await interaction.followup.send(f"❌ No recent games found for Xbox user '{profile['display_name']}'")
                    return
                    
                await self._show_xbox_recent_embed(interaction, recent_games, profile)
                
        except Exception as e:
            logger.error(f"Error getting recent Xbox games: {e}")
            await interaction.followup.send(f"❌ Could not retrieve recent Xbox games for user '{gamertag}'. Please check the gamertag.")
    
    async def _show_steam_games_embed(self, interaction: discord.Interaction, games: List[Dict], profile: Dict):
        """Show Steam games in a rich embed"""
        embed = discord.Embed(
            title=f"🎮 Steam Library for {profile['profile_name']}",
            description=f"Showing {len(games)} games (sorted by recent playtime)",
            color=discord.Color.blue(),
            url=f"https://steamcommunity.com/profiles/{profile['steam_id']}/games/?tab=all"
        )
        
        # Add profile avatar if available
        if profile.get('avatar_url'):
            embed.set_thumbnail(url=profile['avatar_url'])
        
        total_playtime = sum(game.get('playtime_forever', 0) for game in games)
        if total_playtime > 0:
            hours = total_playtime / 60
            embed.add_field(
                name="⏱️ Total Playtime", 
                value=SteamApiClient.format_playtime(total_playtime),
                inline=True
            )
        
        for i, game in enumerate(games[:15], 1):  # Limit to 15 games for embed
            playtime_forever = game.get('playtime_forever', 0)
            playtime_recent = game.get('playtime_2weeks', 0)
            
            game_info = []
            if playtime_forever > 0:
                game_info.append(f"⏱️ Total: {SteamApiClient.format_playtime(playtime_forever)}")
            
            if playtime_recent > 0:
                game_info.append(f"🔥 Recent: {SteamApiClient.format_playtime(playtime_recent)}")
            
            if not game_info:
                game_info.append("❌ Never played")
            
            embed.add_field(
                name=f"{i}. {game['name']}",
                value="\n".join(game_info),
                inline=True
            )
        
        if len(games) > 15:
            embed.add_field(
                name="📎 Note",
                value=f"... and {len(games) - 15} more games",
                inline=False
            )
        
        embed.set_footer(
            text=f"Steam ID: {profile['steam_id']}",
            icon_url="https://store.steampowered.com/favicon.ico"
        )
        
        await interaction.followup.send(embed=embed)
    
    async def _show_steam_recent_embed(self, interaction: discord.Interaction, games: List[Dict], profile: Dict):
        """Show recent Steam games in a rich embed"""
        embed = discord.Embed(
            title=f"🔥 Recent Steam Games for {profile['profile_name']}",
            description=f"Showing {len(games)} recently played games",
            color=discord.Color.blue(),
            url=f"https://steamcommunity.com/profiles/{profile['steam_id']}/games/?tab=recent"
        )
        
        # Add profile avatar if available
        if profile.get('avatar_url'):
            embed.set_thumbnail(url=profile['avatar_url'])
        
        for i, game in enumerate(games, 1):
            playtime_forever = game.get('playtime_forever', 0)
            playtime_recent = game.get('playtime_2weeks', 0)
            
            game_info = []
            if playtime_recent > 0:
                game_info.append(f"🔥 Last 2 weeks: {SteamApiClient.format_playtime(playtime_recent)}")
            
            if playtime_forever > 0:
                game_info.append(f"⏱️ Total: {SteamApiClient.format_playtime(playtime_forever)}")
            
            embed.add_field(
                name=f"{i}. {game['name']}",
                value="\n".join(game_info) if game_info else "Recently played",
                inline=True
            )
        
        embed.set_footer(
            text=f"Steam ID: {profile['steam_id']}",
            icon_url="https://store.steampowered.com/favicon.ico"
        )
        
        await interaction.followup.send(embed=embed)
    
    async def _show_xbox_games_embed(self, interaction: discord.Interaction, games: List[Dict], profile: Dict):
        """Show Xbox games in a rich embed"""
        embed = discord.Embed(
            title=f"🎯 Xbox Library for {profile['display_name']}",
            description=f"Showing {len(games)} games with achievements",
            color=discord.Color.green()
        )
        
        # Add profile avatar if available
        if profile.get('avatar_url'):
            embed.set_thumbnail(url=profile['avatar_url'])
        
        total_gamerscore = sum(game.get('current_gamerscore', 0) for game in games)
        max_gamerscore = sum(game.get('max_gamerscore', 0) for game in games)
        
        if total_gamerscore > 0:
            embed.add_field(
                name="🏆 Total Gamerscore", 
                value=f"{XboxApiClient.format_gamerscore(total_gamerscore)} / {XboxApiClient.format_gamerscore(max_gamerscore)}",
                inline=True
            )
        
        for i, game in enumerate(games[:15], 1):  # Limit to 15 games for embed
            current_score = game.get('current_gamerscore', 0)
            max_score = game.get('max_gamerscore', 0)
            progress = game.get('progress_percentage', 0)
            
            game_info = []
            if current_score > 0 or max_score > 0:
                game_info.append(f"🏆 {current_score} / {max_score} GS")
            
            if progress > 0:
                progress_emoji = XboxApiClient.get_progress_emoji(progress)
                game_info.append(f"{progress_emoji} {progress:.0f}% complete")
            
            current_achievements = game.get('current_achievements', 0)
            total_achievements = game.get('total_achievements', 0)
            if total_achievements > 0:
                game_info.append(f"🏅 {current_achievements}/{total_achievements} achievements")
            
            if not game_info:
                game_info.append("❌ No progress")
            
            embed.add_field(
                name=f"{i}. {game['name']}",
                value="\n".join(game_info),
                inline=True
            )
        
        if len(games) > 15:
            embed.add_field(
                name="📎 Note",
                value=f"... and {len(games) - 15} more games",
                inline=False
            )
        
        embed.set_footer(
            text=f"Xbox Gamertag: {profile['gamertag']}",
            icon_url="https://assets.xboxservices.com/assets/XboxOne/favicon.ico"
        )
        
        await interaction.followup.send(embed=embed)
    
    async def _show_xbox_recent_embed(self, interaction: discord.Interaction, games: List[Dict], profile: Dict):
        """Show recent Xbox games in a rich embed"""
        embed = discord.Embed(
            title=f"🔥 Recent Xbox Games for {profile['display_name']}",
            description=f"Showing {len(games)} recently played games (last 30 days)",
            color=discord.Color.green()
        )
        
        # Add profile avatar if available
        if profile.get('avatar_url'):
            embed.set_thumbnail(url=profile['avatar_url'])
        
        for i, game in enumerate(games, 1):
            current_score = game.get('current_gamerscore', 0)
            max_score = game.get('max_gamerscore', 0)
            progress = game.get('progress_percentage', 0)
            last_unlock = game.get('last_unlock')
            
            game_info = []
            if last_unlock:
                game_info.append(f"📅 Last activity: {last_unlock.strftime('%Y-%m-%d')}")
            
            if current_score > 0 or max_score > 0:
                game_info.append(f"🏆 {current_score} / {max_score} GS")
            
            if progress > 0:
                progress_emoji = XboxApiClient.get_progress_emoji(progress)
                game_info.append(f"{progress_emoji} {progress:.0f}% complete")
            
            embed.add_field(
                name=f"{i}. {game['name']}",
                value="\n".join(game_info) if game_info else "Recently played",
                inline=True
            )
        
        embed.set_footer(
            text=f"Xbox Gamertag: {profile['gamertag']}",
            icon_url="https://assets.xboxservices.com/assets/XboxOne/favicon.ico"
        )
        
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(UserProfilesCog(bot))
