"""
Pytest fixtures and configuration for Jarvfjallet bot tests.
These fixtures provide reusable test components.
"""

import pytest
import asyncio
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, AsyncMock

# Import our mocks
from tests.mocks.discord_mocks import (
    MockBot, MockDiscordInteraction, MockDiscordUser, MockDiscordMember,
    MockDiscordEmbed, MockDiscordColor, create_mock_interaction, create_mock_bot
)

# Import actual bot components
from utils.database import Database
from cogs.game_assignment import GameAssignment


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
    """Create a test database with some sample data"""
    db = Database(temp_db_path)
    await db.initialize()
    
    # Add some test data
    await db._connection.execute("""
        INSERT INTO games (id, game_name, game_url, dev_name, short_text, windows, mac, linux)
        VALUES 
            (1, 'Test Game 1', 'https://example.com/game1', 'Dev Studio', 'A fun test game', 1, 0, 1),
            (2, 'Test Game 2', 'https://example.com/game2', 'Indie Dev', 'Another test game', 1, 1, 0),
            (3, 'Assigned Game', 'https://example.com/game3', 'Studio X', 'Already assigned', 1, 1, 1)
    """)
    
    # Assign one game to a test user
    await db._connection.execute("""
        UPDATE games SET reviewer = ?, assign_date = ? WHERE id = 3
    """, ('123456789', 1692000000000))
    
    await db._connection.commit()
    
    yield db
    await db.close()


@pytest.fixture
def mock_discord_user():
    """Create a mock Discord user"""
    return MockDiscordUser(123456789, "TestUser")


@pytest.fixture
def mock_discord_member():
    """Create a mock Discord member"""
    return MockDiscordMember(123456789, "TestMember")


@pytest.fixture
def mock_interaction(mock_discord_user):
    """Create a mock Discord interaction"""
    return MockDiscordInteraction(mock_discord_user)


@pytest.fixture
async def mock_bot(test_database):
    """Create a mock bot with test database"""
    bot = MockBot()
    bot.database = test_database
    return bot


@pytest.fixture
async def game_assignment_cog(mock_bot):
    """Create GameAssignment cog with mock bot"""
    cog = GameAssignment(mock_bot)
    await mock_bot.add_cog(cog)
    return cog


@pytest.fixture
def mock_discord():
    """Mock the entire discord module"""
    with patch.dict('sys.modules', {
        'discord': AsyncMock(),
        'discord.ext': AsyncMock(),
        'discord.ext.commands': AsyncMock(),
        'discord.app_commands': AsyncMock(),
    }):
        # Create mock discord module
        import sys
        discord_mock = AsyncMock()
        discord_mock.Interaction = MockDiscordInteraction
        discord_mock.Member = MockDiscordMember
        discord_mock.User = MockDiscordUser
        discord_mock.Embed = MockDiscordEmbed
        discord_mock.Color = MockDiscordColor
        
        sys.modules['discord'] = discord_mock
        yield discord_mock


@pytest.fixture
def sample_game_data():
    """Sample game data for testing"""
    return {
        'id': 999,
        'game_name': 'Sample Game',
        'game_url': 'https://example.com/sample-game',
        'dev_name': 'Sample Developer',
        'short_text': 'A sample game for testing',
        'thumb_url': 'https://example.com/thumb.jpg',
        'windows': True,
        'mac': False,
        'linux': True,
        'game_host': 'itch.io'
    }


@pytest.fixture
def empty_database(temp_db_path):
    """Create an empty test database"""
    async def _create_empty_db():
        db = Database(temp_db_path)
        await db.initialize()
        return db
    return _create_empty_db


# Async test helper
def pytest_configure(config):
    """Configure pytest for async testing"""
    pytest.asyncio_mode = "auto"


# Pytest collection configuration
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


class AsyncMockContext:
    """Helper class for async context manager mocking"""
    def __init__(self, return_value=None, side_effect=None):
        self.return_value = return_value
        self.side_effect = side_effect
        
    async def __aenter__(self):
        if self.side_effect:
            if asyncio.iscoroutinefunction(self.side_effect):
                return await self.side_effect()
            else:
                return self.side_effect()
        return self.return_value
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return False
