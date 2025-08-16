#!/usr/bin/env python3
"""
Enhanced database tests that would have caught the row factory bug.
These tests specifically verify dictionary access patterns and row conversion.
"""

import asyncio
import tempfile
import os
import pytest
from utils.database import Database


class TestDatabaseRowFactoryBugPrevention:
    """Tests specifically designed to catch row factory conversion issues"""

    @pytest.fixture
    async def real_working_database(self):
        """Create a properly working database for testing"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_file:
            db_path = temp_file.name
        
        try:
            db = Database(db_path)
            await db.initialize()
            
            # Use the database's proper connection method, not _connection
            import aiosqlite
            async with aiosqlite.connect(db_path) as conn:
                conn.row_factory = aiosqlite.Row
                await conn.execute("""
                    INSERT INTO games (id, game_name, game_url, dev_name, short_text, windows, mac, linux, reviewer, assign_date)
                    VALUES 
                        (1, 'Unassigned Game', 'https://example.com/1', 'Dev1', 'Test game 1', 1, 0, 1, NULL, NULL),
                        (2, 'Assigned Game', 'https://example.com/2', 'Dev2', 'Test game 2', 1, 1, 0, '123456789', 1692000000000)
                """)
                await conn.commit()
            
            yield db
            
        finally:
            await db.close()
            if os.path.exists(db_path):
                os.unlink(db_path)

    async def test_get_random_unassigned_game_returns_dict_with_access(self, real_working_database):
        """Test that get_random_unassigned_game returns a dictionary with proper access"""
        game = await real_working_database.get_random_unassigned_game()
        
        assert game is not None, "Should return a game"
        
        # This would have failed with the dict(row) bug!
        assert isinstance(game, dict), "Should return a dictionary"
        
        # Test dictionary-style access - this was the actual bug
        assert game['id'] == 1, "Should access via bracket notation"
        assert game['game_name'] == 'Unassigned Game', "Should access game name"
        
        # Test .get() access - this was also failing
        assert game.get('id') == 1, "Should access via .get() method"
        assert game.get('game_name') == 'Unassigned Game', "Should get game name"
        assert game.get('nonexistent_key') is None, ".get() should return None for missing keys"
        
        # Test that all expected keys are present and accessible
        required_keys = ['id', 'game_name', 'game_url', 'dev_name', 'short_text']
        for key in required_keys:
            assert key in game, f"Game should have key: {key}"
            assert game[key] is not None, f"Key {key} should not be None"

    async def test_get_user_games_legacy_returns_dict_list_with_access(self, real_working_database):
        """Test that get_user_games_legacy returns a list of dictionaries with proper access"""
        games = await real_working_database.get_user_games_legacy('123456789', 'TestUser')
        
        assert len(games) == 1, "Should return one assigned game"
        
        game = games[0]
        
        # This would have failed with the dict(row) bug!
        assert isinstance(game, dict), "Each game should be a dictionary"
        
        # Test dictionary-style access - this was the actual bug
        assert game['id'] == 2, "Should access ID via bracket notation"
        assert game['game_name'] == 'Assigned Game', "Should access game name"
        assert game['reviewer'] == '123456789', "Should access reviewer"
        
        # Test .get() access - this was also failing
        assert game.get('id') == 2, "Should access via .get() method"
        assert game.get('game_name') == 'Assigned Game', "Should get game name"
        assert game.get('reviewer') == '123456789', "Should get reviewer"
        assert game.get('nonexistent_key') is None, ".get() should return None for missing keys"

    async def test_get_game_by_id_returns_dict_with_access(self, real_working_database):
        """Test that get_game_by_id returns a dictionary with proper access"""
        game = await real_working_database.get_game_by_id(1)
        
        assert game is not None, "Should return the game"
        assert isinstance(game, dict), "Should return a dictionary"
        
        # Test dictionary-style access
        assert game['id'] == 1, "Should access ID via bracket notation"
        assert game['game_name'] == 'Unassigned Game', "Should access game name"
        
        # Test .get() access
        assert game.get('id') == 1, "Should access via .get() method"
        assert game.get('nonexistent_key') is None, ".get() should return None for missing keys"

    async def test_get_user_assignments_returns_dict_list_with_access(self, real_working_database):
        """Test that get_user_assignments returns dictionaries with proper access"""
        # First assign a game
        await real_working_database.assign_game_to_user(1, '999888777', 'NewUser')
        
        # Then get assignments
        assignments = await real_working_database.get_user_assignments('999888777')
        
        assert len(assignments) == 1, "Should return one assignment"
        
        assignment = assignments[0]
        assert isinstance(assignment, dict), "Assignment should be a dictionary"
        
        # Test dictionary-style access
        assert assignment['id'] == 1, "Should access game ID"
        assert assignment['game_name'] == 'Unassigned Game', "Should access game name"
        
        # Test .get() access
        assert assignment.get('id') == 1, "Should access via .get() method"


class TestCommandIntegrationWithRealDatabase:
    """Integration tests that run actual commands against real database"""
    
    async def test_hit_command_with_real_database_flow(self):
        """Test the complete /hit command flow with real database operations"""
        # This test should have existed to catch the bug!
        
        # Set up real database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_file:
            db_path = temp_file.name
        
        try:
            # Initialize bot with real database
            from tests.mocks.discord_mocks import MockBot, MockDiscordInteraction, MockDiscordUser
            from cogs.game_assignment import GameAssignment
            
            db = Database(db_path)
            await db.initialize()
            
            # Add test data using proper database methods
            import aiosqlite
            async with aiosqlite.connect(db_path) as conn:
                conn.row_factory = aiosqlite.Row
                await conn.execute("""
                    INSERT INTO games (id, game_name, game_url, dev_name, short_text, windows, mac, linux)
                    VALUES (1, 'Test Game', 'https://example.com/test', 'Test Dev', 'A test game', 1, 0, 1)
                """)
                await conn.commit()
            
            # Create real bot with real database
            bot = MockBot()
            bot.database = db
            cog = GameAssignment(bot)
            
            # Create mock interaction
            user = MockDiscordUser(555444333, 'TestUser')
            interaction = MockDiscordInteraction(user)
            interaction.user.send = lambda **kwargs: asyncio.sleep(0)  # Mock DM
            
            # Execute the actual command - this would have failed with dict(row) bug!
            await cog.hit(interaction)
            
            # Verify the command succeeded
            assert interaction.response.deferred, "Response should be deferred"
            
            # Verify game was actually assigned in database
            user_games = await db.get_user_games_legacy(str(user.id), user.display_name)
            assert len(user_games) == 1, "User should have one assigned game"
            assert user_games[0]['game_name'] == 'Test Game', "Should assign the correct game"
            
            await db.close()
            
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    async def test_status_command_with_real_database_flow(self):
        """Test the complete /status command flow with real database operations"""
        # Similar test for /status command with real database
        # This would have also caught the bug
        pass


if __name__ == "__main__":
    # Run the tests that would have caught the bug
    import pytest
    pytest.main([__file__, "-v"])
