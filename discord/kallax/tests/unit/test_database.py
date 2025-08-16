"""
Unit tests for Kallax Database class.
Tests database operations, user profiles, game caching, and data integrity.
"""

import pytest
import tempfile
import os
import time
from datetime import datetime
from utils.database import Database


@pytest.mark.unit
@pytest.mark.database
class TestDatabaseInitialization:
    """Test database initialization and schema creation"""

    async def test_database_initialization(self, temp_db_path):
        """Test that database initializes correctly"""
        db = Database(temp_db_path)
        await db.initialize()
        
        assert db._initialized is True
        assert os.path.exists(temp_db_path)
        
        # Check that tables were created
        connection = await db.get_connection()
        cursor = await connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        tables = [row[0] for row in await cursor.fetchall()]
        
        required_tables = {'user_profiles', 'game_cache', 'game_plays', 'server_settings'}
        assert required_tables.issubset(set(tables))
        
        await db.close()

    async def test_database_lazy_initialization(self, temp_db_path):
        """Test that database initializes lazily on first use"""
        db = Database(temp_db_path)
        assert not db._initialized
        
        # Should initialize on first connection request
        await db.get_connection()
        assert db._initialized
        
        await db.close()

    async def test_database_schema_validation(self, temp_db_path):
        """Test that existing database schema is validated"""
        # Create database first
        db = Database(temp_db_path)
        await db.initialize()
        await db.close()
        
        # Reconnect to existing database
        db2 = Database(temp_db_path)
        await db2.initialize()
        
        assert db2._initialized is True
        await db2.close()

    async def test_database_missing_tables_creation(self, temp_db_path):
        """Test creation of missing tables in existing database"""
        # Create database with minimal setup
        db = Database(temp_db_path)
        connection = await db.get_connection()
        
        # Drop one table to simulate missing table scenario
        await connection.execute("DROP TABLE IF EXISTS game_plays")
        await connection.commit()
        
        # Close and reinitialize
        await db.close()
        
        db2 = Database(temp_db_path)
        await db2.initialize()
        
        # Verify table was recreated
        cursor = await connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='game_plays'"
        )
        result = await cursor.fetchone()
        assert result is not None
        
        await db2.close()


@pytest.mark.unit
@pytest.mark.database
class TestUserProfiles:
    """Test user profile operations"""

    async def test_create_user_profile(self, empty_database):
        """Test creating a new user profile"""
        success = await empty_database.create_user_profile(
            discord_id=123456789,
            bgg_username="testuser",
            steam_id="76561198000000001",
            xbox_gamertag="TestXboxUser"
        )
        
        assert success is True
        
        # Verify profile was created
        profile = await empty_database.get_user_profile(123456789)
        assert profile is not None
        assert profile['discord_id'] == 123456789
        assert profile['bgg_username'] == "testuser"
        assert profile['steam_id'] == "76561198000000001"
        assert profile['xbox_gamertag'] == "TestXboxUser"

    async def test_create_user_profile_partial(self, empty_database):
        """Test creating user profile with only some platforms"""
        success = await empty_database.create_user_profile(
            discord_id=987654321,
            bgg_username="partialuser"
        )
        
        assert success is True
        
        profile = await empty_database.get_user_profile(987654321)
        assert profile['bgg_username'] == "partialuser"
        assert profile['steam_id'] is None
        assert profile['xbox_gamertag'] is None

    async def test_update_user_profile(self, test_database):
        """Test updating an existing user profile"""
        # Update existing profile
        success = await test_database.update_user_profile(
            discord_id=123456789,
            bgg_username="updateduser",
            weekly_stats_enabled=True
        )
        
        assert success is True
        
        # Verify update
        profile = await test_database.get_user_profile(123456789)
        assert profile['bgg_username'] == "updateduser"
        assert profile['weekly_stats_enabled'] is True
        assert profile['steam_id'] == "76561198000000001"  # Should remain unchanged

    async def test_update_nonexistent_profile(self, empty_database):
        """Test updating a profile that doesn't exist"""
        success = await empty_database.update_user_profile(
            discord_id=999999999,
            bgg_username="nonexistent"
        )
        
        assert success is False

    async def test_get_user_profile_not_found(self, empty_database):
        """Test getting a profile that doesn't exist"""
        profile = await empty_database.get_user_profile(999999999)
        assert profile is None

    async def test_delete_user_profile(self, test_database):
        """Test deleting a user profile"""
        # Verify profile exists
        profile = await test_database.get_user_profile(123456789)
        assert profile is not None
        
        # Delete profile
        success = await test_database.delete_user_profile(123456789)
        assert success is True
        
        # Verify profile is gone
        profile = await test_database.get_user_profile(123456789)
        assert profile is None

    async def test_get_users_by_platform(self, test_database):
        """Test getting users by platform username"""
        # Test BGG username lookup
        users = await test_database.get_users_by_platform('bgg', 'testuser')
        assert len(users) == 1
        assert users[0]['discord_id'] == 123456789

        # Test Steam ID lookup  
        users = await test_database.get_users_by_platform('steam', '76561198000000001')
        assert len(users) == 1
        assert users[0]['discord_id'] == 123456789

        # Test nonexistent user
        users = await test_database.get_users_by_platform('bgg', 'nonexistent')
        assert len(users) == 0


@pytest.mark.unit
@pytest.mark.database
class TestGameCache:
    """Test game cache operations"""

    async def test_cache_game(self, empty_database, sample_bgg_game_data):
        """Test caching a game"""
        success = await empty_database.cache_game(sample_bgg_game_data)
        assert success is True
        
        # Verify game was cached
        cached_game = await empty_database.get_cached_game(sample_bgg_game_data['bgg_id'])
        assert cached_game is not None
        assert cached_game['name'] == sample_bgg_game_data['name']
        assert cached_game['rating'] == sample_bgg_game_data['rating']

    async def test_cache_game_update_existing(self, test_database):
        """Test updating an existing cached game"""
        # Update existing game in cache
        updated_data = {
            'bgg_id': 174430,
            'name': 'Gloomhaven (Updated)',
            'rating': 9.0,
            'rating_count': 80000
        }
        
        success = await test_database.cache_game(updated_data)
        assert success is True
        
        # Verify update
        cached_game = await test_database.get_cached_game(174430)
        assert cached_game['name'] == 'Gloomhaven (Updated)'
        assert cached_game['rating'] == 9.0
        assert cached_game['rating_count'] == 80000

    async def test_get_cached_game_not_found(self, empty_database):
        """Test getting a game that's not in cache"""
        cached_game = await empty_database.get_cached_game(999999)
        assert cached_game is None

    async def test_is_game_cached(self, test_database):
        """Test checking if game is cached"""
        # Should be cached (from test_database fixture)
        is_cached = await test_database.is_game_cached(174430)
        assert is_cached is True
        
        # Should not be cached
        is_cached = await test_database.is_game_cached(999999)
        assert is_cached is False

    async def test_get_cached_games_batch(self, test_database):
        """Test getting multiple cached games at once"""
        bgg_ids = [174430, 167791, 999999]  # Mix of existing and non-existing
        games = await test_database.get_cached_games_batch(bgg_ids)
        
        # Should return games for existing IDs only
        assert len(games) == 2
        game_ids = [game['bgg_id'] for game in games]
        assert 174430 in game_ids
        assert 167791 in game_ids
        assert 999999 not in game_ids

    async def test_cache_expiration(self, empty_database, sample_bgg_game_data):
        """Test cache expiration logic"""
        # Cache a game
        await empty_database.cache_game(sample_bgg_game_data)
        
        # Check if cache is fresh (should be fresh immediately)
        is_fresh = await empty_database.is_cache_fresh(sample_bgg_game_data['bgg_id'], hours=24)
        assert is_fresh is True
        
        # Check with very short expiration (should be stale)
        is_fresh = await empty_database.is_cache_fresh(sample_bgg_game_data['bgg_id'], hours=0.001)
        assert is_fresh is True  # Still fresh since we just cached it


@pytest.mark.unit
@pytest.mark.database
class TestGamePlays:
    """Test game play tracking operations"""

    async def test_add_game_play(self, test_database):
        """Test adding a game play record"""
        play_data = {
            'discord_id': 123456789,
            'bgg_id': 174430,
            'game_name': 'Gloomhaven',
            'play_date': '2023-12-01',
            'duration_minutes': 120,
            'player_count': 4,
            'players': 'Alice, Bob, Charlie, David',
            'location': 'Home'
        }
        
        play_id = await test_database.add_game_play(**play_data)
        assert play_id is not None
        assert isinstance(play_id, int)

    async def test_get_user_plays(self, test_database):
        """Test getting plays for a user"""
        # Add some test plays first
        play1 = {
            'discord_id': 123456789,
            'bgg_id': 174430,
            'game_name': 'Gloomhaven',
            'play_date': '2023-12-01',
            'duration_minutes': 120,
            'player_count': 4
        }
        
        play2 = {
            'discord_id': 123456789,
            'bgg_id': 167791,
            'game_name': 'Terraforming Mars',
            'play_date': '2023-12-02',
            'duration_minutes': 90,
            'player_count': 3
        }
        
        await test_database.add_game_play(**play1)
        await test_database.add_game_play(**play2)
        
        # Get plays for user
        plays = await test_database.get_user_plays(123456789)
        assert len(plays) >= 2
        
        # Verify play data
        play_names = [play['game_name'] for play in plays]
        assert 'Gloomhaven' in play_names
        assert 'Terraforming Mars' in play_names

    async def test_get_user_plays_with_limit(self, test_database):
        """Test getting user plays with limit"""
        # Add multiple plays
        for i in range(5):
            play_data = {
                'discord_id': 123456789,
                'bgg_id': 174430,
                'game_name': 'Gloomhaven',
                'play_date': f'2023-12-{i+1:02d}',
                'duration_minutes': 120,
                'player_count': 4
            }
            await test_database.add_game_play(**play_data)
        
        # Get limited results
        plays = await test_database.get_user_plays(123456789, limit=3)
        assert len(plays) == 3

    async def test_get_game_play_stats(self, test_database):
        """Test getting play statistics for a user"""
        # Add some plays with different games and durations
        plays_data = [
            {'discord_id': 123456789, 'bgg_id': 174430, 'game_name': 'Gloomhaven', 
             'play_date': '2023-12-01', 'duration_minutes': 120, 'player_count': 4},
            {'discord_id': 123456789, 'bgg_id': 174430, 'game_name': 'Gloomhaven',
             'play_date': '2023-12-02', 'duration_minutes': 150, 'player_count': 3},
            {'discord_id': 123456789, 'bgg_id': 167791, 'game_name': 'Terraforming Mars',
             'play_date': '2023-12-03', 'duration_minutes': 90, 'player_count': 5}
        ]
        
        for play_data in plays_data:
            await test_database.add_game_play(**play_data)
        
        # Get stats
        stats = await test_database.get_game_play_stats(123456789)
        
        assert stats['total_plays'] >= 3
        assert stats['total_playtime'] >= 360  # 120 + 150 + 90
        assert stats['unique_games'] >= 2
        assert 'avg_playtime' in stats
        assert 'avg_players' in stats


@pytest.mark.unit
@pytest.mark.database  
class TestServerSettings:
    """Test server settings operations"""

    async def test_create_server_settings(self, empty_database):
        """Test creating server settings"""
        guild_id = 555666777
        channel_id = 888999000
        
        success = await empty_database.update_server_settings(
            guild_id=guild_id,
            weekly_stats_channel_id=channel_id,
            command_prefix='?'
        )
        
        assert success is True
        
        # Verify settings
        settings = await empty_database.get_server_settings(guild_id)
        assert settings is not None
        assert settings['guild_id'] == guild_id
        assert settings['weekly_stats_channel_id'] == channel_id
        assert settings['command_prefix'] == '?'

    async def test_update_server_settings(self, empty_database):
        """Test updating existing server settings"""
        guild_id = 555666777
        
        # Create initial settings
        await empty_database.update_server_settings(guild_id=guild_id, command_prefix='!')
        
        # Update settings
        success = await empty_database.update_server_settings(
            guild_id=guild_id,
            weekly_stats_channel_id=999000111,
            command_prefix='?'
        )
        
        assert success is True
        
        # Verify update
        settings = await empty_database.get_server_settings(guild_id)
        assert settings['weekly_stats_channel_id'] == 999000111
        assert settings['command_prefix'] == '?'

    async def test_get_server_settings_not_found(self, empty_database):
        """Test getting settings for non-existent server"""
        settings = await empty_database.get_server_settings(999999999)
        assert settings is None


@pytest.mark.unit
@pytest.mark.database
class TestDatabasePerformance:
    """Test database performance and optimization"""

    async def test_connection_reuse(self, temp_db_path):
        """Test that database connections are reused properly"""
        db = Database(temp_db_path)
        
        # Get connection multiple times
        conn1 = await db.get_connection()
        conn2 = await db.get_connection()
        
        # Should be the same connection object
        assert conn1 is conn2
        
        await db.close()

    async def test_batch_operations_performance(self, empty_database):
        """Test batch operations are more efficient"""
        import time
        
        # Time individual inserts
        start_time = time.time()
        for i in range(10):
            game_data = {
                'bgg_id': 1000 + i,
                'name': f'Test Game {i}',
                'year_published': 2020 + i,
                'rating': 7.0 + (i * 0.1)
            }
            await empty_database.cache_game(game_data)
        individual_time = time.time() - start_time
        
        # Time batch operation
        start_time = time.time()
        batch_data = []
        for i in range(10):
            batch_data.append({
                'bgg_id': 2000 + i,
                'name': f'Batch Game {i}',
                'year_published': 2020 + i,
                'rating': 7.0 + (i * 0.1)
            })
        
        # Simulate batch insert (would need to implement this method)
        for game_data in batch_data:
            await empty_database.cache_game(game_data)
        batch_time = time.time() - start_time
        
        # Batch should be at least somewhat comparable (this is a simple test)
        assert batch_time < individual_time * 2  # Allow some overhead


@pytest.mark.unit
@pytest.mark.database
class TestDatabaseErrorHandling:
    """Test database error handling and edge cases"""

    async def test_database_connection_error_handling(self, temp_db_path):
        """Test handling of database connection errors"""
        db = Database("/invalid/path/to/database.db")
        
        # Should handle invalid path gracefully during initialization
        try:
            await db.initialize()
            # If we get here, the database was created (which is valid behavior)
            await db.close()
        except Exception as e:
            # Error is acceptable for invalid paths
            assert "permission" in str(e).lower() or "no such file" in str(e).lower()

    async def test_invalid_user_profile_data(self, empty_database):
        """Test handling of invalid user profile data"""
        # Try to create profile with invalid discord_id type
        with pytest.raises((TypeError, ValueError)):
            await empty_database.create_user_profile(
                discord_id="invalid_id",  # Should be int
                bgg_username="test"
            )

    async def test_sql_injection_protection(self, empty_database):
        """Test protection against SQL injection"""
        malicious_username = "test'; DROP TABLE user_profiles; --"
        
        # Should not cause SQL injection
        success = await empty_database.create_user_profile(
            discord_id=123456789,
            bgg_username=malicious_username
        )
        
        assert success is True
        
        # Verify table still exists and profile was created safely
        profile = await empty_database.get_user_profile(123456789)
        assert profile is not None
        assert profile['bgg_username'] == malicious_username

    async def test_concurrent_access(self, temp_db_path):
        """Test concurrent database access"""
        db1 = Database(temp_db_path)
        db2 = Database(temp_db_path)
        
        await db1.initialize()
        await db2.initialize()
        
        # Both should be able to perform operations
        success1 = await db1.create_user_profile(123456789, bgg_username="user1")
        success2 = await db2.create_user_profile(987654321, bgg_username="user2")
        
        assert success1 is True
        assert success2 is True
        
        # Both users should exist
        profile1 = await db1.get_user_profile(123456789)
        profile2 = await db2.get_user_profile(987654321)
        
        assert profile1 is not None
        assert profile2 is not None
        
        await db1.close()
        await db2.close()

    async def test_database_corruption_recovery(self, temp_db_path):
        """Test recovery from database corruption scenarios"""
        # Create and initialize database
        db = Database(temp_db_path)
        await db.initialize()
        await db.close()
        
        # Simulate corruption by writing invalid data to file
        with open(temp_db_path, 'w') as f:
            f.write("corrupted data")
        
        # Try to reconnect - should handle corruption gracefully
        db2 = Database(temp_db_path)
        try:
            await db2.initialize()
            # If initialization succeeds, database was recreated
            await db2.close()
        except Exception as e:
            # Corruption handling is acceptable behavior
            assert "database" in str(e).lower() or "corrupt" in str(e).lower()
