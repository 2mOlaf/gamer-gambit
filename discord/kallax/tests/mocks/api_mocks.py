"""
API mocks for external services used by Kallax bot.
These mocks simulate responses from BoardGameGeek, Steam, and Xbox APIs.
"""

from typing import Dict, List, Any, Optional
from unittest.mock import AsyncMock, MagicMock
import json
from datetime import datetime, timedelta


class MockBGGApiClient:
    """Mock BoardGameGeek API client"""
    
    def __init__(self):
        self.session = None
        self._mock_games = self._create_mock_bgg_games()
        self._mock_collections = self._create_mock_collections()
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
        
    def _create_mock_bgg_games(self) -> List[Dict[str, Any]]:
        """Create sample BGG game data"""
        return [
            {
                'bgg_id': 174430,
                'name': 'Gloomhaven',
                'year_published': 2017,
                'image_url': 'https://cf.geekdo-images.com/sVYVoN5tKpTqZYXk4j6n5Q__original/img/gloomhaven.jpg',
                'thumbnail_url': 'https://cf.geekdo-images.com/sVYVoN5tKpTqZYXk4j6n5Q__thumb/img/gloomhaven_thumb.jpg',
                'description': 'Gloomhaven is a game of Euro-inspired tactical combat...',
                'min_players': 1,
                'max_players': 4,
                'playing_time': 120,
                'min_playtime': 60,
                'max_playtime': 180,
                'min_age': 14,
                'rating': 8.7,
                'rating_count': 75000,
                'weight': 3.9,
                'categories': ['Adventure', 'Exploration', 'Fantasy'],
                'mechanics': ['Action Point Allowance System', 'Cooperative Play']
            },
            {
                'bgg_id': 167791,
                'name': 'Terraforming Mars',
                'year_published': 2016,
                'image_url': 'https://cf.geekdo-images.com/wg9oOLcsKvDesSUdZQ4rxw__original/img/terraforming_mars.jpg',
                'thumbnail_url': 'https://cf.geekdo-images.com/wg9oOLcsKvDesSUdZQ4rxw__thumb/img/terraforming_mars_thumb.jpg',
                'description': 'In the 2400s, mankind begins to terraform the planet Mars...',
                'min_players': 1,
                'max_players': 5,
                'playing_time': 120,
                'min_playtime': 90,
                'max_playtime': 150,
                'min_age': 12,
                'rating': 8.4,
                'rating_count': 60000,
                'weight': 3.3,
                'categories': ['Economic', 'Science Fiction'],
                'mechanics': ['Card Drafting', 'Tile Placement']
            },
            {
                'bgg_id': 12333,
                'name': 'Twilight Struggle',
                'year_published': 2005,
                'image_url': 'https://cf.geekdo-images.com/twilight_struggle.jpg',
                'thumbnail_url': 'https://cf.geekdo-images.com/twilight_struggle_thumb.jpg',
                'description': 'Relive the Cold War between the United States and Soviet Union...',
                'min_players': 2,
                'max_players': 2,
                'playing_time': 180,
                'min_playtime': 120,
                'max_playtime': 240,
                'min_age': 13,
                'rating': 8.3,
                'rating_count': 55000,
                'weight': 3.6,
                'categories': ['Political', 'Wargame'],
                'mechanics': ['Area Control', 'Card Driven']
            }
        ]
        
    def _create_mock_collections(self) -> Dict[str, List[Dict[str, Any]]]:
        """Create sample user collections"""
        return {
            'testuser': [
                {
                    'bgg_id': 174430,
                    'name': 'Gloomhaven',
                    'year_published': 2017,
                    'owned': True,
                    'previously_owned': False,
                    'want': False,
                    'want_to_play': True,
                    'want_to_buy': False,
                    'wishlist': False,
                    'preordered': False,
                    'for_trade': False,
                    'rating': 9,
                    'num_plays': 15
                },
                {
                    'bgg_id': 167791,
                    'name': 'Terraforming Mars',
                    'year_published': 2016,
                    'owned': True,
                    'previously_owned': False,
                    'want': False,
                    'want_to_play': False,
                    'want_to_buy': False,
                    'wishlist': False,
                    'preordered': False,
                    'for_trade': False,
                    'rating': 8,
                    'num_plays': 8
                }
            ]
        }
        
    async def search_games(self, query: str, include_ratings: bool = False) -> List[Dict[str, Any]]:
        """Mock game search"""
        query_lower = query.lower()
        results = []
        
        for game in self._mock_games:
            if query_lower in game['name'].lower():
                result = game.copy()
                if include_ratings:
                    result['rating'] = game['rating']
                    result['rating_count'] = game['rating_count']
                results.append(result)
                
        return results[:10]  # Limit to 10 results
        
    async def get_game_details(self, bgg_id: int) -> Optional[Dict[str, Any]]:
        """Mock getting detailed game information"""
        for game in self._mock_games:
            if game['bgg_id'] == bgg_id:
                return game.copy()
        return None
        
    async def get_user_collection(self, username: str, statuses: List[str]) -> List[Dict[str, Any]]:
        """Mock getting user's game collection"""
        if username.lower() not in self._mock_collections:
            if 'nonexistent' in username.lower():
                raise Exception(f"User '{username}' not found")
            return []
            
        collection = self._mock_collections[username.lower()]
        
        # Filter by status if specified
        if 'own' in statuses:
            collection = [game for game in collection if game.get('owned', False)]
            
        return collection.copy()
        
    async def get_hot_games(self, game_type: str = 'boardgame') -> List[Dict[str, Any]]:
        """Mock getting hot games list"""
        return [
            {'bgg_id': 999001, 'name': 'Hot Game 1', 'year_published': 2023, 'rank': 1},
            {'bgg_id': 999002, 'name': 'Hot Game 2', 'year_published': 2023, 'rank': 2},
            {'bgg_id': 999003, 'name': 'Hot Game 3', 'year_published': 2022, 'rank': 3}
        ]


class MockSteamApiClient:
    """Mock Steam API client"""
    
    def __init__(self):
        self.session = None
        self._mock_games = self._create_mock_steam_games()
        self._mock_profiles = self._create_mock_profiles()
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
        
    def _create_mock_steam_games(self) -> List[Dict[str, Any]]:
        """Create sample Steam game data"""
        return [
            {
                'app_id': 570,
                'name': 'Dota 2',
                'release_date': '2013',
                'price': 'Free',
                'description': 'Every day, millions of players worldwide enter battle as one of over a hundred Dota heroes...',
                'header_image': 'https://cdn.akamai.steamstatic.com/steam/apps/570/header.jpg',
                'screenshots': ['https://cdn.akamai.steamstatic.com/steam/apps/570/ss_1.jpg'],
                'genres': ['Action', 'Free to Play', 'Strategy'],
                'developers': ['Valve'],
                'publishers': ['Valve'],
                'metacritic_score': 90,
                'positive_reviews': 95,
                'negative_reviews': 5
            },
            {
                'app_id': 730,
                'name': 'Counter-Strike: Global Offensive',
                'release_date': '2012',
                'price': 'Free',
                'description': 'Counter-Strike: Global Offensive expands upon the team-based action gameplay...',
                'header_image': 'https://cdn.akamai.steamstatic.com/steam/apps/730/header.jpg',
                'screenshots': ['https://cdn.akamai.steamstatic.com/steam/apps/730/ss_1.jpg'],
                'genres': ['Action', 'Free to Play'],
                'developers': ['Valve', 'Hidden Path Entertainment'],
                'publishers': ['Valve'],
                'metacritic_score': 83,
                'positive_reviews': 92,
                'negative_reviews': 8
            },
            {
                'app_id': 271590,
                'name': 'Grand Theft Auto V',
                'release_date': '2015',
                'price': '$29.99',
                'description': 'When a young street hustler, a retired bank robber and a terrifying psychopath...',
                'header_image': 'https://cdn.akamai.steamstatic.com/steam/apps/271590/header.jpg',
                'screenshots': ['https://cdn.akamai.steamstatic.com/steam/apps/271590/ss_1.jpg'],
                'genres': ['Action', 'Adventure'],
                'developers': ['Rockstar North'],
                'publishers': ['Rockstar Games'],
                'metacritic_score': 96,
                'positive_reviews': 88,
                'negative_reviews': 12
            }
        ]
        
    def _create_mock_profiles(self) -> Dict[str, Dict[str, Any]]:
        """Create sample Steam profiles"""
        return {
            '76561198000000001': {
                'steam_id': '76561198000000001',
                'display_name': 'TestSteamUser',
                'real_name': 'Test User',
                'avatar_url': 'https://avatars.steamstatic.com/test_avatar.jpg',
                'profile_url': 'https://steamcommunity.com/id/teststeamuser/',
                'created': 1234567890,
                'last_logoff': 1640000000,
                'game_count': 150,
                'level': 25
            },
            'teststeamuser': {  # Custom URL mapping
                'steam_id': '76561198000000001',
                'display_name': 'TestSteamUser',
                'real_name': 'Test User',
                'avatar_url': 'https://avatars.steamstatic.com/test_avatar.jpg',
                'profile_url': 'https://steamcommunity.com/id/teststeamuser/',
                'created': 1234567890,
                'last_logoff': 1640000000,
                'game_count': 150,
                'level': 25
            }
        }
        
    async def search_games(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Mock game search"""
        query_lower = query.lower()
        results = []
        
        for game in self._mock_games:
            if query_lower in game['name'].lower():
                results.append(game.copy())
                
        return results[:limit]
        
    async def get_game_details(self, app_id: int) -> Optional[Dict[str, Any]]:
        """Mock getting detailed game information"""
        for game in self._mock_games:
            if game['app_id'] == app_id:
                return game.copy()
        return None
        
    async def get_steam_id(self, username: str) -> Optional[str]:
        """Mock resolving Steam ID from username"""
        if username in self._mock_profiles:
            return self._mock_profiles[username]['steam_id']
        return None
        
    async def get_user_profile(self, steam_id: str) -> Optional[Dict[str, Any]]:
        """Mock getting user profile"""
        if steam_id in self._mock_profiles:
            return self._mock_profiles[steam_id].copy()
        return None
        
    async def get_user_games(self, steam_id: str) -> List[Dict[str, Any]]:
        """Mock getting user's game library"""
        if steam_id not in self._mock_profiles:
            return []
            
        # Return sample games with playtime
        return [
            {
                'app_id': 570,
                'name': 'Dota 2',
                'playtime_forever': 1200,  # minutes
                'playtime_2weeks': 60
            },
            {
                'app_id': 730,
                'name': 'Counter-Strike: Global Offensive',
                'playtime_forever': 800,
                'playtime_2weeks': 120
            }
        ]


class MockXboxApiClient:
    """Mock Xbox API client"""
    
    def __init__(self):
        self.session = None
        self._mock_games = self._create_mock_xbox_games()
        self._mock_profiles = self._create_mock_xbox_profiles()
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
        
    def _create_mock_xbox_games(self) -> List[Dict[str, Any]]:
        """Create sample Xbox game data"""
        return [
            {
                'product_id': '9NBLGGH4R6P9',
                'name': 'Halo Infinite',
                'release_date': '2021',
                'price': 'Free',
                'description': 'Master Chief returns in Halo Infinite – the next chapter of the legendary franchise.',
                'image_url': 'https://store-images.s-microsoft.com/image/halo_infinite.jpg',
                'genres': ['Shooter', 'Action'],
                'developer': '343 Industries',
                'publisher': 'Xbox Game Studios',
                'rating': 'M',
                'platforms': ['Xbox Series X|S', 'Xbox One', 'PC']
            },
            {
                'product_id': '9P3J32CTXLRZ',
                'name': 'Forza Horizon 5',
                'release_date': '2021',
                'price': '$59.99',
                'description': 'Your greatest Horizon Adventure awaits! Explore the vibrant and ever-evolving open world landscapes of Mexico.',
                'image_url': 'https://store-images.s-microsoft.com/image/forza_horizon_5.jpg',
                'genres': ['Racing & Flying', 'Sports'],
                'developer': 'Playground Games',
                'publisher': 'Xbox Game Studios',
                'rating': 'T',
                'platforms': ['Xbox Series X|S', 'Xbox One', 'PC']
            },
            {
                'product_id': '9MW7XDZ0DH8J',
                'name': 'Microsoft Flight Simulator',
                'release_date': '2020',
                'price': '$59.99',
                'description': 'From light planes to wide-body jets, fly highly detailed and accurate aircraft in the next generation of Microsoft Flight Simulator.',
                'image_url': 'https://store-images.s-microsoft.com/image/flight_simulator.jpg',
                'genres': ['Simulation', 'Racing & Flying'],
                'developer': 'Asobo Studio',
                'publisher': 'Xbox Game Studios',
                'rating': 'E',
                'platforms': ['Xbox Series X|S', 'PC']
            }
        ]
        
    def _create_mock_xbox_profiles(self) -> Dict[str, Dict[str, Any]]:
        """Create sample Xbox profiles"""
        return {
            'testxboxuser': {
                'gamertag': 'TestXboxUser',
                'xuid': '2533274792395555',
                'display_name': 'TestXboxUser',
                'real_name': 'Test Xbox User',
                'gamer_pic': 'https://images-eds-ssl.xboxlive.com/image/test_avatar.png',
                'gamerscore': 15000,
                'tier': 'Gold',
                'reputation': 'GoodPlayer',
                'following_count': 50,
                'followers_count': 75
            }
        }
        
    async def search_games(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Mock game search"""
        query_lower = query.lower()
        results = []
        
        for game in self._mock_games:
            if query_lower in game['name'].lower():
                results.append(game.copy())
                
        return results[:limit]
        
    async def get_game_details(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Mock getting detailed game information"""
        for game in self._mock_games:
            if game['product_id'] == product_id:
                return game.copy()
        return None
        
    async def search_gamertag(self, gamertag: str) -> Optional[Dict[str, Any]]:
        """Mock searching for gamertag"""
        if gamertag.lower() in self._mock_profiles:
            return self._mock_profiles[gamertag.lower()].copy()
        if 'nonexistent' in gamertag.lower():
            return None
        # Return basic profile for unknown but valid gamertags
        return {
            'gamertag': gamertag,
            'xuid': '2533274792395999',
            'display_name': gamertag,
            'gamer_pic': 'https://images-eds-ssl.xboxlive.com/image/default_avatar.png',
            'gamerscore': 1000
        }
        
    async def get_user_achievements(self, xuid: str, title_id: str = None) -> List[Dict[str, Any]]:
        """Mock getting user achievements"""
        return [
            {
                'achievement_id': 'test_achievement_1',
                'name': 'First Steps',
                'description': 'Complete the tutorial',
                'unlocked': True,
                'unlock_time': '2023-01-15T10:30:00Z',
                'gamerscore': 10
            },
            {
                'achievement_id': 'test_achievement_2',
                'name': 'Master Player',
                'description': 'Reach level 50',
                'unlocked': False,
                'gamerscore': 50
            }
        ]


# Mock factory functions
def create_mock_bgg_client() -> MockBGGApiClient:
    """Create a mock BGG API client"""
    return MockBGGApiClient()


def create_mock_steam_client() -> MockSteamApiClient:
    """Create a mock Steam API client"""
    return MockSteamApiClient()


def create_mock_xbox_client() -> MockXboxApiClient:
    """Create a mock Xbox API client"""
    return MockXboxApiClient()


# API response builders for testing different scenarios
class MockApiResponseBuilder:
    """Builder for creating various API response scenarios"""
    
    @staticmethod
    def bgg_empty_search() -> List[Dict[str, Any]]:
        """Empty BGG search result"""
        return []
        
    @staticmethod
    def bgg_error_response() -> Exception:
        """BGG API error"""
        return Exception("BGG API Error: Rate limit exceeded")
        
    @staticmethod
    def steam_private_profile() -> Exception:
        """Steam private profile error"""
        return Exception("Profile is private")
        
    @staticmethod
    def xbox_network_error() -> Exception:
        """Xbox network error"""
        return Exception("Network error: Connection timeout")


# Export all mock classes and functions
__all__ = [
    'MockBGGApiClient',
    'MockSteamApiClient', 
    'MockXboxApiClient',
    'MockApiResponseBuilder',
    'create_mock_bgg_client',
    'create_mock_steam_client',
    'create_mock_xbox_client'
]
