import asyncio
import logging
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import os

import aiohttp

logger = logging.getLogger(__name__)

class SteamApiClient:
    """Steam Web API Client"""
    
    BASE_URL = "https://api.steampowered.com"
    STORE_URL = "https://store.steampowered.com/api"
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("STEAM_API_KEY")
        self.session: Optional[aiohttp.ClientSession] = None
        
        if not self.api_key:
            logger.warning("Steam API key not provided. Some functionality will be limited.")
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            
    async def get_steam_id(self, steam_input: str) -> Optional[str]:
        """Resolve Steam ID from various input formats"""
        if not self.api_key:
            logger.warning("Steam API key required for ID resolution")
            return None
            
        # Check if it's already a SteamID64 (17 digits starting with 765)
        if steam_input.isdigit() and len(steam_input) == 17 and steam_input.startswith('765'):
            return steam_input
            
        # Try to resolve custom URL/vanity URL
        try:
            url = f"{self.BASE_URL}/ISteamUser/ResolveVanityURL/v0001/"
            params = {
                'key': self.api_key,
                'vanityurl': steam_input,
                'url_type': 1
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('response', {}).get('success') == 1:
                        return data['response']['steamid']
                        
            # If vanity URL resolution failed, try as direct SteamID64
            return steam_input if steam_input.isdigit() else None
            
        except Exception as e:
            logger.error(f"Error resolving Steam ID: {e}")
            return None
            
    async def get_user_profile(self, steam_id: str) -> Optional[Dict[str, Any]]:
        """Get Steam user profile information"""
        if not self.api_key:
            logger.warning("Steam API key required for user profiles")
            return None
            
        try:
            url = f"{self.BASE_URL}/ISteamUser/GetPlayerSummaries/v0002/"
            params = {
                'key': self.api_key,
                'steamids': steam_id
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    players = data.get('response', {}).get('players', [])
                    if players:
                        player = players[0]
                        return {
                            'steam_id': player.get('steamid'),
                            'profile_name': player.get('personaname'),
                            'real_name': player.get('realname'),
                            'avatar_url': player.get('avatarfull'),
                            'profile_url': player.get('profileurl'),
                            'profile_state': player.get('profilestate'),
                            'visibility_state': player.get('communityvisibilitystate')
                        }
            return None
            
        except Exception as e:
            logger.error(f"Error getting Steam profile: {e}")
            return None
            
    async def get_user_games(self, steam_id: str) -> List[Dict[str, Any]]:
        """Get user's owned games"""
        if not self.api_key:
            logger.warning("Steam API key required for games list")
            return []
            
        try:
            url = f"{self.BASE_URL}/IPlayerService/GetOwnedGames/v0001/"
            params = {
                'key': self.api_key,
                'steamid': steam_id,
                'format': 'json',
                'include_appinfo': 'true',
                'include_played_free_games': 'true'
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    games = data.get('response', {}).get('games', [])
                    
                    # Sort by playtime (most played first)
                    games.sort(key=lambda x: x.get('playtime_forever', 0), reverse=True)
                    
                    result = []
                    for game in games:
                        result.append({
                            'app_id': game.get('appid'),
                            'name': game.get('name', 'Unknown Game'),
                            'playtime_forever': game.get('playtime_forever', 0),
                            'playtime_2weeks': game.get('playtime_2weeks', 0),
                            'img_icon_url': game.get('img_icon_url'),
                            'img_logo_url': game.get('img_logo_url')
                        })
                    return result
            return []
            
        except Exception as e:
            logger.error(f"Error getting Steam games: {e}")
            return []
            
    async def get_recent_games(self, steam_id: str, count: int = 10) -> List[Dict[str, Any]]:
        """Get recently played games"""
        if not self.api_key:
            logger.warning("Steam API key required for recent games")
            return []
            
        try:
            url = f"{self.BASE_URL}/IPlayerService/GetRecentlyPlayedGames/v0001/"
            params = {
                'key': self.api_key,
                'steamid': steam_id,
                'count': count,
                'format': 'json'
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    games = data.get('response', {}).get('games', [])
                    
                    result = []
                    for game in games:
                        result.append({
                            'app_id': game.get('appid'),
                            'name': game.get('name', 'Unknown Game'),
                            'playtime_forever': game.get('playtime_forever', 0),
                            'playtime_2weeks': game.get('playtime_2weeks', 0),
                            'img_icon_url': game.get('img_icon_url'),
                            'img_logo_url': game.get('img_logo_url')
                        })
                    return result
            return []
            
        except Exception as e:
            logger.error(f"Error getting recent Steam games: {e}")
            return []
            
    async def search_games(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search Steam games with enriched data"""
        try:
            # Use Steam store search API
            url = f"{self.STORE_URL}/storesearch/"
            params = {
                'term': query,
                'l': 'english',
                'cc': 'US'
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    items = data.get('items', [])[:limit]
                    
                    result = []
                    for item in items:
                        if item.get('type') == 'app':  # Only games, not DLC/bundles
                            # Get basic search result data
                            game_data = {
                                'app_id': item.get('id'),
                                'name': item.get('name', 'Unknown Game'),
                                'price': item.get('price', {}).get('final_formatted', 'N/A'),
                                'release_date': item.get('release_date'),
                                'capsule_image': item.get('tiny_image'),
                                'metacritic_score': item.get('metascore'),
                                'type': item.get('type')
                            }
                            
                            # Try to get enhanced data if available in search results
                            if item.get('header_image'):
                                game_data['header_image'] = item.get('header_image')
                            if item.get('discount'):
                                game_data['discount'] = item.get('discount')
                            if item.get('platforms'):
                                game_data['platforms'] = item.get('platforms')
                            
                            result.append(game_data)
                    return result
            return []
            
        except Exception as e:
            logger.error(f"Error searching Steam games: {e}")
            return []
            
    async def get_game_details(self, app_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific game"""
        try:
            url = f"{self.STORE_URL}/appdetails/"
            params = {
                'appids': app_id,
                'l': 'english'
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    app_data = data.get(str(app_id), {})
                    
                    if app_data.get('success') and app_data.get('data'):
                        game_data = app_data['data']
                        return {
                            'app_id': app_id,
                            'name': game_data.get('name'),
                            'description': game_data.get('short_description'),
                            'header_image': game_data.get('header_image'),
                            'capsule_image': game_data.get('capsule_image'),
                            'developers': game_data.get('developers', []),
                            'publishers': game_data.get('publishers', []),
                            'release_date': game_data.get('release_date', {}).get('date'),
                            'price': game_data.get('price_overview', {}).get('final_formatted'),
                            'platforms': game_data.get('platforms', {}),
                            'metacritic_score': game_data.get('metacritic', {}).get('score'),
                            'genres': [g.get('description') for g in game_data.get('genres', [])],
                            'achievements': game_data.get('achievements', {}).get('total')
                        }
            return None
            
        except Exception as e:
            logger.error(f"Error getting game details: {e}")
            return None
            
    @staticmethod
    def format_playtime(minutes: int) -> str:
        """Format playtime in minutes to human readable format"""
        if minutes == 0:
            return "Never played"
        elif minutes < 60:
            return f"{minutes} min"
        else:
            hours = minutes / 60
            if hours < 1000:
                return f"{hours:.1f} hrs"
            else:
                return f"{hours:,.0f} hrs"
