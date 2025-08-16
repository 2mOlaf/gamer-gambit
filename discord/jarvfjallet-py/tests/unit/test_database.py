"""
Unit tests for the Database class.
These tests verify database operations work correctly.
"""

import pytest
import tempfile
import os
from utils.database import Database


@pytest.mark.unit
@pytest.mark.database
class TestDatabaseOperations:
    """Test database CRUD operations"""

    async def test_database_initialization(self, temp_db_path):
        """Test that database initializes correctly"""
        db = Database(temp_db_path)
        await db.initialize()
        
        assert db._initialized is True
        assert os.path.exists(temp_db_path)
        
        # Check that tables were created
        cursor = await db._connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        tables = [row[0] for row in await cursor.fetchall()]
        
        assert 'games' in tables
        assert 'user_assignments' in tables
        
        await db.close()

    async def test_has_games_empty_database(self, empty_database):
        """Test has_games returns False for empty database"""
        db = await empty_database()
        result = await db.has_games()
        assert result is False
        await db.close()

    async def test_has_games_with_data(self, test_database):
        """Test has_games returns True when database has games"""
        result = await test_database.has_games()
        assert result is True

    async def test_get_random_unassigned_game(self, test_database):
        """Test getting random unassigned games"""
        # Should get one of the unassigned games (1 or 2)
        game = await test_database.get_random_unassigned_game()
        
        assert game is not None
        assert game['id'] in [1, 2]  # Games 1 and 2 are unassigned
        assert game['reviewer'] is None or game['reviewer'] == ''

    async def test_get_random_unassigned_game_empty(self, empty_database):
        """Test getting random game from empty database"""
        db = await empty_database()
        game = await db.get_random_unassigned_game()
        assert game is None
        await db.close()

    async def test_assign_game_to_user(self, test_database):
        """Test assigning a game to a user"""
        # Assign game 1 to test user
        success = await test_database.assign_game_to_user(1, '555444333', 'NewUser')
        assert success is True
        
        # Verify assignment
        cursor = await test_database._connection.execute(
            "SELECT reviewer FROM games WHERE id = ?", (1,)
        )
        row = await cursor.fetchone()
        assert row[0] == '555444333'
        
        # Check user_assignments table
        cursor = await test_database._connection.execute(
            "SELECT user_id, game_id FROM user_assignments WHERE game_id = ?", (1,)
        )
        row = await cursor.fetchone()
        assert row[0] == '555444333'
        assert row[1] == 1

    async def test_get_user_games_legacy(self, test_database):
        """Test getting user's assigned games"""
        # Test user 123456789 should have game 3 assigned
        games = await test_database.get_user_games_legacy('123456789', 'TestUser')
        
        assert len(games) == 1
        assert games[0]['id'] == 3
        assert games[0]['game_name'] == 'Assigned Game'

    async def test_get_user_games_legacy_no_games(self, test_database):
        """Test getting games for user with no assignments"""
        games = await test_database.get_user_games_legacy('999888777', 'NoGamesUser')
        assert len(games) == 0

    async def test_get_game_stats(self, test_database):
        """Test getting database statistics"""
        stats = await test_database.get_game_stats()
        
        assert stats['total_games'] == 3
        assert stats['assigned_games'] == 1  # Game 3 is assigned
        assert stats['unassigned_games'] == 2  # Games 1 and 2
        assert stats['completed_reviews'] == 0  # No reviews completed

    async def test_get_game_stats_empty(self, empty_database):
        """Test stats for empty database"""
        db = await empty_database()
        stats = await db.get_game_stats()
        
        assert stats['total_games'] == 0
        assert stats['assigned_games'] == 0
        assert stats['unassigned_games'] == 0
        assert stats['completed_reviews'] == 0
        
        await db.close()

    async def test_get_game_by_id(self, test_database):
        """Test getting specific game by ID"""
        game = await test_database.get_game_by_id(1)
        
        assert game is not None
        assert game['id'] == 1
        assert game['game_name'] == 'Test Game 1'
        assert game['dev_name'] == 'Dev Studio'

    async def test_get_game_by_id_not_found(self, test_database):
        """Test getting non-existent game"""
        game = await test_database.get_game_by_id(999)
        assert game is None

    async def test_update_review_completion(self, test_database):
        """Test marking a game review as completed"""
        # Complete review for game 3
        success = await test_database.update_review_completion(3, 'https://example.com/review')
        assert success is True
        
        # Check that review_url and review_date were set
        cursor = await test_database._connection.execute(
            "SELECT review_url, review_date FROM games WHERE id = ?", (3,)
        )
        row = await cursor.fetchone()
        assert row[0] == 'https://example.com/review'
        assert row[1] is not None  # review_date should be set
        
        # Check stats now show 1 completed review
        stats = await test_database.get_game_stats()
        assert stats['completed_reviews'] == 1


@pytest.mark.unit
@pytest.mark.database
class TestDatabaseRowFactory:
    """Test that row factory conversion works correctly"""
    
    async def test_row_factory_dict_conversion(self, test_database):
        """Test that rows are properly converted to dictionaries"""
        game = await test_database.get_game_by_id(1)
        
        # Should be a dictionary
        assert isinstance(game, dict)
        
        # Should have expected keys
        assert 'id' in game
        assert 'game_name' in game
        assert 'dev_name' in game
        
        # Values should be accessible via dictionary access
        assert game['id'] == 1
        assert game['game_name'] == 'Test Game 1'

    async def test_user_games_legacy_dict_conversion(self, test_database):
        """Test that user games are returned as dictionaries"""
        games = await test_database.get_user_games_legacy('123456789', 'TestUser')
        
        assert len(games) > 0
        game = games[0]
        
        # Should be a dictionary
        assert isinstance(game, dict)
        
        # Should be accessible via .get() method
        assert game.get('id') == 3
        assert game.get('game_name') == 'Assigned Game'
        assert game.get('nonexistent_key') is None
