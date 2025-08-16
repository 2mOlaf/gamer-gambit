"""
Unit tests for UserProfiles cog commands.
Tests profile management, validation, and Discord interactions.
"""

import pytest
import discord
from unittest.mock import AsyncMock, MagicMock
from cogs.user_profiles import UserProfiles


@pytest.mark.unit
@pytest.mark.asyncio
class TestUserProfilesCogInitialization:
    """Test UserProfiles cog initialization and setup"""

    async def test_cog_initialization(self, mock_bot):
        """Test that UserProfiles cog initializes correctly"""
        cog = UserProfiles(mock_bot)
        
        assert cog.bot is mock_bot
        assert cog.db is None  # Database should be injected later

    async def test_cog_setup_with_database(self, user_profiles_cog):
        """Test cog setup with database injection"""
        assert user_profiles_cog.db is not None


@pytest.mark.unit
@pytest.mark.asyncio
class TestSetProfileCommands:
    """Test profile setting commands"""

    async def test_set_bgg_profile_new_user(self, user_profiles_cog, mock_interaction):
        """Test setting BGG profile for new user"""
        # Mock database to return success for new profile creation
        user_profiles_cog.db.get_user_profile = AsyncMock(return_value=None)
        user_profiles_cog.db.create_user_profile = AsyncMock(return_value=True)
        
        await user_profiles_cog.set_bgg_profile(mock_interaction, "testuser")
        
        # Verify database calls
        user_profiles_cog.db.get_user_profile.assert_called_once_with(mock_interaction.user.id)
        user_profiles_cog.db.create_user_profile.assert_called_once_with(
            discord_id=mock_interaction.user.id,
            bgg_username="testuser"
        )
        
        # Verify response
        mock_interaction.response.send_message.assert_called_once()
        args = mock_interaction.response.send_message.call_args
        assert "BoardGameGeek profile set" in args.args[0]

    async def test_set_bgg_profile_existing_user(self, user_profiles_cog, mock_interaction,
                                               sample_user_profile):
        """Test setting BGG profile for existing user"""
        user_profiles_cog.db.get_user_profile = AsyncMock(return_value=sample_user_profile)
        user_profiles_cog.db.update_user_profile = AsyncMock(return_value=True)
        
        await user_profiles_cog.set_bgg_profile(mock_interaction, "newusername")
        
        # Verify update call
        user_profiles_cog.db.update_user_profile.assert_called_once_with(
            discord_id=mock_interaction.user.id,
            bgg_username="newusername"
        )
        
        # Verify response
        mock_interaction.response.send_message.assert_called_once()
        args = mock_interaction.response.send_message.call_args
        assert "BoardGameGeek profile updated" in args.args[0]

    async def test_set_bgg_profile_invalid_username(self, user_profiles_cog, mock_interaction):
        """Test setting BGG profile with invalid username"""
        # Test empty username
        await user_profiles_cog.set_bgg_profile(mock_interaction, "")
        
        mock_interaction.response.send_message.assert_called_once()
        args = mock_interaction.response.send_message.call_args
        assert "Username cannot be empty" in args.args[0]
        assert args.kwargs.get('ephemeral', False) is True

    async def test_set_bgg_profile_too_long(self, user_profiles_cog, mock_interaction):
        """Test setting BGG profile with username too long"""
        long_username = "a" * 51  # Assume 50 char limit
        
        await user_profiles_cog.set_bgg_profile(mock_interaction, long_username)
        
        mock_interaction.response.send_message.assert_called_once()
        args = mock_interaction.response.send_message.call_args
        assert "Username is too long" in args.args[0]
        assert args.kwargs.get('ephemeral', False) is True

    async def test_set_steam_profile_valid_id(self, user_profiles_cog, mock_interaction):
        """Test setting Steam profile with valid Steam ID"""
        valid_steam_id = "76561198000000001"
        
        user_profiles_cog.db.get_user_profile = AsyncMock(return_value=None)
        user_profiles_cog.db.create_user_profile = AsyncMock(return_value=True)
        
        await user_profiles_cog.set_steam_profile(mock_interaction, valid_steam_id)
        
        user_profiles_cog.db.create_user_profile.assert_called_once_with(
            discord_id=mock_interaction.user.id,
            steam_id=valid_steam_id
        )
        
        mock_interaction.response.send_message.assert_called_once()
        args = mock_interaction.response.send_message.call_args
        assert "Steam profile set" in args.args[0]

    async def test_set_steam_profile_invalid_id(self, user_profiles_cog, mock_interaction):
        """Test setting Steam profile with invalid Steam ID"""
        invalid_steam_id = "invalid_id"
        
        await user_profiles_cog.set_steam_profile(mock_interaction, invalid_steam_id)
        
        mock_interaction.response.send_message.assert_called_once()
        args = mock_interaction.response.send_message.call_args
        assert "Invalid Steam ID format" in args.args[0]
        assert args.kwargs.get('ephemeral', False) is True

    async def test_set_xbox_profile_valid_gamertag(self, user_profiles_cog, mock_interaction):
        """Test setting Xbox profile with valid gamertag"""
        valid_gamertag = "TestXboxUser"
        
        user_profiles_cog.db.get_user_profile = AsyncMock(return_value=None)
        user_profiles_cog.db.create_user_profile = AsyncMock(return_value=True)
        
        await user_profiles_cog.set_xbox_profile(mock_interaction, valid_gamertag)
        
        user_profiles_cog.db.create_user_profile.assert_called_once_with(
            discord_id=mock_interaction.user.id,
            xbox_gamertag=valid_gamertag
        )
        
        mock_interaction.response.send_message.assert_called_once()
        args = mock_interaction.response.send_message.call_args
        assert "Xbox profile set" in args.args[0]

    async def test_set_xbox_profile_invalid_gamertag(self, user_profiles_cog, mock_interaction):
        """Test setting Xbox profile with invalid gamertag"""
        # Test gamertag with invalid characters
        invalid_gamertag = "Test@#$%User"
        
        await user_profiles_cog.set_xbox_profile(mock_interaction, invalid_gamertag)
        
        mock_interaction.response.send_message.assert_called_once()
        args = mock_interaction.response.send_message.call_args
        assert "Invalid Xbox gamertag" in args.args[0]
        assert args.kwargs.get('ephemeral', False) is True

    async def test_set_profile_database_error(self, user_profiles_cog, mock_interaction):
        """Test handling database errors during profile creation"""
        user_profiles_cog.db.get_user_profile = AsyncMock(return_value=None)
        user_profiles_cog.db.create_user_profile = AsyncMock(return_value=False)
        
        await user_profiles_cog.set_bgg_profile(mock_interaction, "testuser")
        
        mock_interaction.response.send_message.assert_called_once()
        args = mock_interaction.response.send_message.call_args
        assert "Error saving profile" in args.args[0]
        assert args.kwargs.get('ephemeral', False) is True


@pytest.mark.unit
@pytest.mark.asyncio
class TestShowProfileCommand:
    """Test profile display functionality"""

    async def test_show_profile_existing_user(self, user_profiles_cog, mock_interaction,
                                            sample_user_profile):
        """Test showing profile for existing user"""
        user_profiles_cog.db.get_user_profile = AsyncMock(return_value=sample_user_profile)
        
        await user_profiles_cog.show_profile(mock_interaction, None)
        
        user_profiles_cog.db.get_user_profile.assert_called_once_with(mock_interaction.user.id)
        mock_interaction.response.send_message.assert_called_once()
        
        args = mock_interaction.response.send_message.call_args
        assert 'embed' in args.kwargs
        embed = args.kwargs['embed']
        
        # Verify embed contains profile information
        assert mock_interaction.user.display_name in embed.title
        embed_text = str(embed.to_dict())
        assert sample_user_profile['bgg_username'] in embed_text
        assert sample_user_profile['steam_id'] in embed_text
        assert sample_user_profile['xbox_gamertag'] in embed_text

    async def test_show_profile_other_user(self, user_profiles_cog, mock_interaction,
                                         sample_user_profile, mock_member):
        """Test showing profile for another user"""
        user_profiles_cog.db.get_user_profile = AsyncMock(return_value=sample_user_profile)
        
        await user_profiles_cog.show_profile(mock_interaction, mock_member)
        
        user_profiles_cog.db.get_user_profile.assert_called_once_with(mock_member.id)
        mock_interaction.response.send_message.assert_called_once()
        
        args = mock_interaction.response.send_message.call_args
        assert 'embed' in args.kwargs
        embed = args.kwargs['embed']
        assert mock_member.display_name in embed.title

    async def test_show_profile_no_profile(self, user_profiles_cog, mock_interaction):
        """Test showing profile when user has no profile"""
        user_profiles_cog.db.get_user_profile = AsyncMock(return_value=None)
        
        await user_profiles_cog.show_profile(mock_interaction, None)
        
        mock_interaction.response.send_message.assert_called_once()
        args = mock_interaction.response.send_message.call_args
        assert "No profile found" in args.args[0]
        assert args.kwargs.get('ephemeral', False) is True

    async def test_show_profile_partial_profile(self, user_profiles_cog, mock_interaction):
        """Test showing profile with only some platforms set"""
        partial_profile = {
            'discord_id': mock_interaction.user.id,
            'bgg_username': 'testuser',
            'steam_id': None,
            'xbox_gamertag': None,
            'weekly_stats_enabled': False,
            'created_at': '2023-12-01 00:00:00'
        }
        
        user_profiles_cog.db.get_user_profile = AsyncMock(return_value=partial_profile)
        
        await user_profiles_cog.show_profile(mock_interaction, None)
        
        mock_interaction.response.send_message.assert_called_once()
        args = mock_interaction.response.send_message.call_args
        assert 'embed' in args.kwargs
        embed = args.kwargs['embed']
        
        # Should show available platforms and indicate missing ones
        embed_text = str(embed.to_dict())
        assert 'testuser' in embed_text
        assert 'Not set' in embed_text  # For missing platforms


@pytest.mark.unit
@pytest.mark.asyncio
class TestDeleteProfileCommand:
    """Test profile deletion functionality"""

    async def test_delete_profile_existing_user(self, user_profiles_cog, mock_interaction,
                                              sample_user_profile):
        """Test deleting profile for existing user"""
        user_profiles_cog.db.get_user_profile = AsyncMock(return_value=sample_user_profile)
        user_profiles_cog.db.delete_user_profile = AsyncMock(return_value=True)
        
        await user_profiles_cog.delete_profile(mock_interaction)
        
        user_profiles_cog.db.delete_user_profile.assert_called_once_with(mock_interaction.user.id)
        mock_interaction.response.send_message.assert_called_once()
        
        args = mock_interaction.response.send_message.call_args
        assert "Profile deleted successfully" in args.args[0]

    async def test_delete_profile_no_profile(self, user_profiles_cog, mock_interaction):
        """Test deleting profile when user has no profile"""
        user_profiles_cog.db.get_user_profile = AsyncMock(return_value=None)
        
        await user_profiles_cog.delete_profile(mock_interaction)
        
        mock_interaction.response.send_message.assert_called_once()
        args = mock_interaction.response.send_message.call_args
        assert "No profile found to delete" in args.args[0]
        assert args.kwargs.get('ephemeral', False) is True

    async def test_delete_profile_database_error(self, user_profiles_cog, mock_interaction,
                                               sample_user_profile):
        """Test handling database errors during profile deletion"""
        user_profiles_cog.db.get_user_profile = AsyncMock(return_value=sample_user_profile)
        user_profiles_cog.db.delete_user_profile = AsyncMock(return_value=False)
        
        await user_profiles_cog.delete_profile(mock_interaction)
        
        mock_interaction.response.send_message.assert_called_once()
        args = mock_interaction.response.send_message.call_args
        assert "Error deleting profile" in args.args[0]
        assert args.kwargs.get('ephemeral', False) is True


@pytest.mark.unit
@pytest.mark.asyncio
class TestToggleStatsCommand:
    """Test weekly stats toggle functionality"""

    async def test_toggle_stats_enable(self, user_profiles_cog, mock_interaction,
                                     sample_user_profile):
        """Test enabling weekly stats"""
        # Start with stats disabled
        profile = sample_user_profile.copy()
        profile['weekly_stats_enabled'] = False
        
        user_profiles_cog.db.get_user_profile = AsyncMock(return_value=profile)
        user_profiles_cog.db.update_user_profile = AsyncMock(return_value=True)
        
        await user_profiles_cog.toggle_weekly_stats(mock_interaction)
        
        user_profiles_cog.db.update_user_profile.assert_called_once_with(
            discord_id=mock_interaction.user.id,
            weekly_stats_enabled=True
        )
        
        mock_interaction.response.send_message.assert_called_once()
        args = mock_interaction.response.send_message.call_args
        assert "Weekly stats enabled" in args.args[0]

    async def test_toggle_stats_disable(self, user_profiles_cog, mock_interaction,
                                      sample_user_profile):
        """Test disabling weekly stats"""
        # Start with stats enabled
        profile = sample_user_profile.copy()
        profile['weekly_stats_enabled'] = True
        
        user_profiles_cog.db.get_user_profile = AsyncMock(return_value=profile)
        user_profiles_cog.db.update_user_profile = AsyncMock(return_value=True)
        
        await user_profiles_cog.toggle_weekly_stats(mock_interaction)
        
        user_profiles_cog.db.update_user_profile.assert_called_once_with(
            discord_id=mock_interaction.user.id,
            weekly_stats_enabled=False
        )
        
        mock_interaction.response.send_message.assert_called_once()
        args = mock_interaction.response.send_message.call_args
        assert "Weekly stats disabled" in args.args[0]

    async def test_toggle_stats_no_profile(self, user_profiles_cog, mock_interaction):
        """Test toggling stats when user has no profile"""
        user_profiles_cog.db.get_user_profile = AsyncMock(return_value=None)
        
        await user_profiles_cog.toggle_weekly_stats(mock_interaction)
        
        mock_interaction.response.send_message.assert_called_once()
        args = mock_interaction.response.send_message.call_args
        assert "No profile found" in args.args[0]
        assert args.kwargs.get('ephemeral', False) is True


@pytest.mark.unit
@pytest.mark.asyncio
class TestValidationHelpers:
    """Test validation helper methods"""

    def test_validate_steam_id_valid(self, user_profiles_cog):
        """Test Steam ID validation with valid IDs"""
        valid_ids = [
            "76561198000000001",
            "76561198123456789",
            "76561197960265729"  # Minimum valid Steam ID
        ]
        
        for steam_id in valid_ids:
            assert user_profiles_cog._validate_steam_id(steam_id) is True

    def test_validate_steam_id_invalid(self, user_profiles_cog):
        """Test Steam ID validation with invalid IDs"""
        invalid_ids = [
            "invalid_id",
            "12345",
            "76561198000000000",  # Too low
            "76561199999999999",  # Too high
            "",
            None
        ]
        
        for steam_id in invalid_ids:
            assert user_profiles_cog._validate_steam_id(steam_id) is False

    def test_validate_xbox_gamertag_valid(self, user_profiles_cog):
        """Test Xbox gamertag validation with valid gamertags"""
        valid_gamertags = [
            "TestUser",
            "Test User 123",
            "Test-User_123",
            "a" * 15  # Max length
        ]
        
        for gamertag in valid_gamertags:
            assert user_profiles_cog._validate_xbox_gamertag(gamertag) is True

    def test_validate_xbox_gamertag_invalid(self, user_profiles_cog):
        """Test Xbox gamertag validation with invalid gamertags"""
        invalid_gamertags = [
            "",
            "a",  # Too short
            "a" * 16,  # Too long
            "Test@User",  # Invalid character
            "Test#User",  # Invalid character
            None
        ]
        
        for gamertag in invalid_gamertags:
            assert user_profiles_cog._validate_xbox_gamertag(gamertag) is False

    def test_validate_bgg_username_valid(self, user_profiles_cog):
        """Test BGG username validation with valid usernames"""
        valid_usernames = [
            "testuser",
            "test_user",
            "TestUser123",
            "a" * 50  # Max length
        ]
        
        for username in valid_usernames:
            assert user_profiles_cog._validate_bgg_username(username) is True

    def test_validate_bgg_username_invalid(self, user_profiles_cog):
        """Test BGG username validation with invalid usernames"""
        invalid_usernames = [
            "",
            "a" * 51,  # Too long
            "test user",  # Spaces not allowed
            "test@user",  # Invalid character
            None
        ]
        
        for username in invalid_usernames:
            assert user_profiles_cog._validate_bgg_username(username) is False


@pytest.mark.unit
@pytest.mark.asyncio
class TestEmbedGeneration:
    """Test Discord embed generation for profiles"""

    def test_create_profile_embed_complete(self, user_profiles_cog, mock_user,
                                         sample_user_profile):
        """Test creating embed for complete profile"""
        embed = user_profiles_cog._create_profile_embed(mock_user, sample_user_profile)
        
        assert embed.title == f"{mock_user.display_name}'s Gaming Profile"
        assert embed.color == discord.Color.blue()
        
        # Check fields
        field_names = [field.name for field in embed.fields]
        assert "BoardGameGeek" in field_names
        assert "Steam" in field_names
        assert "Xbox" in field_names
        
        # Check field values
        embed_text = str(embed.to_dict())
        assert sample_user_profile['bgg_username'] in embed_text
        assert sample_user_profile['steam_id'] in embed_text
        assert sample_user_profile['xbox_gamertag'] in embed_text

    def test_create_profile_embed_partial(self, user_profiles_cog, mock_user):
        """Test creating embed for partial profile"""
        partial_profile = {
            'discord_id': mock_user.id,
            'bgg_username': 'testuser',
            'steam_id': None,
            'xbox_gamertag': None,
            'weekly_stats_enabled': False,
            'created_at': '2023-12-01 00:00:00'
        }
        
        embed = user_profiles_cog._create_profile_embed(mock_user, partial_profile)
        
        assert embed.title == f"{mock_user.display_name}'s Gaming Profile"
        
        # Should show set platforms and indicate unset ones
        embed_text = str(embed.to_dict())
        assert 'testuser' in embed_text
        assert 'Not set' in embed_text

    def test_create_profile_embed_stats_enabled(self, user_profiles_cog, mock_user,
                                              sample_user_profile):
        """Test embed shows weekly stats status"""
        profile = sample_user_profile.copy()
        profile['weekly_stats_enabled'] = True
        
        embed = user_profiles_cog._create_profile_embed(mock_user, profile)
        
        embed_text = str(embed.to_dict())
        assert 'Weekly Stats' in embed_text
        assert 'Enabled' in embed_text


@pytest.mark.unit
@pytest.mark.asyncio
class TestErrorHandling:
    """Test error handling throughout the cog"""

    async def test_database_connection_error(self, user_profiles_cog, mock_interaction):
        """Test handling database connection errors"""
        user_profiles_cog.db.get_user_profile = AsyncMock(side_effect=Exception("DB Error"))
        
        await user_profiles_cog.show_profile(mock_interaction, None)
        
        mock_interaction.response.send_message.assert_called_once()
        args = mock_interaction.response.send_message.call_args
        assert "Error retrieving profile" in args.args[0]
        assert args.kwargs.get('ephemeral', False) is True

    async def test_interaction_error(self, user_profiles_cog, mock_interaction):
        """Test handling Discord interaction errors"""
        mock_interaction.response.send_message = AsyncMock(
            side_effect=discord.HTTPException("Discord error")
        )
        user_profiles_cog.db.get_user_profile = AsyncMock(return_value=None)
        
        with pytest.raises(discord.HTTPException):
            await user_profiles_cog.show_profile(mock_interaction, None)

    async def test_invalid_user_parameter(self, user_profiles_cog, mock_interaction):
        """Test handling invalid user parameter"""
        # Create a mock member that doesn't exist
        fake_member = MagicMock()
        fake_member.id = 999999999
        fake_member.display_name = "NonExistentUser"
        
        user_profiles_cog.db.get_user_profile = AsyncMock(return_value=None)
        
        await user_profiles_cog.show_profile(mock_interaction, fake_member)
        
        mock_interaction.response.send_message.assert_called_once()
        args = mock_interaction.response.send_message.call_args
        assert "No profile found" in args.args[0]


@pytest.mark.unit
@pytest.mark.asyncio
class TestCommandPermissions:
    """Test command permissions and access control"""

    async def test_profile_commands_in_dm(self, user_profiles_cog, mock_dm_interaction):
        """Test profile commands work in DM channels"""
        user_profiles_cog.db.get_user_profile = AsyncMock(return_value=None)
        
        await user_profiles_cog.show_profile(mock_dm_interaction, None)
        
        # Should work in DM
        mock_dm_interaction.response.send_message.assert_called_once()

    async def test_set_profile_self_only(self, user_profiles_cog, mock_interaction):
        """Test that users can only set their own profiles"""
        # Profile setting commands should only affect the command user
        user_profiles_cog.db.get_user_profile = AsyncMock(return_value=None)
        user_profiles_cog.db.create_user_profile = AsyncMock(return_value=True)
        
        await user_profiles_cog.set_bgg_profile(mock_interaction, "testuser")
        
        # Should use interaction.user.id, not allow setting for others
        user_profiles_cog.db.create_user_profile.assert_called_once()
        call_args = user_profiles_cog.db.create_user_profile.call_args
        assert call_args[1]['discord_id'] == mock_interaction.user.id


@pytest.mark.unit
@pytest.mark.asyncio
class TestCogEventHandlers:
    """Test cog event handlers if any exist"""

    async def test_cog_load_event(self, user_profiles_cog):
        """Test cog loading event"""
        # This would test any on_ready or similar event handlers
        # if implemented in the cog
        pass

    async def test_cog_unload_cleanup(self, user_profiles_cog):
        """Test cleanup on cog unload"""
        # This would test any cleanup logic when the cog is unloaded
        pass


@pytest.mark.unit
@pytest.mark.performance
class TestPerformance:
    """Test performance aspects of profile operations"""

    async def test_profile_retrieval_performance(self, user_profiles_cog, mock_interaction,
                                               sample_user_profile, performance_threshold):
        """Test that profile retrieval is performant"""
        user_profiles_cog.db.get_user_profile = AsyncMock(return_value=sample_user_profile)
        
        import time
        start_time = time.time()
        
        await user_profiles_cog.show_profile(mock_interaction, None)
        
        execution_time = time.time() - start_time
        assert execution_time < performance_threshold['database_query']

    async def test_bulk_profile_operations(self, user_profiles_cog, mock_interaction):
        """Test performance with multiple profile operations"""
        user_profiles_cog.db.get_user_profile = AsyncMock(return_value=None)
        user_profiles_cog.db.create_user_profile = AsyncMock(return_value=True)
        
        import time
        start_time = time.time()
        
        # Simulate multiple profile setting operations
        for i in range(10):
            await user_profiles_cog.set_bgg_profile(mock_interaction, f"user{i}")
        
        execution_time = time.time() - start_time
        # Should complete 10 operations in reasonable time
        assert execution_time < 2.0  # 2 seconds for 10 operations
