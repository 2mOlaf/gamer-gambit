"""
Unit tests for the GameAssignment cog.
These tests verify command functionality without Discord dependencies.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from cogs.game_assignment import GameAssignment
from tests.mocks.discord_mocks import (
    MockBot, MockDiscordInteraction, MockDiscordUser, MockDiscordEmbed,
    MockDiscordColor, create_mock_interaction
)


@pytest.mark.unit
class TestGameAssignmentCog:
    """Test GameAssignment cog functionality"""
    
    def test_cog_initialization(self, mock_bot):
        """Test that cog initializes correctly"""
        cog = GameAssignment(mock_bot)
        assert cog.bot == mock_bot

    async def test_hit_command_success(self, game_assignment_cog, mock_interaction, sample_game_data):
        """Test successful game assignment with /hit command"""
        # Mock database to return sample game
        game_assignment_cog.bot.database.get_random_unassigned_game = AsyncMock(return_value=sample_game_data)
        game_assignment_cog.bot.database.assign_game_to_user = AsyncMock(return_value=True)
        
        # Mock user.send for DM (should not raise exception)
        mock_interaction.user.send = AsyncMock()
        
        # Execute command
        await game_assignment_cog.hit(mock_interaction)
        
        # Verify response was deferred
        assert mock_interaction.response.deferred is True
        
        # Verify database methods were called
        game_assignment_cog.bot.database.get_random_unassigned_game.assert_called_once()
        game_assignment_cog.bot.database.assign_game_to_user.assert_called_once_with(
            sample_game_data['id'],
            str(mock_interaction.user.id),
            mock_interaction.user.display_name
        )

    async def test_hit_command_no_games_available(self, game_assignment_cog, mock_interaction):
        """Test /hit command when no games are available"""
        # Mock database to return no games
        game_assignment_cog.bot.database.get_random_unassigned_game = AsyncMock(return_value=None)
        
        await game_assignment_cog.hit(mock_interaction)
        
        # Verify response was deferred
        assert mock_interaction.response.deferred is True
        
        # Verify no assignment was attempted
        assert not hasattr(game_assignment_cog.bot.database, 'assign_game_to_user') or \
               not game_assignment_cog.bot.database.assign_game_to_user.called

    async def test_hit_command_assignment_fails(self, game_assignment_cog, mock_interaction, sample_game_data):
        """Test /hit command when game assignment fails"""
        # Mock database to return game but fail assignment
        game_assignment_cog.bot.database.get_random_unassigned_game = AsyncMock(return_value=sample_game_data)
        game_assignment_cog.bot.database.assign_game_to_user = AsyncMock(return_value=False)
        
        await game_assignment_cog.hit(mock_interaction)
        
        # Verify response was deferred
        assert mock_interaction.response.deferred is True
        
        # Verify assignment was attempted but failed
        game_assignment_cog.bot.database.assign_game_to_user.assert_called_once()

    async def test_status_command_with_games(self, game_assignment_cog, mock_interaction):
        """Test /status command when user has assigned games"""
        # Mock games data
        mock_games = [
            {
                'id': 1,
                'game_name': 'Test Game',
                'game_url': 'https://example.com/game',
                'dev_name': 'Test Dev',
                'review_date': None,
                'assign_date': 1692000000000
            }
        ]
        
        game_assignment_cog.bot.database.get_user_games_legacy = AsyncMock(return_value=mock_games)
        
        await game_assignment_cog.status(mock_interaction)
        
        # Verify response was deferred
        assert mock_interaction.response.deferred is True
        
        # Verify database method was called with correct params
        game_assignment_cog.bot.database.get_user_games_legacy.assert_called_once_with(
            str(mock_interaction.user.id),
            mock_interaction.user.display_name
        )

    async def test_status_command_no_games(self, game_assignment_cog, mock_interaction):
        """Test /status command when user has no games"""
        # Mock empty games list
        game_assignment_cog.bot.database.get_user_games_legacy = AsyncMock(return_value=[])
        game_assignment_cog.bot.database.get_game_stats = AsyncMock(return_value={'total_games': 10})
        
        await game_assignment_cog.status(mock_interaction)
        
        # Verify response was deferred
        assert mock_interaction.response.deferred is True
        
        # Verify both database methods were called
        game_assignment_cog.bot.database.get_user_games_legacy.assert_called_once()
        game_assignment_cog.bot.database.get_game_stats.assert_called_once()

    async def test_status_command_empty_database(self, game_assignment_cog, mock_interaction):
        """Test /status command when database is empty"""
        # Mock empty games list and empty stats
        game_assignment_cog.bot.database.get_user_games_legacy = AsyncMock(return_value=[])
        game_assignment_cog.bot.database.get_game_stats = AsyncMock(return_value={'total_games': 0})
        
        await game_assignment_cog.status(mock_interaction)
        
        # Verify response was deferred
        assert mock_interaction.response.deferred is True

    async def test_status_command_with_other_user(self, game_assignment_cog, mock_interaction):
        """Test /status command checking another user's games"""
        other_user = MockDiscordUser(987654321, "OtherUser")
        
        game_assignment_cog.bot.database.get_user_games_legacy = AsyncMock(return_value=[])
        game_assignment_cog.bot.database.get_game_stats = AsyncMock(return_value={'total_games': 10})
        
        await game_assignment_cog.status(mock_interaction, other_user)
        
        # Verify database method was called with other user's info
        game_assignment_cog.bot.database.get_user_games_legacy.assert_called_once_with(
            str(other_user.id),
            other_user.display_name
        )

    async def test_mystats_command_with_games(self, game_assignment_cog, mock_interaction):
        """Test /mystats command when user has games"""
        # Mock games with different completion states
        mock_games = [
            {
                'id': 1, 'game_name': 'Completed Game', 'game_url': 'https://example.com/1',
                'review_date': '1692000000000', 'windows': True, 'mac': False, 'linux': False
            },
            {
                'id': 2, 'game_name': 'Pending Game', 'game_url': 'https://example.com/2',
                'review_date': None, 'windows': False, 'mac': True, 'linux': True
            }
        ]
        
        game_assignment_cog.bot.database.get_user_games_legacy = AsyncMock(return_value=mock_games)
        
        await game_assignment_cog.mystats(mock_interaction)
        
        # Verify response was deferred
        assert mock_interaction.response.deferred is True
        
        # Verify database method was called
        game_assignment_cog.bot.database.get_user_games_legacy.assert_called_once_with(
            str(mock_interaction.user.id),
            mock_interaction.user.display_name
        )

    async def test_mystats_command_no_games(self, game_assignment_cog, mock_interaction):
        """Test /mystats command when user has no games"""
        game_assignment_cog.bot.database.get_user_games_legacy = AsyncMock(return_value=[])
        game_assignment_cog.bot.database.get_game_stats = AsyncMock(return_value={'total_games': 10})
        
        await game_assignment_cog.mystats(mock_interaction)
        
        # Verify response was deferred
        assert mock_interaction.response.deferred is True

    async def test_gameinfo_command(self, game_assignment_cog, mock_interaction):
        """Test /gameinfo command"""
        # Mock database stats
        mock_stats = {
            'total_games': 100,
            'unassigned_games': 60,
            'assigned_games': 30,
            'completed_reviews': 10
        }
        
        game_assignment_cog.bot.database.get_game_stats = AsyncMock(return_value=mock_stats)
        
        await game_assignment_cog.gameinfo(mock_interaction)
        
        # Verify response was deferred
        assert mock_interaction.response.deferred is True
        
        # Verify database method was called
        game_assignment_cog.bot.database.get_game_stats.assert_called_once()

    async def test_command_error_handling(self, game_assignment_cog, mock_interaction):
        """Test that commands handle database errors gracefully"""
        # Mock database to raise an exception
        game_assignment_cog.bot.database.get_random_unassigned_game = AsyncMock(
            side_effect=Exception("Database error")
        )
        
        # Should not raise exception
        await game_assignment_cog.hit(mock_interaction)
        
        # Verify response was deferred (error handling should still defer)
        assert mock_interaction.response.deferred is True


@pytest.mark.unit
class TestGameAssignmentHelpers:
    """Test helper functions and edge cases"""
    
    def test_date_conversion_logic(self):
        """Test date conversion logic in status command"""
        from datetime import datetime
        
        # Test timestamp conversion
        timestamp = 1692000000000  # Example timestamp
        converted = datetime.fromtimestamp(int(timestamp) / 1000)
        assert isinstance(converted, datetime)
        
    def test_platform_detection_logic(self):
        """Test platform detection in mystats command"""
        mock_games = [
            {'windows': True, 'mac': False, 'linux': False},
            {'windows': False, 'mac': True, 'linux': True},
            {'windows': True, 'mac': True, 'linux': False}
        ]
        
        # Count platforms (simulating logic from mystats)
        windows_games = sum(1 for game in mock_games if game.get('windows'))
        mac_games = sum(1 for game in mock_games if game.get('mac'))
        linux_games = sum(1 for game in mock_games if game.get('linux'))
        
        assert windows_games == 2
        assert mac_games == 2
        assert linux_games == 1

    def test_completion_rate_calculation(self):
        """Test completion rate calculation logic"""
        mock_games = [
            {'review_date': '1692000000000'},  # Completed
            {'review_date': None},             # Not completed
            {'review_date': ''},               # Not completed
            {'review_date': '1692000001000'},  # Completed
        ]
        
        # Simulate completion rate calculation
        completed_games = sum(1 for game in mock_games 
                            if game.get('review_date') and str(game['review_date']).isdigit())
        total_games = len(mock_games)
        completion_rate = (completed_games / total_games * 100) if total_games > 0 else 0
        
        assert completed_games == 2
        assert total_games == 4
        assert completion_rate == 50.0
