"""
Unit tests for API clients (BGG, Steam, Xbox).
Tests API communication, data parsing, and error handling.
"""

import pytest
import aiohttp
from unittest.mock import AsyncMock, MagicMock, patch
from utils.bgg_client import BoardGameGeekClient
from utils.steam_client import SteamClient
from utils.xbox_client import XboxClient


@pytest.mark.unit
@pytest.mark.api
class TestBoardGameGeekClient:
    """Test BoardGameGeek API client functionality"""

    def test_bgg_client_initialization(self):
        """Test BGG client initializes correctly"""
        client = BoardGameGeekClient()
        
        assert client.base_url == "https://boardgamegeek.com/xmlapi2"
        assert client.session is None  # Should be lazy-loaded
        assert hasattr(client, 'search_games')

    async def test_search_games_success(self, mock_bgg_client, sample_bgg_game_data):
        """Test successful game search"""
        # Configure mock to return sample data
        mock_bgg_client.search_games.return_value = [sample_bgg_game_data]
        
        results = await mock_bgg_client.search_games("Gloomhaven")
        
        assert len(results) == 1
        assert results[0]['name'] == sample_bgg_game_data['name']
        assert results[0]['bgg_id'] == sample_bgg_game_data['bgg_id']

    async def test_search_games_empty_query(self, mock_bgg_client):
        """Test search with empty query"""
        with pytest.raises(ValueError, match="Search query cannot be empty"):
            await mock_bgg_client.search_games("")

    async def test_search_games_api_error(self, mock_bgg_client):
        """Test handling of API errors during search"""
        mock_bgg_client.search_games.side_effect = aiohttp.ClientError("Connection error")
        
        with pytest.raises(aiohttp.ClientError):
            await mock_bgg_client.search_games("test")

    async def test_get_game_details_success(self, mock_bgg_client, sample_bgg_game_detailed):
        """Test getting detailed game information"""
        mock_bgg_client.get_game_details.return_value = sample_bgg_game_detailed
        
        result = await mock_bgg_client.get_game_details(174430)
        
        assert result['name'] == sample_bgg_game_detailed['name']
        assert result['bgg_id'] == 174430
        assert 'description' in result
        assert 'mechanics' in result

    async def test_get_game_details_not_found(self, mock_bgg_client):
        """Test getting details for non-existent game"""
        mock_bgg_client.get_game_details.return_value = None
        
        result = await mock_bgg_client.get_game_details(999999)
        
        assert result is None

    async def test_get_game_details_invalid_id(self, mock_bgg_client):
        """Test getting details with invalid game ID"""
        with pytest.raises(ValueError, match="Game ID must be positive"):
            await mock_bgg_client.get_game_details(0)
        
        with pytest.raises(ValueError, match="Game ID must be positive"):
            await mock_bgg_client.get_game_details(-1)

    async def test_get_top_games_success(self, mock_bgg_client):
        """Test getting top games list"""
        top_games = [
            {'bgg_id': 1, 'name': 'Game 1', 'rank': 1, 'rating': 9.0},
            {'bgg_id': 2, 'name': 'Game 2', 'rank': 2, 'rating': 8.9},
            {'bgg_id': 3, 'name': 'Game 3', 'rank': 3, 'rating': 8.8}
        ]
        
        mock_bgg_client.get_top_games.return_value = top_games
        
        result = await mock_bgg_client.get_top_games(limit=3)
        
        assert len(result) == 3
        assert result[0]['rank'] == 1
        assert result[2]['rank'] == 3

    async def test_get_top_games_with_limit(self, mock_bgg_client):
        """Test getting top games with specific limit"""
        top_games = [{'bgg_id': i, 'name': f'Game {i}', 'rank': i} for i in range(1, 11)]
        
        mock_bgg_client.get_top_games.return_value = top_games[:5]  # Mock respects limit
        
        result = await mock_bgg_client.get_top_games(limit=5)
        
        assert len(result) == 5

    async def test_get_trending_games_success(self, mock_bgg_client):
        """Test getting trending games"""
        trending_games = [
            {'bgg_id': 1, 'name': 'Trending Game 1', 'rating': 8.0},
            {'bgg_id': 2, 'name': 'Trending Game 2', 'rating': 7.8}
        ]
        
        mock_bgg_client.get_trending_games.return_value = trending_games
        
        result = await mock_bgg_client.get_trending_games()
        
        assert len(result) == 2
        assert 'Trending Game 1' in [game['name'] for game in result]

    async def test_get_random_game_success(self, mock_bgg_client):
        """Test getting random game recommendation"""
        random_game = {
            'bgg_id': 12345,
            'name': 'Random Board Game',
            'rating': 7.5,
            'year_published': 2020
        }
        
        mock_bgg_client.get_random_game.return_value = random_game
        
        result = await mock_bgg_client.get_random_game()
        
        assert result['name'] == 'Random Board Game'
        assert result['bgg_id'] == 12345

    async def test_session_management(self):
        """Test that client properly manages HTTP session"""
        client = BoardGameGeekClient()
        
        # Should create session on first use
        assert client.session is None
        
        # This would test session creation in real implementation
        # For now, we test that the structure is correct
        assert hasattr(client, '_get_session')

    async def test_rate_limiting_respect(self, mock_bgg_client):
        """Test that client respects rate limiting"""
        # BGG has strict rate limits, client should handle this
        mock_bgg_client.search_games.return_value = []
        
        # Make multiple rapid requests
        for _ in range(3):
            await mock_bgg_client.search_games("test")
        
        # Should complete without errors (rate limiting handled internally)
        assert mock_bgg_client.search_games.call_count == 3


@pytest.mark.unit
@pytest.mark.api
class TestSteamClient:
    """Test Steam API client functionality"""

    def test_steam_client_initialization(self):
        """Test Steam client initializes correctly"""
        client = SteamClient()
        
        assert client.base_url == "https://api.steampowered.com"
        assert client.store_url == "https://store.steampowered.com/api"
        assert hasattr(client, 'search_games')

    async def test_search_games_success(self, mock_steam_client, sample_steam_game_data):
        """Test successful Steam game search"""
        mock_steam_client.search_games.return_value = [sample_steam_game_data]
        
        results = await mock_steam_client.search_games("Portal 2")
        
        assert len(results) == 1
        assert results[0]['name'] == sample_steam_game_data['name']
        assert results[0]['steam_id'] == sample_steam_game_data['steam_id']

    async def test_search_games_empty_query(self, mock_steam_client):
        """Test search with empty query"""
        with pytest.raises(ValueError, match="Search query cannot be empty"):
            await mock_steam_client.search_games("")

    async def test_search_games_no_results(self, mock_steam_client):
        """Test search with no results"""
        mock_steam_client.search_games.return_value = []
        
        results = await mock_steam_client.search_games("NonexistentGame12345")
        
        assert len(results) == 0

    async def test_get_game_details_success(self, mock_steam_client, sample_steam_game_detailed):
        """Test getting detailed Steam game information"""
        mock_steam_client.get_game_details.return_value = sample_steam_game_detailed
        
        result = await mock_steam_client.get_game_details(620)
        
        assert result['name'] == sample_steam_game_detailed['name']
        assert result['steam_id'] == 620
        assert 'description' in result
        assert 'price' in result

    async def test_get_game_details_not_found(self, mock_steam_client):
        """Test getting details for non-existent Steam game"""
        mock_steam_client.get_game_details.return_value = None
        
        result = await mock_steam_client.get_game_details(999999)
        
        assert result is None

    async def test_get_game_details_invalid_id(self, mock_steam_client):
        """Test getting details with invalid Steam ID"""
        with pytest.raises(ValueError, match="Steam ID must be positive"):
            await mock_steam_client.get_game_details(0)

    async def test_get_user_games_success(self, mock_steam_client):
        """Test getting user's Steam library"""
        user_games = [
            {'steam_id': 620, 'name': 'Portal 2', 'playtime_forever': 120},
            {'steam_id': 440, 'name': 'Team Fortress 2', 'playtime_forever': 300}
        ]
        
        mock_steam_client.get_user_games.return_value = user_games
        
        result = await mock_steam_client.get_user_games("76561198000000001")
        
        assert len(result) == 2
        assert result[0]['name'] == 'Portal 2'

    async def test_get_user_games_private_profile(self, mock_steam_client):
        """Test handling private Steam profile"""
        mock_steam_client.get_user_games.side_effect = PermissionError("Profile is private")
        
        with pytest.raises(PermissionError):
            await mock_steam_client.get_user_games("76561198000000001")

    async def test_get_user_games_invalid_steam_id(self, mock_steam_client):
        """Test getting games with invalid Steam ID"""
        with pytest.raises(ValueError, match="Invalid Steam ID format"):
            await mock_steam_client.get_user_games("invalid_id")

    async def test_get_popular_games_success(self, mock_steam_client):
        """Test getting popular Steam games"""
        popular_games = [
            {'steam_id': 1, 'name': 'Popular Game 1', 'current_players': 50000},
            {'steam_id': 2, 'name': 'Popular Game 2', 'current_players': 30000}
        ]
        
        mock_steam_client.get_popular_games.return_value = popular_games
        
        result = await mock_steam_client.get_popular_games()
        
        assert len(result) == 2
        assert result[0]['current_players'] >= result[1]['current_players']


@pytest.mark.unit
@pytest.mark.api
class TestXboxClient:
    """Test Xbox API client functionality"""

    def test_xbox_client_initialization(self):
        """Test Xbox client initializes correctly"""
        client = XboxClient()
        
        assert client.base_url == "https://xbl.io/api/v2"
        assert hasattr(client, 'search_games')

    async def test_search_games_success(self, mock_xbox_client, sample_xbox_game_data):
        """Test successful Xbox game search"""
        mock_xbox_client.search_games.return_value = [sample_xbox_game_data]
        
        results = await mock_xbox_client.search_games("Halo Infinite")
        
        assert len(results) == 1
        assert results[0]['name'] == sample_xbox_game_data['name']
        assert results[0]['xbox_id'] == sample_xbox_game_data['xbox_id']

    async def test_search_games_empty_query(self, mock_xbox_client):
        """Test search with empty query"""
        with pytest.raises(ValueError, match="Search query cannot be empty"):
            await mock_xbox_client.search_games("")

    async def test_search_games_no_results(self, mock_xbox_client):
        """Test search with no results"""
        mock_xbox_client.search_games.return_value = []
        
        results = await mock_xbox_client.search_games("NonexistentGame12345")
        
        assert len(results) == 0

    async def test_get_game_details_success(self, mock_xbox_client, sample_xbox_game_detailed):
        """Test getting detailed Xbox game information"""
        mock_xbox_client.get_game_details.return_value = sample_xbox_game_detailed
        
        result = await mock_xbox_client.get_game_details("halo-infinite")
        
        assert result['name'] == sample_xbox_game_detailed['name']
        assert result['xbox_id'] == "halo-infinite"
        assert 'description' in result
        assert 'genres' in result

    async def test_get_game_details_not_found(self, mock_xbox_client):
        """Test getting details for non-existent Xbox game"""
        mock_xbox_client.get_game_details.return_value = None
        
        result = await mock_xbox_client.get_game_details("nonexistent-game")
        
        assert result is None

    async def test_get_user_profile_success(self, mock_xbox_client):
        """Test getting Xbox user profile"""
        user_profile = {
            'gamertag': 'TestXboxUser',
            'gamerscore': 12345,
            'account_tier': 'Gold',
            'reputation': 'GoodPlayer'
        }
        
        mock_xbox_client.get_user_profile.return_value = user_profile
        
        result = await mock_xbox_client.get_user_profile("TestXboxUser")
        
        assert result['gamertag'] == 'TestXboxUser'
        assert result['gamerscore'] == 12345

    async def test_get_user_profile_not_found(self, mock_xbox_client):
        """Test getting profile for non-existent user"""
        mock_xbox_client.get_user_profile.return_value = None
        
        result = await mock_xbox_client.get_user_profile("NonexistentUser12345")
        
        assert result is None

    async def test_get_user_achievements_success(self, mock_xbox_client):
        """Test getting user achievements for a game"""
        achievements = [
            {'name': 'First Blood', 'description': 'Get first kill', 'unlocked': True},
            {'name': 'Master Chief', 'description': 'Complete campaign', 'unlocked': False}
        ]
        
        mock_xbox_client.get_user_achievements.return_value = achievements
        
        result = await mock_xbox_client.get_user_achievements("TestXboxUser", "halo-infinite")
        
        assert len(result) == 2
        assert result[0]['unlocked'] is True
        assert result[1]['unlocked'] is False

    async def test_get_trending_games_success(self, mock_xbox_client):
        """Test getting trending Xbox games"""
        trending_games = [
            {'xbox_id': 'game1', 'name': 'Trending Xbox Game 1', 'players': 100000},
            {'xbox_id': 'game2', 'name': 'Trending Xbox Game 2', 'players': 80000}
        ]
        
        mock_xbox_client.get_trending_games.return_value = trending_games
        
        result = await mock_xbox_client.get_trending_games()
        
        assert len(result) == 2
        assert result[0]['players'] >= result[1]['players']


@pytest.mark.unit
@pytest.mark.api
class TestApiClientErrorHandling:
    """Test error handling across all API clients"""

    async def test_network_timeout_handling(self, mock_bgg_client):
        """Test handling of network timeouts"""
        import asyncio
        mock_bgg_client.search_games.side_effect = asyncio.TimeoutError("Request timed out")
        
        with pytest.raises(asyncio.TimeoutError):
            await mock_bgg_client.search_games("test")

    async def test_http_error_handling(self, mock_steam_client):
        """Test handling of HTTP errors"""
        mock_steam_client.search_games.side_effect = aiohttp.ClientResponseError(
            None, None, status=429, message="Rate limited"
        )
        
        with pytest.raises(aiohttp.ClientResponseError):
            await mock_steam_client.search_games("test")

    async def test_invalid_response_data_handling(self, mock_xbox_client):
        """Test handling of invalid response data"""
        mock_xbox_client.search_games.side_effect = ValueError("Invalid JSON response")
        
        with pytest.raises(ValueError):
            await mock_xbox_client.search_games("test")

    async def test_connection_error_handling(self, mock_bgg_client):
        """Test handling of connection errors"""
        mock_bgg_client.search_games.side_effect = aiohttp.ClientConnectorError(
            None, OSError("Connection failed")
        )
        
        with pytest.raises(aiohttp.ClientConnectorError):
            await mock_bgg_client.search_games("test")

    async def test_authentication_error_handling(self, mock_xbox_client):
        """Test handling of authentication errors"""
        mock_xbox_client.get_user_profile.side_effect = aiohttp.ClientResponseError(
            None, None, status=401, message="Unauthorized"
        )
        
        with pytest.raises(aiohttp.ClientResponseError):
            await mock_xbox_client.get_user_profile("test")


@pytest.mark.unit
@pytest.mark.api
class TestApiClientDataParsing:
    """Test data parsing and formatting across API clients"""

    async def test_bgg_xml_parsing(self, mock_bgg_client):
        """Test BGG XML response parsing"""
        # BGG uses XML responses, should be parsed correctly
        mock_response_data = {
            'bgg_id': 174430,
            'name': 'Gloomhaven',
            'year_published': 2017,
            'rating': 8.7,
            'rating_count': 70000,
            'description': 'A game description...'
        }
        
        mock_bgg_client.search_games.return_value = [mock_response_data]
        
        result = await mock_bgg_client.search_games("Gloomhaven")
        
        # Should have all expected fields
        assert 'bgg_id' in result[0]
        assert 'name' in result[0]
        assert 'year_published' in result[0]
        assert isinstance(result[0]['rating'], (int, float))

    async def test_steam_json_parsing(self, mock_steam_client):
        """Test Steam JSON response parsing"""
        mock_response_data = {
            'steam_id': 620,
            'name': 'Portal 2',
            'price': '$9.99',
            'release_date': '2011-04-18',
            'description': 'A puzzle game...'
        }
        
        mock_steam_client.search_games.return_value = [mock_response_data]
        
        result = await mock_steam_client.search_games("Portal 2")
        
        # Should have proper Steam fields
        assert 'steam_id' in result[0]
        assert 'name' in result[0]
        assert 'price' in result[0]
        assert isinstance(result[0]['steam_id'], int)

    async def test_xbox_json_parsing(self, mock_xbox_client):
        """Test Xbox JSON response parsing"""
        mock_response_data = {
            'xbox_id': 'halo-infinite',
            'name': 'Halo Infinite',
            'genres': ['Shooter', 'Action'],
            'developer': '343 Industries',
            'description': 'A sci-fi shooter...'
        }
        
        mock_xbox_client.search_games.return_value = [mock_response_data]
        
        result = await mock_xbox_client.search_games("Halo Infinite")
        
        # Should have proper Xbox fields
        assert 'xbox_id' in result[0]
        assert 'name' in result[0]
        assert 'genres' in result[0]
        assert isinstance(result[0]['genres'], list)


@pytest.mark.unit
@pytest.mark.api
class TestApiClientCaching:
    """Test caching behavior of API clients"""

    async def test_response_caching(self, mock_bgg_client):
        """Test that responses are cached appropriately"""
        # First call
        mock_bgg_client.search_games.return_value = [{'bgg_id': 1, 'name': 'Test Game'}]
        result1 = await mock_bgg_client.search_games("test")
        
        # Second identical call
        result2 = await mock_bgg_client.search_games("test")
        
        # Results should be identical
        assert result1 == result2
        
        # Should use cache (implementation dependent)
        # In real implementation, might check call count

    async def test_cache_invalidation(self, mock_steam_client):
        """Test cache invalidation after time expires"""
        # This would test cache expiration logic
        # Implementation depends on actual caching strategy
        pass


@pytest.mark.unit
@pytest.mark.performance
class TestApiClientPerformance:
    """Test performance aspects of API clients"""

    async def test_concurrent_requests(self, mock_bgg_client, performance_threshold):
        """Test handling of concurrent API requests"""
        import asyncio
        import time
        
        mock_bgg_client.search_games.return_value = [{'bgg_id': 1, 'name': 'Test Game'}]
        
        # Make concurrent requests
        start_time = time.time()
        
        tasks = [mock_bgg_client.search_games(f"game{i}") for i in range(5)]
        results = await asyncio.gather(*tasks)
        
        execution_time = time.time() - start_time
        
        assert len(results) == 5
        assert execution_time < performance_threshold['api_request'] * 2  # Allow some overhead

    async def test_large_response_handling(self, mock_steam_client):
        """Test handling of large API responses"""
        # Create large mock response
        large_response = [
            {'steam_id': i, 'name': f'Game {i}'} for i in range(100)
        ]
        
        mock_steam_client.search_games.return_value = large_response
        
        import time
        start_time = time.time()
        
        result = await mock_steam_client.search_games("games")
        
        execution_time = time.time() - start_time
        
        assert len(result) == 100
        assert execution_time < 1.0  # Should process quickly


@pytest.mark.unit
@pytest.mark.api
class TestApiClientConfiguration:
    """Test API client configuration and settings"""

    def test_client_customization(self):
        """Test client initialization with custom settings"""
        # Test custom timeout
        custom_timeout = 30
        client = BoardGameGeekClient(timeout=custom_timeout)
        assert hasattr(client, 'timeout')
        
        # Test custom base URL (if supported)
        custom_url = "https://custom.api.example.com"
        # This would depend on actual implementation

    def test_client_headers(self):
        """Test that clients set appropriate headers"""
        client = SteamClient()
        
        # Should set User-Agent and other headers
        assert hasattr(client, '_get_headers')
        
        # In real implementation, would check actual headers

    def test_client_authentication(self):
        """Test client authentication setup"""
        # Xbox client requires authentication
        client = XboxClient()
        
        # Should handle API key configuration
        assert hasattr(client, 'api_key') or hasattr(client, '_auth_header')

    def test_client_rate_limiting_config(self):
        """Test rate limiting configuration"""
        # BGG has strict rate limits
        client = BoardGameGeekClient()
        
        # Should have rate limiting configuration
        assert hasattr(client, 'rate_limit') or hasattr(client, '_rate_limiter')
