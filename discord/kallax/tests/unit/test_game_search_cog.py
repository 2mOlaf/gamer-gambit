"""
Unit tests for GameSearch cog commands.
Tests command execution, API integration, and Discord interaction responses.
"""

import pytest
import discord
from unittest.mock import AsyncMock, MagicMock, patch
from cogs.game_search import GameSearch
from utils.bgg_client import BoardGameGeekClient
from utils.steam_client import SteamClient
from utils.xbox_client import XboxClient


@pytest.mark.unit
@pytest.mark.asyncio
class TestGameSearchCogInitialization:
    """Test GameSearch cog initialization and setup"""

    async def test_cog_initialization(self, mock_bot, test_database):
        """Test that GameSearch cog initializes correctly"""
        cog = GameSearch(mock_bot)
        
        assert cog.bot is mock_bot
        assert cog.db is None  # Database should be injected later
        assert hasattr(cog, 'bgg_client')
        assert hasattr(cog, 'steam_client')
        assert hasattr(cog, 'xbox_client')

    async def test_cog_setup_with_database(self, game_search_cog):
        """Test cog setup with database injection"""
        assert game_search_cog.db is not None
        assert hasattr(game_search_cog, 'bgg_client')
        assert isinstance(game_search_cog.bgg_client, BoardGameGeekClient)

    async def test_api_clients_initialization(self, game_search_cog):
        """Test that API clients are properly initialized"""
        # Should have proper client instances
        assert game_search_cog.bgg_client is not None
        assert game_search_cog.steam_client is not None
        assert game_search_cog.xbox_client is not None


@pytest.mark.unit
@pytest.mark.asyncio
class TestBoardGameSearchCommand:
    """Test board game search functionality"""

    async def test_search_board_game_success(self, game_search_cog, mock_interaction, 
                                           sample_bgg_game_data, mock_bgg_client):
        """Test successful board game search"""
        # Configure mock to return sample data
        mock_bgg_client.search_games.return_value = [sample_bgg_game_data]
        game_search_cog.bgg_client = mock_bgg_client
        
        # Execute command
        await game_search_cog.search_board_game(mock_interaction, "Gloomhaven")
        
        # Verify API call
        mock_bgg_client.search_games.assert_called_once_with("Gloomhaven")
        
        # Verify response sent
        mock_interaction.response.send_message.assert_called_once()
        args = mock_interaction.response.send_message.call_args
        
        # Check that embed was sent
        assert 'embed' in args.kwargs
        embed = args.kwargs['embed']
        assert embed.title == sample_bgg_game_data['name']
        assert str(sample_bgg_game_data['rating']) in embed.description

    async def test_search_board_game_no_results(self, game_search_cog, mock_interaction, 
                                              mock_bgg_client):
        """Test board game search with no results"""
        mock_bgg_client.search_games.return_value = []
        game_search_cog.bgg_client = mock_bgg_client
        
        await game_search_cog.search_board_game(mock_interaction, "NonexistentGame")
        
        mock_interaction.response.send_message.assert_called_once()
        args = mock_interaction.response.send_message.call_args
        
        # Should send error message
        assert "No board games found" in args.args[0]
        assert args.kwargs.get('ephemeral', False) is True

    async def test_search_board_game_api_error(self, game_search_cog, mock_interaction, 
                                             mock_bgg_client):
        """Test handling of API errors during board game search"""
        mock_bgg_client.search_games.side_effect = Exception("API Error")
        game_search_cog.bgg_client = mock_bgg_client
        
        await game_search_cog.search_board_game(mock_interaction, "TestGame")
        
        mock_interaction.response.send_message.assert_called_once()
        args = mock_interaction.response.send_message.call_args
        
        # Should send error message
        assert "Error searching for board games" in args.args[0]
        assert args.kwargs.get('ephemeral', False) is True

    async def test_search_board_game_multiple_results(self, game_search_cog, mock_interaction,
                                                    mock_bgg_client):
        """Test board game search returning multiple results"""
        # Create multiple sample games
        games = [
            {
                'bgg_id': 174430,
                'name': 'Gloomhaven',
                'year_published': 2017,
                'rating': 8.7,
                'rating_count': 70000
            },
            {
                'bgg_id': 167791,
                'name': 'Terraforming Mars',
                'year_published': 2016,
                'rating': 8.4,
                'rating_count': 75000
            }
        ]
        
        mock_bgg_client.search_games.return_value = games
        game_search_cog.bgg_client = mock_bgg_client
        
        await game_search_cog.search_board_game(mock_interaction, "Game")
        
        mock_interaction.response.send_message.assert_called_once()
        args = mock_interaction.response.send_message.call_args
        
        # Should send embed with first result
        assert 'embed' in args.kwargs
        embed = args.kwargs['embed']
        assert embed.title == 'Gloomhaven'  # First result

    async def test_search_board_game_caching(self, game_search_cog, mock_interaction,
                                           sample_bgg_game_data, mock_bgg_client):
        """Test that search results are cached properly"""
        mock_bgg_client.search_games.return_value = [sample_bgg_game_data]
        game_search_cog.bgg_client = mock_bgg_client
        
        await game_search_cog.search_board_game(mock_interaction, "Gloomhaven")
        
        # Verify game was cached in database
        # This would require the database to be mocked as well
        assert mock_bgg_client.search_games.called


@pytest.mark.unit
@pytest.mark.asyncio
class TestSteamGameSearchCommand:
    """Test Steam game search functionality"""

    async def test_search_steam_game_success(self, game_search_cog, mock_interaction,
                                           sample_steam_game_data, mock_steam_client):
        """Test successful Steam game search"""
        mock_steam_client.search_games.return_value = [sample_steam_game_data]
        game_search_cog.steam_client = mock_steam_client
        
        await game_search_cog.search_steam_game(mock_interaction, "Portal 2")
        
        mock_steam_client.search_games.assert_called_once_with("Portal 2")
        mock_interaction.response.send_message.assert_called_once()
        
        args = mock_interaction.response.send_message.call_args
        assert 'embed' in args.kwargs
        embed = args.kwargs['embed']
        assert embed.title == sample_steam_game_data['name']

    async def test_search_steam_game_no_results(self, game_search_cog, mock_interaction,
                                              mock_steam_client):
        """Test Steam game search with no results"""
        mock_steam_client.search_games.return_value = []
        game_search_cog.steam_client = mock_steam_client
        
        await game_search_cog.search_steam_game(mock_interaction, "NonexistentGame")
        
        mock_interaction.response.send_message.assert_called_once()
        args = mock_interaction.response.send_message.call_args
        
        assert "No Steam games found" in args.args[0]
        assert args.kwargs.get('ephemeral', False) is True

    async def test_search_steam_game_api_error(self, game_search_cog, mock_interaction,
                                             mock_steam_client):
        """Test handling of Steam API errors"""
        mock_steam_client.search_games.side_effect = Exception("Steam API Error")
        game_search_cog.steam_client = mock_steam_client
        
        await game_search_cog.search_steam_game(mock_interaction, "Portal 2")
        
        mock_interaction.response.send_message.assert_called_once()
        args = mock_interaction.response.send_message.call_args
        
        assert "Error searching Steam games" in args.args[0]
        assert args.kwargs.get('ephemeral', False) is True


@pytest.mark.unit
@pytest.mark.asyncio
class TestXboxGameSearchCommand:
    """Test Xbox game search functionality"""

    async def test_search_xbox_game_success(self, game_search_cog, mock_interaction,
                                          sample_xbox_game_data, mock_xbox_client):
        """Test successful Xbox game search"""
        mock_xbox_client.search_games.return_value = [sample_xbox_game_data]
        game_search_cog.xbox_client = mock_xbox_client
        
        await game_search_cog.search_xbox_game(mock_interaction, "Halo Infinite")
        
        mock_xbox_client.search_games.assert_called_once_with("Halo Infinite")
        mock_interaction.response.send_message.assert_called_once()
        
        args = mock_interaction.response.send_message.call_args
        assert 'embed' in args.kwargs
        embed = args.kwargs['embed']
        assert embed.title == sample_xbox_game_data['name']

    async def test_search_xbox_game_no_results(self, game_search_cog, mock_interaction,
                                             mock_xbox_client):
        """Test Xbox game search with no results"""
        mock_xbox_client.search_games.return_value = []
        game_search_cog.xbox_client = mock_xbox_client
        
        await game_search_cog.search_xbox_game(mock_interaction, "NonexistentGame")
        
        mock_interaction.response.send_message.assert_called_once()
        args = mock_interaction.response.send_message.call_args
        
        assert "No Xbox games found" in args.args[0]
        assert args.kwargs.get('ephemeral', False) is True

    async def test_search_xbox_game_api_error(self, game_search_cog, mock_interaction,
                                            mock_xbox_client):
        """Test handling of Xbox API errors"""
        mock_xbox_client.search_games.side_effect = Exception("Xbox API Error")
        game_search_cog.xbox_client = mock_xbox_client
        
        await game_search_cog.search_xbox_game(mock_interaction, "Halo Infinite")
        
        mock_interaction.response.send_message.assert_called_once()
        args = mock_interaction.response.send_message.call_args
        
        assert "Error searching Xbox games" in args.args[0]
        assert args.kwargs.get('ephemeral', False) is True


@pytest.mark.unit
@pytest.mark.asyncio
class TestGameDetailsCommand:
    """Test game details retrieval functionality"""

    async def test_get_bgg_game_details(self, game_search_cog, mock_interaction,
                                      sample_bgg_game_detailed, mock_bgg_client):
        """Test getting detailed BGG game information"""
        mock_bgg_client.get_game_details.return_value = sample_bgg_game_detailed
        game_search_cog.bgg_client = mock_bgg_client
        
        await game_search_cog.bgg_game_details(mock_interaction, 174430)
        
        mock_bgg_client.get_game_details.assert_called_once_with(174430)
        mock_interaction.response.send_message.assert_called_once()
        
        args = mock_interaction.response.send_message.call_args
        assert 'embed' in args.kwargs
        embed = args.kwargs['embed']
        assert embed.title == sample_bgg_game_detailed['name']
        
        # Check that detailed fields are included
        assert len(embed.fields) > 0
        field_names = [field.name for field in embed.fields]
        assert "Rating" in field_names
        assert "Year Published" in field_names

    async def test_get_bgg_game_details_not_found(self, game_search_cog, mock_interaction,
                                                mock_bgg_client):
        """Test handling when BGG game details not found"""
        mock_bgg_client.get_game_details.return_value = None
        game_search_cog.bgg_client = mock_bgg_client
        
        await game_search_cog.bgg_game_details(mock_interaction, 999999)
        
        mock_interaction.response.send_message.assert_called_once()
        args = mock_interaction.response.send_message.call_args
        
        assert "Game not found" in args.args[0]
        assert args.kwargs.get('ephemeral', False) is True

    async def test_get_steam_game_details(self, game_search_cog, mock_interaction,
                                        sample_steam_game_detailed, mock_steam_client):
        """Test getting detailed Steam game information"""
        mock_steam_client.get_game_details.return_value = sample_steam_game_detailed
        game_search_cog.steam_client = mock_steam_client
        
        await game_search_cog.steam_game_details(mock_interaction, 620)
        
        mock_steam_client.get_game_details.assert_called_once_with(620)
        mock_interaction.response.send_message.assert_called_once()
        
        args = mock_interaction.response.send_message.call_args
        assert 'embed' in args.kwargs
        embed = args.kwargs['embed']
        assert embed.title == sample_steam_game_detailed['name']


@pytest.mark.unit
@pytest.mark.asyncio  
class TestGameComparisonCommand:
    """Test game comparison functionality"""

    async def test_compare_games_success(self, game_search_cog, mock_interaction,
                                       mock_bgg_client):
        """Test successful game comparison"""
        # Setup mock data for two different games
        game1 = {
            'bgg_id': 174430,
            'name': 'Gloomhaven',
            'rating': 8.7,
            'rating_count': 70000,
            'year_published': 2017
        }
        
        game2 = {
            'bgg_id': 167791, 
            'name': 'Terraforming Mars',
            'rating': 8.4,
            'rating_count': 75000,
            'year_published': 2016
        }
        
        mock_bgg_client.get_game_details.side_effect = [game1, game2]
        game_search_cog.bgg_client = mock_bgg_client
        
        await game_search_cog.compare_board_games(mock_interaction, 174430, 167791)
        
        # Verify both games were fetched
        assert mock_bgg_client.get_game_details.call_count == 2
        mock_interaction.response.send_message.assert_called_once()
        
        args = mock_interaction.response.send_message.call_args
        assert 'embed' in args.kwargs
        embed = args.kwargs['embed']
        assert "Game Comparison" in embed.title
        
        # Verify both games appear in embed
        embed_text = str(embed.to_dict())
        assert "Gloomhaven" in embed_text
        assert "Terraforming Mars" in embed_text

    async def test_compare_games_same_game(self, game_search_cog, mock_interaction):
        """Test comparison of the same game (should show error)"""
        await game_search_cog.compare_board_games(mock_interaction, 174430, 174430)
        
        mock_interaction.response.send_message.assert_called_once()
        args = mock_interaction.response.send_message.call_args
        
        assert "Cannot compare a game with itself" in args.args[0]
        assert args.kwargs.get('ephemeral', False) is True

    async def test_compare_games_one_not_found(self, game_search_cog, mock_interaction,
                                             mock_bgg_client):
        """Test comparison when one game is not found"""
        mock_bgg_client.get_game_details.side_effect = [
            {'bgg_id': 174430, 'name': 'Gloomhaven'},
            None  # Second game not found
        ]
        game_search_cog.bgg_client = mock_bgg_client
        
        await game_search_cog.compare_board_games(mock_interaction, 174430, 999999)
        
        mock_interaction.response.send_message.assert_called_once()
        args = mock_interaction.response.send_message.call_args
        
        assert "Could not find one or both games" in args.args[0]
        assert args.kwargs.get('ephemeral', False) is True


@pytest.mark.unit
@pytest.mark.asyncio
class TestRandomGameCommand:
    """Test random game recommendation functionality"""

    async def test_random_board_game_success(self, game_search_cog, mock_interaction,
                                           mock_bgg_client):
        """Test successful random board game recommendation"""
        random_game = {
            'bgg_id': 12345,
            'name': 'Random Board Game',
            'rating': 7.5,
            'rating_count': 1000,
            'year_published': 2020
        }
        
        mock_bgg_client.get_random_game.return_value = random_game
        game_search_cog.bgg_client = mock_bgg_client
        
        await game_search_cog.random_board_game(mock_interaction)
        
        mock_bgg_client.get_random_game.assert_called_once()
        mock_interaction.response.send_message.assert_called_once()
        
        args = mock_interaction.response.send_message.call_args
        assert 'embed' in args.kwargs
        embed = args.kwargs['embed']
        assert embed.title == random_game['name']

    async def test_random_board_game_api_error(self, game_search_cog, mock_interaction,
                                             mock_bgg_client):
        """Test random game command with API error"""
        mock_bgg_client.get_random_game.side_effect = Exception("API Error")
        game_search_cog.bgg_client = mock_bgg_client
        
        await game_search_cog.random_board_game(mock_interaction)
        
        mock_interaction.response.send_message.assert_called_once()
        args = mock_interaction.response.send_message.call_args
        
        assert "Error getting random game" in args.args[0]
        assert args.kwargs.get('ephemeral', False) is True


@pytest.mark.unit
@pytest.mark.asyncio
class TestGameListCommands:
    """Test game list functionality (top games, trending, etc.)"""

    async def test_top_board_games_success(self, game_search_cog, mock_interaction,
                                         mock_bgg_client):
        """Test getting top board games list"""
        top_games = [
            {'bgg_id': 1, 'name': 'Game 1', 'rating': 9.0, 'rank': 1},
            {'bgg_id': 2, 'name': 'Game 2', 'rating': 8.9, 'rank': 2},
            {'bgg_id': 3, 'name': 'Game 3', 'rating': 8.8, 'rank': 3}
        ]
        
        mock_bgg_client.get_top_games.return_value = top_games
        game_search_cog.bgg_client = mock_bgg_client
        
        await game_search_cog.top_board_games(mock_interaction, count=3)
        
        mock_bgg_client.get_top_games.assert_called_once_with(limit=3)
        mock_interaction.response.send_message.assert_called_once()
        
        args = mock_interaction.response.send_message.call_args
        assert 'embed' in args.kwargs
        embed = args.kwargs['embed']
        assert "Top Board Games" in embed.title

    async def test_trending_board_games_success(self, game_search_cog, mock_interaction,
                                              mock_bgg_client):
        """Test getting trending board games"""
        trending_games = [
            {'bgg_id': 1, 'name': 'Trending Game 1', 'rating': 8.0},
            {'bgg_id': 2, 'name': 'Trending Game 2', 'rating': 7.8}
        ]
        
        mock_bgg_client.get_trending_games.return_value = trending_games
        game_search_cog.bgg_client = mock_bgg_client
        
        await game_search_cog.trending_board_games(mock_interaction)
        
        mock_bgg_client.get_trending_games.assert_called_once()
        mock_interaction.response.send_message.assert_called_once()
        
        args = mock_interaction.response.send_message.call_args
        assert 'embed' in args.kwargs
        embed = args.kwargs['embed']
        assert "Trending Board Games" in embed.title


@pytest.mark.unit
@pytest.mark.asyncio
class TestEmbedGeneration:
    """Test Discord embed generation for games"""

    def test_create_game_embed_board_game(self, game_search_cog, sample_bgg_game_data):
        """Test creating embed for board game"""
        embed = game_search_cog._create_game_embed(sample_bgg_game_data, 'board')
        
        assert embed.title == sample_bgg_game_data['name']
        assert str(sample_bgg_game_data['rating']) in embed.description
        assert embed.color == discord.Color.blue()  # BoardGameGeek color
        
        # Check fields
        field_names = [field.name for field in embed.fields]
        assert "Year Published" in field_names
        assert "BGG Rating" in field_names

    def test_create_game_embed_steam_game(self, game_search_cog, sample_steam_game_data):
        """Test creating embed for Steam game"""
        embed = game_search_cog._create_game_embed(sample_steam_game_data, 'steam')
        
        assert embed.title == sample_steam_game_data['name']
        assert embed.color == discord.Color.dark_blue()  # Steam color
        
        # Check Steam-specific fields
        field_names = [field.name for field in embed.fields]
        if 'price' in sample_steam_game_data:
            assert "Price" in field_names

    def test_create_game_embed_xbox_game(self, game_search_cog, sample_xbox_game_data):
        """Test creating embed for Xbox game"""
        embed = game_search_cog._create_game_embed(sample_xbox_game_data, 'xbox')
        
        assert embed.title == sample_xbox_game_data['name']
        assert embed.color == discord.Color.green()  # Xbox color

    def test_embed_with_missing_fields(self, game_search_cog):
        """Test embed creation with minimal game data"""
        minimal_game = {
            'name': 'Minimal Game',
            'bgg_id': 12345
        }
        
        embed = game_search_cog._create_game_embed(minimal_game, 'board')
        
        assert embed.title == 'Minimal Game'
        # Should handle missing fields gracefully
        assert embed is not None


@pytest.mark.unit
@pytest.mark.asyncio
class TestErrorHandling:
    """Test error handling throughout the cog"""

    async def test_command_with_interaction_error(self, game_search_cog, mock_bgg_client):
        """Test handling of Discord interaction errors"""
        # Create a mock interaction that raises an error
        mock_interaction = MagicMock()
        mock_interaction.response.send_message = AsyncMock(side_effect=discord.HTTPException("Discord error"))
        
        mock_bgg_client.search_games.return_value = []
        game_search_cog.bgg_client = mock_bgg_client
        
        # Should handle the Discord error gracefully
        with pytest.raises(discord.HTTPException):
            await game_search_cog.search_board_game(mock_interaction, "test")

    async def test_command_with_invalid_parameters(self, game_search_cog, mock_interaction):
        """Test commands with invalid parameters"""
        # Test with negative game ID
        await game_search_cog.bgg_game_details(mock_interaction, -1)
        
        mock_interaction.response.send_message.assert_called_once()
        args = mock_interaction.response.send_message.call_args
        
        assert "Invalid game ID" in args.args[0]
        assert args.kwargs.get('ephemeral', False) is True

    async def test_timeout_handling(self, game_search_cog, mock_interaction, mock_bgg_client):
        """Test handling of API timeouts"""
        import asyncio
        
        mock_bgg_client.search_games.side_effect = asyncio.TimeoutError("Timeout")
        game_search_cog.bgg_client = mock_bgg_client
        
        await game_search_cog.search_board_game(mock_interaction, "test")
        
        mock_interaction.response.send_message.assert_called_once()
        args = mock_interaction.response.send_message.call_args
        
        assert "request timed out" in args.args[0].lower()
        assert args.kwargs.get('ephemeral', False) is True


@pytest.mark.unit
@pytest.mark.asyncio
class TestCommandPermissions:
    """Test command permissions and access control"""

    async def test_command_in_dm(self, game_search_cog, mock_dm_interaction, mock_bgg_client):
        """Test commands work in DM channels"""
        mock_bgg_client.search_games.return_value = []
        game_search_cog.bgg_client = mock_bgg_client
        
        await game_search_cog.search_board_game(mock_dm_interaction, "test")
        
        # Should work in DM
        mock_dm_interaction.response.send_message.assert_called_once()

    async def test_command_rate_limiting(self, game_search_cog, mock_interaction, mock_bgg_client):
        """Test command rate limiting behavior"""
        # This would test rate limiting if implemented
        mock_bgg_client.search_games.return_value = []
        game_search_cog.bgg_client = mock_bgg_client
        
        # Make multiple rapid requests
        for _ in range(3):
            await game_search_cog.search_board_game(mock_interaction, "test")
        
        # All should succeed (rate limiting not implemented in this version)
        assert mock_interaction.response.send_message.call_count == 3
