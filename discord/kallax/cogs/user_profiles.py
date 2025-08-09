import discord
from discord.ext import commands
import asyncio
import logging
from typing import Dict, Any, Optional, List
import json

from utils.bgg_api import BGGApiClient

logger = logging.getLogger(__name__)

class UserProfilesCog(commands.Cog):
    """User profile management and collection display"""
    
    def __init__(self, bot):
        self.bot = bot
        
    @commands.group(name='profile', aliases=['me', 'user'])
    async def profile(self, ctx):
        """User profile management commands"""
        if ctx.invoked_subcommand is None:
            # Show user's own profile
            await self._show_profile(ctx, ctx.author.id)
            
    @profile.command(name='set')
    async def set_profile(self, ctx, platform: str, *, username: str):
        """Set your profile information for various gaming platforms
        
        Usage: !profile set <platform> <username>
        Platforms: bgg, steam, xbox
        Example: !profile set bgg myBGGusername
        """
        platform = platform.lower()
        valid_platforms = {'bgg': 'bgg_username', 'steam': 'steam_id', 'xbox': 'xbox_gamertag'}
        
        if platform not in valid_platforms:
            await ctx.send(f"❌ Invalid platform. Valid options: {', '.join(valid_platforms.keys())}")
            return
            
        username = username.strip()
        if not username:
            await ctx.send("❌ Please provide a valid username")
            return
            
        # Validate BGG username by checking if it exists
        if platform == 'bgg':
            async with ctx.typing():
                try:
                    async with BGGApiClient() as bgg:
                        collection = await bgg.get_user_collection(username, ['own'])
                        # If no exception and we get a response (even empty), user exists
                        
                except Exception as e:
                    logger.error(f"BGG validation error: {e}")
                    await ctx.send(f"❌ Could not find BGG user '{username}'. Please check the username and try again.")
                    return
        
        # Update user profile
        profile_data = {valid_platforms[platform]: username}
        
        try:
            success = await self.bot.database.update_user_profile(ctx.author.id, **profile_data)
            if success:
                await ctx.send(f"✅ {platform.upper()} profile set to: **{username}**")
            else:
                # Create profile if update failed
                success = await self.bot.database.create_user_profile(ctx.author.id, **profile_data)
                if success:
                    await ctx.send(f"✅ Profile created! {platform.upper()} username set to: **{username}**")
                else:
                    await ctx.send("❌ Failed to update profile. Please try again.")
        except Exception as e:
            logger.error(f"Error updating profile: {e}")
            await ctx.send("❌ An error occurred while updating your profile.")
    
    @profile.command(name='show')
    async def show_profile(self, ctx, user: discord.Member = None):
        """Show a user's profile information
        
        Usage: !profile show [@user]
        Example: !profile show @SomeUser
        """
        target_user = user or ctx.author
        await self._show_profile(ctx, target_user.id, target_user)
        
    async def _show_profile(self, ctx, discord_id: int, discord_user: discord.Member = None):
        """Internal method to show user profile"""
        try:
            profile = await self.bot.database.get_user_profile(discord_id)
            
            if not profile:
                if discord_id == ctx.author.id:
                    await ctx.send("❌ You don't have a profile yet. Use `!profile set bgg <username>` to get started!")
                else:
                    username = discord_user.display_name if discord_user else "User"
                    await ctx.send(f"❌ {username} doesn't have a profile set up yet.")
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
            
            embed.set_footer(text="Use !profile set <platform> <username> to update your profile")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error showing profile: {e}")
            await ctx.send("❌ An error occurred while retrieving the profile.")
    
    @commands.command(name='collection', aliases=['coll'])
    async def show_collection(self, ctx, username: str = None, collection_type: str = "own"):
        """Show BGG collection for a user
        
        Usage: !collection [username] [type]
        Types: own, wishlist, fortrade, want
        Example: !collection myBGGuser own
        """
        # If no username provided, try to get from user's profile
        if not username:
            profile = await self.bot.database.get_user_profile(ctx.author.id)
            if not profile or not profile.get('bgg_username'):
                await ctx.send("❌ Please specify a BGG username or set your profile with `!profile set bgg <username>`")
                return
            username = profile['bgg_username']
            
        collection_type = collection_type.lower()
        valid_types = ['own', 'wishlist', 'fortrade', 'want']
        
        if collection_type not in valid_types:
            collection_type = 'own'
            
        async with ctx.typing():
            try:
                async with BGGApiClient() as bgg:
                    collection = await bgg.get_user_collection(username, [collection_type])
                    
                    if not collection:
                        type_name = collection_type.replace('fortrade', 'for trade').title()
                        await ctx.send(f"❌ No games found in {username}'s {type_name} collection")
                        return
                        
                    await self._show_collection_pages(ctx, collection, username, collection_type)
                    
            except Exception as e:
                logger.error(f"Error getting collection: {e}")
                await ctx.send(f"❌ Could not retrieve collection for user '{username}'. Please check the username.")
    
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
                    
    @commands.command(name='plays', aliases=['games'])
    async def show_recent_plays(self, ctx, username: str = None, limit: int = 10):
        """Show recent game plays from BGG
        
        Usage: !plays [username] [limit]
        Example: !plays myBGGuser 20
        """
        # If no username provided, try to get from user's profile
        if not username:
            profile = await self.bot.database.get_user_profile(ctx.author.id)
            if not profile or not profile.get('bgg_username'):
                await ctx.send("❌ Please specify a BGG username or set your profile with `!profile set bgg <username>`")
                return
            username = profile['bgg_username']
            
        limit = max(1, min(limit, 50))  # Limit between 1 and 50
        
        async with ctx.typing():
            try:
                async with BGGApiClient() as bgg:
                    plays_data = await bgg.get_user_plays(username, page=1)
                    plays = plays_data.get('plays', [])[:limit]
                    
                    if not plays:
                        await ctx.send(f"❌ No recent plays found for user '{username}'")
                        return
                        
                    await self._show_plays_embed(ctx, plays, username, plays_data.get('total', 0))
                    
            except Exception as e:
                logger.error(f"Error getting plays: {e}")
                await ctx.send(f"❌ Could not retrieve plays for user '{username}'. Please check the username.")
                
    async def _show_plays_embed(self, ctx, plays: List[Dict], username: str, total_plays: int):
        """Show plays in a rich embed"""
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
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(UserProfilesCog(bot))
