import asyncio
import logging
import os
from typing import Dict, List, Optional, Any
from datetime import datetime

import aiohttp

logger = logging.getLogger(__name__)

class XboxApiClient:
    """Xbox Live API Client - Basic Implementation"""
    
    BASE_URL = "https://xbl.io/api/v2"
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("XBOX_API_KEY")
        self.session: Optional[aiohttp.ClientSession] = None
        
        if not self.api_key:
            logger.warning("Xbox API key not provided. Xbox functionality will be limited.")
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            headers={
                "X-Authorization": self.api_key if self.api_key else "",
                "Accept": "application/json"
            } if self.api_key else {}
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            
    async def search_gamertag(self, gamertag: str) -> Optional[Dict[str, Any]]:
        """Search for a gamertag"""
        if not self.api_key:
            logger.warning("Xbox API key not available for gamertag search")
            return None
            
        try:
            url = f"{self.BASE_URL}/search/{gamertag}"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data and len(data) > 0:
                        return data[0]  # Return first match
                return None
        except Exception as e:
            logger.error(f"Error searching Xbox gamertag: {e}")
            return None
            
    async def get_user_profile(self, gamertag: str) -> Optional[Dict[str, Any]]:
        """Get user profile information"""
        if not self.api_key:
            return {
                "display_name": gamertag,
                "gamertag": gamertag,
                "avatar_url": None
            }
            
        try:
            url = f"{self.BASE_URL}/profile/{gamertag}"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "display_name": data.get("displayName", gamertag),
                        "gamertag": data.get("gamertag", gamertag),
                        "avatar_url": data.get("displayPicRaw")
                    }
                return None
        except Exception as e:
            logger.error(f"Error getting Xbox profile: {e}")
            return None
            
    async def get_user_games(self, gamertag: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get user's games with achievements"""
        if not self.api_key:
            logger.warning("Xbox API key not available for games data")
            return []
            
        try:
            url = f"{self.BASE_URL}/achievements/player/{gamertag}"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    games = data.get("titles", [])[:limit]
                    
                    result = []
                    for game in games:
                        result.append({
                            "name": game.get("name", "Unknown Game"),
                            "current_gamerscore": game.get("currentGamerscore", 0),
                            "max_gamerscore": game.get("maxGamerscore", 0),
                            "progress_percentage": game.get("progressPercentage", 0),
                            "current_achievements": game.get("currentAchievements", 0),
                            "total_achievements": game.get("totalAchievements", 0)
                        })
                    return result
                return []
        except Exception as e:
            logger.error(f"Error getting Xbox games: {e}")
            return []
            
    async def get_recent_games(self, gamertag: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recently played games"""
        # For now, return subset of all games as "recent"
        all_games = await self.get_user_games(gamertag, limit)
        return all_games  # In a full implementation, this would be filtered by recent activity
        
    async def search_games(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for Xbox games (basic implementation)"""
        # Basic implementation - in production this would use Xbox's game search API
        logger.info(f"Xbox game search not fully implemented for query: {query}")
        return []
        
    @staticmethod
    def format_gamerscore(score: int) -> str:
        """Format gamerscore for display"""
        if score >= 1000:
            return f"{score/1000:.1f}K"
        return str(score)
        
    @staticmethod
    def get_progress_emoji(percentage: float) -> str:
        """Get progress emoji based on percentage"""
        if percentage >= 100:
            return "🏆"
        elif percentage >= 75:
            return "🥈"
        elif percentage >= 50:
            return "🥉"
        elif percentage >= 25:
            return "📈"
        else:
            return "📊"
