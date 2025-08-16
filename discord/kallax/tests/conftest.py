"""
Comprehensive pytest fixtures and configuration for Kallax bot tests.
These fixtures provide reusable test components for testing Discord commands,
database operations, and API integrations.
"""

import pytest
import asyncio
import tempfile
import os
import json
from pathlib import Path
from unittest.mock import patch, AsyncMock, MagicMock
from typing import Dict, Any, List

# Import our mocks
from tests.mocks.discord_mocks import (
    MockKallaxBot, MockDiscordInteraction, MockDiscordUser, MockDiscordMember,
    MockDiscordGuild, MockDiscordEmbed, MockDiscordColor,
    create_mock_user, create_mock_member, create_mock_guild, 
    create_mock_interaction, create_mock_bot
)

from tests.mocks.api_mocks import (
    MockBGGApiClient, MockSteamApiClient, MockXboxApiClient,
    create_mock_bgg_client, create_mock_steam_client, create_mock_xbox_client
)


# Bot and Discord fixtures
@pytest.fixture
def mock_kallax_bot():
    """Create a mock Kallax bot instance"""
    return create_mock_bot()


@pytest.fixture
def mock_user():
    """Create a mock Discord user"""
    return create_mock_user(123456789, "TestUser")


@pytest.fixture
def mock_member():
    """Create a mock Discord member"""
    return create_mock_member(987654321, "TestMember")


@pytest.fixture
def mock_guild():
    """Create a mock Discord guild"""
    return create_mock_guild(555666777, "Test Guild")


@pytest.fixture
def mock_interaction(mock_user, mock_guild):
    """Create a mock Discord interaction"""
    return create_mock_interaction(mock_user, "gg-search", mock_guild)


@pytest.fixture
def mock_dm_interaction(mock_user):
    """Create a mock Discord DM interaction"""
    return create_mock_interaction(mock_user, "dm_command", None)


# Database fixtures
@pytest.fixture
def temp_db_path():
    """Create a temporary database path for testing"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_file:
        temp_path = temp_file.name
    yield temp_path
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
async def test_database(temp_db_path):
    """Create a test database with sample data"""
    from utils.database import Database
    
    db = Database(temp_db_path)
    await db.initialize()
    
    # Add sample user profiles
    await db.create_user_profile(
        123456789,
        bgg_username="testuser",
        steam_id="76561198000000001",
        xbox_gamertag="TestXboxUser"
    )
    
    await db.create_user_profile(
        987654321,
        bgg_username="testuser2"
    )
    
    # Add sample game cache data
    connection = await db.get_connection()
    await connection.execute("""
        INSERT INTO game_cache (
            bgg_id, name, year_published, min_players, max_players, 
            playing_time, rating, rating_count, weight
        ) VALUES 
            (174430, 'Gloomhaven', 2017, 1, 4, 120, 8.7, 75000, 3.9),
            (167791, 'Terraforming Mars', 2016, 1, 5, 120, 8.4, 60000, 3.3),
            (12333, 'Twilight Struggle', 2005, 2, 2, 180, 8.3, 55000, 3.6)
    """)
    await connection.commit()
    
    yield db
    await db.close()


@pytest.fixture
async def empty_database(temp_db_path):
    """Create an empty test database"""
    from utils.database import Database
    
    db = Database(temp_db_path)
    await db.initialize()
    yield db
    await db.close()


# API client fixtures
@pytest.fixture
def mock_bgg_client():
    """Create a mock BGG API client"""
    return create_mock_bgg_client()


@pytest.fixture
def mock_steam_client():
    """Create a mock Steam API client"""
    return create_mock_steam_client()


@pytest.fixture
def mock_xbox_client():
    """Create a mock Xbox API client"""
    return create_mock_xbox_client()


# Cog fixtures
@pytest.fixture
async def user_profiles_cog(mock_kallax_bot, test_database):
    """Create UserProfilesCog with test database"""
    from cogs.user_profiles import UserProfilesCog
    
    mock_kallax_bot.database = test_database
    cog = UserProfilesCog(mock_kallax_bot)
    await mock_kallax_bot.add_cog(cog)
    return cog


@pytest.fixture
async def game_search_cog(mock_kallax_bot):
    """Create GameSearchCog with mock APIs"""
    from cogs.game_search import GameSearchCog
    
    cog = GameSearchCog(mock_kallax_bot)
    await mock_kallax_bot.add_cog(cog)
    
    # Patch API clients to use mocks
    with patch('utils.bgg_api.BGGApiClient', return_value=create_mock_bgg_client()):
        with patch('utils.steam_api.SteamApiClient', return_value=create_mock_steam_client()):
            with patch('utils.xbox_api.XboxApiClient', return_value=create_mock_xbox_client()):
                yield cog


# Sample data fixtures
@pytest.fixture
def sample_bgg_game_data():
    """Sample BGG game data for testing"""
    return {
        'bgg_id': 174430,
        'name': 'Gloomhaven',
        'year_published': 2017,
        'image_url': 'https://cf.geekdo-images.com/image.jpg',
        'thumbnail_url': 'https://cf.geekdo-images.com/thumb.jpg',
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
    }


@pytest.fixture
def sample_steam_game_data():
    """Sample Steam game data for testing"""
    return {
        'app_id': 570,
        'name': 'Dota 2',
        'release_date': '2013',
        'price': 'Free',
        'description': 'Every day, millions of players worldwide enter battle...',
        'header_image': 'https://cdn.akamai.steamstatic.com/steam/apps/570/header.jpg',
        'screenshots': ['https://cdn.akamai.steamstatic.com/steam/apps/570/ss_1.jpg'],
        'genres': ['Action', 'Free to Play', 'Strategy'],
        'developers': ['Valve'],
        'publishers': ['Valve'],
        'metacritic_score': 90,
        'positive_reviews': 95,
        'negative_reviews': 5
    }


@pytest.fixture
def sample_xbox_game_data():
    """Sample Xbox game data for testing"""
    return {
        'product_id': '9NBLGGH4R6P9',
        'name': 'Halo Infinite',
        'release_date': '2021',
        'price': 'Free',
        'description': 'Master Chief returns in Halo Infinite...',
        'image_url': 'https://store-images.s-microsoft.com/image/halo_infinite.jpg',
        'genres': ['Shooter', 'Action'],
        'developer': '343 Industries',
        'publisher': 'Xbox Game Studios',
        'rating': 'M',
        'platforms': ['Xbox Series X|S', 'Xbox One', 'PC']
    }


@pytest.fixture
def sample_user_profile():
    """Sample user profile data for testing"""
    return {
        'discord_id': 123456789,
        'bgg_username': 'testuser',
        'steam_id': '76561198000000001',
        'xbox_gamertag': 'TestXboxUser',
        'weekly_stats_enabled': True,
        'weekly_stats_channel_id': None
    }


@pytest.fixture
def sample_bgg_collection():
    """Sample BGG collection data for testing"""
    return [
        {
            'bgg_id': 174430,
            'name': 'Gloomhaven',
            'year_published': 2017,
            'owned': True,
            'want_to_play': True,
            'rating': 9,
            'num_plays': 15
        },
        {
            'bgg_id': 167791,
            'name': 'Terraforming Mars',
            'year_published': 2016,
            'owned': True,
            'want_to_play': False,
            'rating': 8,
            'num_plays': 8
        }
    ]


# Environment and configuration fixtures
@pytest.fixture
def mock_env_vars():
    """Mock environment variables for testing"""
    test_env = {
        'DATABASE_PATH': './data/test_kallax.db',
        'HEALTH_CHECK_PORT': '8080',
        'ENVIRONMENT': 'test',
        'COMMAND_PREFIX': '!test',
        'BGG_API_BASE_URL': 'https://api.geekdo.com',
        'STEAM_API_KEY': 'test_steam_key',
        'XBOX_API_KEY': 'test_xbox_key'
    }
    
    with patch.dict(os.environ, test_env):
        yield test_env


@pytest.fixture
def mock_aiohttp_session():
    """Mock aiohttp session for API tests"""
    session_mock = AsyncMock()
    
    # Configure common response scenarios
    response_mock = AsyncMock()
    response_mock.json = AsyncMock(return_value={'test': 'data'})
    response_mock.text = AsyncMock(return_value='test response')
    response_mock.status = 200
    response_mock.raise_for_status = MagicMock()
    
    session_mock.get = AsyncMock(return_value=response_mock)
    session_mock.post = AsyncMock(return_value=response_mock)
    session_mock.close = AsyncMock()
    
    return session_mock


# Context manager fixtures
@pytest.fixture
def mock_async_context():
    """Mock async context manager"""
    class MockContext:
        def __init__(self, return_value=None):
            self.return_value = return_value
            
        async def __aenter__(self):
            return self.return_value
            
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            return False
    
    return MockContext


# Error testing fixtures
@pytest.fixture
def api_error_scenarios():
    """Common API error scenarios for testing"""
    return {
        'network_timeout': Exception("Request timeout"),
        'rate_limit': Exception("Rate limit exceeded"),
        'invalid_response': Exception("Invalid JSON response"),
        'server_error': Exception("HTTP 500: Internal Server Error"),
        'not_found': Exception("HTTP 404: Not Found"),
        'unauthorized': Exception("HTTP 401: Unauthorized")
    }


# Performance testing fixtures
@pytest.fixture
def performance_thresholds():
    """Performance thresholds for testing"""
    return {
        'database_query_max_time': 1.0,  # seconds
        'api_request_max_time': 5.0,     # seconds
        'command_response_max_time': 3.0, # seconds
        'embed_generation_max_time': 0.5  # seconds
    }


# Integration testing fixtures
@pytest.fixture
async def integrated_bot_environment(mock_kallax_bot, test_database, mock_env_vars):
    """Create a fully integrated bot environment for testing"""
    # Setup bot with database
    mock_kallax_bot.database = test_database
    
    # Load all cogs
    from cogs.user_profiles import UserProfilesCog
    from cogs.game_search import GameSearchCog
    
    user_profiles_cog = UserProfilesCog(mock_kallax_bot)
    game_search_cog = GameSearchCog(mock_kallax_bot)
    
    await mock_kallax_bot.add_cog(user_profiles_cog)
    await mock_kallax_bot.add_cog(game_search_cog)
    
    # Mock API clients
    with patch('utils.bgg_api.BGGApiClient', return_value=create_mock_bgg_client()):
        with patch('utils.steam_api.SteamApiClient', return_value=create_mock_steam_client()):
            with patch('utils.xbox_api.XboxApiClient', return_value=create_mock_xbox_client()):
                yield {
                    'bot': mock_kallax_bot,
                    'database': test_database,
                    'user_profiles_cog': user_profiles_cog,
                    'game_search_cog': game_search_cog
                }


# Async test configuration
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Test configuration helpers
def pytest_configure(config):
    """Configure pytest for async testing"""
    pytest.asyncio_mode = "auto"


def pytest_collection_modifyitems(config, items):
    """Add markers to tests based on their names and content"""
    for item in items:
        # Add database marker to database tests
        if "database" in item.nodeid or "db" in item.name:
            item.add_marker(pytest.mark.database)
            
        # Add integration marker to integration tests
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
            
        # Add unit marker to unit tests
        if "unit" in item.nodeid or "test_" in item.name:
            item.add_marker(pytest.mark.unit)
            
        # Add API markers based on test content
        if "bgg" in item.name.lower() or "boardgamegeek" in item.name.lower():
            item.add_marker(pytest.mark.bgg)
        if "steam" in item.name.lower():
            item.add_marker(pytest.mark.steam)
        if "xbox" in item.name.lower():
            item.add_marker(pytest.mark.xbox)
            
        # Add slow marker to potentially slow tests
        if any(keyword in item.name.lower() for keyword in ['search', 'collection', 'profile', 'api']):
            item.add_marker(pytest.mark.slow)


# Export fixtures for easier importing
__all__ = [
    'mock_kallax_bot',
    'mock_user',
    'mock_member', 
    'mock_guild',
    'mock_interaction',
    'mock_dm_interaction',
    'temp_db_path',
    'test_database',
    'empty_database',
    'mock_bgg_client',
    'mock_steam_client',
    'mock_xbox_client',
    'user_profiles_cog',
    'game_search_cog',
    'sample_bgg_game_data',
    'sample_steam_game_data',
    'sample_xbox_game_data',
    'sample_user_profile',
    'sample_bgg_collection',
    'mock_env_vars',
    'mock_aiohttp_session',
    'mock_async_context',
    'api_error_scenarios',
    'performance_thresholds',
    'integrated_bot_environment'
]
