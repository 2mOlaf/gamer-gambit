"""
Integration tests for GameAssignment cog with real database interactions.
These tests use a temporary database but test full command workflows.
"""

import pytest
import tempfile
import os
import json
from unittest.mock import AsyncMock, MagicMock
from cogs.game_assignment import GameAssignment
from utils.database import Database
from tests.mocks.discord_mocks import MockBot, MockDiscordInteraction, MockDiscordUser


@pytest.mark.integration
class TestGameAssignmentIntegration:
    """Integration tests for GameAssignment cog with real database"""

    @pytest.fixture
    async def real_database(self):
        """Create a real database instance for integration testing"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_file:
            db_path = temp_file.name
            
        try:
            # Create database and initialize
            db = Database(db_path)
            await db.initialize()
            
            # Add some test games
            await db._connection.execute("""
                INSERT INTO games (id, game_name, game_url, dev_name, short_text, windows, mac, linux)
                VALUES 
                    (1, 'Unassigned Game 1', 'https://example.com/game1', 'Dev Studio', 'A test game', 1, 0, 1),
                    (2, 'Unassigned Game 2', 'https://example.com/game2', 'Indie Dev', 'Another test game', 1, 1, 0),
                    (3, 'Already Assigned', 'https://example.com/game3', 'Studio X', 'Already assigned game', 1, 1, 1)
            """)
            
            # Assign one game to a test user
            await db._connection.execute("""
                UPDATE games SET reviewer = ?, assign_date = ? WHERE id = 3
            """, ('123456789', 1692000000000))
            
            await db._connection.commit()
            yield db
            
        finally:
            await db.close()
            if os.path.exists(db_path):
                os.unlink(db_path)

    @pytest.fixture
    def integration_bot(self, real_database):
        """Create a bot with real database for integration tests"""
        bot = MockBot()
        bot.database = real_database
        return bot

    @pytest.fixture
    def integration_cog(self, integration_bot):
        """Create GameAssignment cog with real database"""
        return GameAssignment(integration_bot)

    @pytest.fixture
    def test_user(self):
        """Create a test user for integration tests"""
        return MockDiscordUser(999888777, "IntegrationTestUser")

    @pytest.fixture
    def test_interaction(self, test_user):
        """Create a test interaction for integration tests"""
        interaction = MockDiscordInteraction(test_user)
        interaction.user.send = AsyncMock()  # Mock DM sending
        return interaction

    async def test_hit_command_full_workflow(self, integration_cog, test_interaction):
        """Test the full /hit command workflow with real database"""
        # Execute the hit command
        await integration_cog.hit(test_interaction)
        
        # Verify response was deferred
        assert test_interaction.response.deferred is True
        
        # Check that a game was assigned to the user in the database
        user_games = await integration_cog.bot.database.get_user_games_legacy(
            str(test_interaction.user.id),
            test_interaction.user.display_name
        )
        
        # Should have one assigned game now
        assert len(user_games) == 1
        assigned_game = user_games[0]
        assert assigned_game['game_name'] in ['Unassigned Game 1', 'Unassigned Game 2']

    async def test_status_command_with_real_data(self, integration_cog, test_interaction):
        """Test /status command with real database data"""
        # First assign a game to the user
        await integration_cog.hit(test_interaction)
        
        # Now check status
        await integration_cog.status(test_interaction)
        
        # Verify response was deferred
        assert test_interaction.response.deferred is True
        
        # Verify that followup.send was called (status info was sent)
        assert test_interaction.followup.send.called

    async def test_mystats_command_with_real_data(self, integration_cog, test_interaction):
        """Test /mystats command with real database data"""
        # First assign a game to the user
        await integration_cog.hit(test_interaction)
        
        # Now check mystats
        await integration_cog.mystats(test_interaction)
        
        # Verify response was deferred
        assert test_interaction.response.deferred is True
        
        # Verify that followup.send was called (stats info was sent)
        assert test_interaction.followup.send.called

    async def test_gameinfo_command_with_real_stats(self, integration_cog, test_interaction):
        """Test /gameinfo command with real database statistics"""
        await integration_cog.gameinfo(test_interaction)
        
        # Verify response was deferred
        assert test_interaction.response.deferred is True
        
        # Verify that followup.send was called (game info was sent)
        assert test_interaction.followup.send.called

    async def test_multiple_users_different_games(self, integration_cog):
        """Test that different users get different games"""
        # Create two different users
        user1 = MockDiscordUser(111111111, "User1")
        user2 = MockDiscordUser(222222222, "User2")
        
        interaction1 = MockDiscordInteraction(user1)
        interaction1.user.send = AsyncMock()
        interaction2 = MockDiscordInteraction(user2)
        interaction2.user.send = AsyncMock()
        
        # Both users hit for games
        await integration_cog.hit(interaction1)
        await integration_cog.hit(interaction2)
        
        # Get their assigned games
        user1_games = await integration_cog.bot.database.get_user_games_legacy(
            str(user1.id), user1.display_name
        )
        user2_games = await integration_cog.bot.database.get_user_games_legacy(
            str(user2.id), user2.display_name
        )
        
        # Both should have one game assigned
        assert len(user1_games) == 1
        assert len(user2_games) == 1
        
        # They should have different games
        assert user1_games[0]['id'] != user2_games[0]['id']

    async def test_no_more_games_available(self, integration_cog):
        """Test what happens when all games are assigned"""
        # Create three users (we have 2 unassigned games + 1 already assigned)
        users = []
        interactions = []
        
        for i in range(3):
            user = MockDiscordUser(333333000 + i, f"User{i}")
            interaction = MockDiscordInteraction(user)
            interaction.user.send = AsyncMock()
            users.append(user)
            interactions.append(interaction)
        
        # First two users should get games
        await integration_cog.hit(interactions[0])
        await integration_cog.hit(interactions[1])
        
        # Third user should get a message that no games are available
        await integration_cog.hit(interactions[2])
        
        # Check that third user has no games assigned
        user3_games = await integration_cog.bot.database.get_user_games_legacy(
            str(users[2].id), users[2].display_name
        )
        assert len(user3_games) == 0

    async def test_status_check_other_user(self, integration_cog):
        """Test checking status of another user"""
        # Create target user and assign them a game
        target_user = MockDiscordUser(444444444, "TargetUser")
        target_interaction = MockDiscordInteraction(target_user)
        target_interaction.user.send = AsyncMock()
        
        await integration_cog.hit(target_interaction)
        
        # Create checker user who will check target's status
        checker_user = MockDiscordUser(555555555, "CheckerUser")
        checker_interaction = MockDiscordInteraction(checker_user)
        
        # Check target user's status
        await integration_cog.status(checker_interaction, target_user)
        
        # Verify response was deferred and sent
        assert checker_interaction.response.deferred is True
        assert checker_interaction.followup.send.called
