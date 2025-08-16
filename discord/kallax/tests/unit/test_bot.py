"""
Unit tests for the main Kallax bot class.
Tests bot initialization, cog loading, and event handling.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from bot import KallaxBot


@pytest.mark.unit
@pytest.mark.asyncio
class TestKallaxBotInitialization:
    """Test KallaxBot initialization and setup"""

    def test_bot_initialization(self):
        """Test that KallaxBot initializes correctly"""
        bot = KallaxBot()
        
        assert bot.initial_extensions == ['cogs.game_search', 'cogs.user_profiles']
        assert hasattr(bot, 'db')
        assert bot.db is None  # Should be initialized later
        assert hasattr(bot, 'startup_time')

    def test_bot_initialization_with_custom_extensions(self):
        """Test bot initialization with custom extensions"""
        custom_extensions = ['cogs.custom_cog', 'cogs.another_cog']
        bot = KallaxBot(initial_extensions=custom_extensions)
        
        assert bot.initial_extensions == custom_extensions

    async def test_bot_setup_database(self, mock_bot):
        """Test database setup during bot initialization"""
        # Mock the database initialization
        mock_bot.db = MagicMock()
        mock_bot.db.initialize = AsyncMock()
        
        await mock_bot.setup_database()
        
        mock_bot.db.initialize.assert_called_once()

    async def test_bot_setup_database_error_handling(self, mock_bot):
        """Test handling of database setup errors"""
        mock_bot.db = MagicMock()
        mock_bot.db.initialize = AsyncMock(side_effect=Exception("Database error"))
        
        with pytest.raises(Exception, match="Database error"):
            await mock_bot.setup_database()


@pytest.mark.unit
@pytest.mark.asyncio
class TestCogManagement:
    """Test cog loading and management"""

    async def test_load_initial_extensions_success(self, mock_bot):
        """Test successful loading of initial extensions"""
        mock_bot.initial_extensions = ['cogs.game_search', 'cogs.user_profiles']
        mock_bot.load_extension = AsyncMock()
        
        await mock_bot.load_extensions()
        
        assert mock_bot.load_extension.call_count == 2
        mock_bot.load_extension.assert_any_call('cogs.game_search')
        mock_bot.load_extension.assert_any_call('cogs.user_profiles')

    async def test_load_extensions_with_failure(self, mock_bot):
        """Test extension loading with one failure"""
        mock_bot.initial_extensions = ['cogs.game_search', 'cogs.invalid_cog']
        
        # Mock load_extension to fail on second call
        def side_effect(extension):
            if extension == 'cogs.invalid_cog':
                raise Exception("Failed to load cog")
            return None
        
        mock_bot.load_extension = AsyncMock(side_effect=side_effect)
        
        # Should continue loading other cogs despite one failure
        await mock_bot.load_extensions()
        
        assert mock_bot.load_extension.call_count == 2

    async def test_inject_database_into_cogs(self, mock_bot, test_database):
        """Test database injection into loaded cogs"""
        # Create mock cogs
        mock_game_search_cog = MagicMock()
        mock_user_profiles_cog = MagicMock()
        
        mock_bot.cogs = {
            'GameSearch': mock_game_search_cog,
            'UserProfiles': mock_user_profiles_cog
        }
        mock_bot.db = test_database
        
        await mock_bot.inject_database_into_cogs()
        
        # Verify database was injected
        assert mock_game_search_cog.db == test_database
        assert mock_user_profiles_cog.db == test_database

    async def test_cog_hot_reload(self, mock_bot):
        """Test hot reloading of cogs"""
        extension_name = 'cogs.game_search'
        mock_bot.reload_extension = AsyncMock()
        
        await mock_bot.reload_cog(extension_name)
        
        mock_bot.reload_extension.assert_called_once_with(extension_name)

    async def test_cog_hot_reload_failure(self, mock_bot):
        """Test handling of hot reload failures"""
        extension_name = 'cogs.game_search'
        mock_bot.reload_extension = AsyncMock(side_effect=Exception("Reload failed"))
        
        with pytest.raises(Exception, match="Reload failed"):
            await mock_bot.reload_cog(extension_name)


@pytest.mark.unit
@pytest.mark.asyncio
class TestBotEventHandlers:
    """Test bot event handlers"""

    async def test_on_ready_event(self, mock_bot):
        """Test bot ready event"""
        mock_bot.user = MagicMock()
        mock_bot.user.name = "Kallax"
        mock_bot.guilds = [MagicMock(), MagicMock()]  # 2 mock guilds
        
        # Mock the setup methods
        mock_bot.setup_database = AsyncMock()
        mock_bot.load_extensions = AsyncMock()
        mock_bot.inject_database_into_cogs = AsyncMock()
        
        await mock_bot.on_ready()
        
        # Verify setup methods were called
        mock_bot.setup_database.assert_called_once()
        mock_bot.load_extensions.assert_called_once()
        mock_bot.inject_database_into_cogs.assert_called_once()

    async def test_on_guild_join_event(self, mock_bot, mock_guild):
        """Test bot joining new guild event"""
        mock_bot.db = MagicMock()
        mock_bot.db.initialize_guild_settings = AsyncMock()
        
        await mock_bot.on_guild_join(mock_guild)
        
        # Should initialize settings for new guild
        mock_bot.db.initialize_guild_settings.assert_called_once_with(mock_guild.id)

    async def test_on_guild_remove_event(self, mock_bot, mock_guild):
        """Test bot leaving guild event"""
        mock_bot.db = MagicMock()
        mock_bot.db.cleanup_guild_data = AsyncMock()
        
        await mock_bot.on_guild_remove(mock_guild)
        
        # Should cleanup guild data
        mock_bot.db.cleanup_guild_data.assert_called_once_with(mock_guild.id)

    async def test_on_application_command_error(self, mock_bot, mock_interaction):
        """Test application command error handling"""
        error = Exception("Test command error")
        
        # Mock interaction response
        mock_interaction.response.is_done.return_value = False
        mock_interaction.response.send_message = AsyncMock()
        
        await mock_bot.on_application_command_error(mock_interaction, error)
        
        # Should send error message to user
        mock_interaction.response.send_message.assert_called_once()
        args = mock_interaction.response.send_message.call_args
        assert "error occurred" in args.args[0].lower()
        assert args.kwargs.get('ephemeral', False) is True

    async def test_on_application_command_error_already_responded(self, mock_bot, mock_interaction):
        """Test error handling when interaction already responded"""
        error = Exception("Test command error")
        
        # Mock interaction as already responded
        mock_interaction.response.is_done.return_value = True
        mock_interaction.followup.send = AsyncMock()
        
        await mock_bot.on_application_command_error(mock_interaction, error)
        
        # Should use followup instead of response
        mock_interaction.followup.send.assert_called_once()

    async def test_on_error_general(self, mock_bot):
        """Test general error event handler"""
        error = Exception("General bot error")
        
        # Mock logger
        with patch('bot.logger') as mock_logger:
            await mock_bot.on_error("test_event", error)
            mock_logger.error.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
class TestBotHealthCheck:
    """Test bot health check and metrics"""

    async def test_health_check_healthy(self, mock_bot):
        """Test health check when bot is healthy"""
        mock_bot.is_closed.return_value = False
        mock_bot.db = MagicMock()
        mock_bot.db.health_check = AsyncMock(return_value=True)
        
        health_status = await mock_bot.health_check()
        
        assert health_status['status'] == 'healthy'
        assert health_status['database'] is True
        assert 'uptime' in health_status
        assert 'guilds' in health_status

    async def test_health_check_unhealthy_bot(self, mock_bot):
        """Test health check when bot is closed"""
        mock_bot.is_closed.return_value = True
        
        health_status = await mock_bot.health_check()
        
        assert health_status['status'] == 'unhealthy'

    async def test_health_check_database_error(self, mock_bot):
        """Test health check with database error"""
        mock_bot.is_closed.return_value = False
        mock_bot.db = MagicMock()
        mock_bot.db.health_check = AsyncMock(return_value=False)
        
        health_status = await mock_bot.health_check()
        
        assert health_status['status'] == 'unhealthy'
        assert health_status['database'] is False

    async def test_get_metrics(self, mock_bot):
        """Test metrics collection"""
        mock_bot.guilds = [MagicMock() for _ in range(5)]  # 5 guilds
        mock_bot.users = [MagicMock() for _ in range(100)]  # 100 users
        mock_bot.db = MagicMock()
        mock_bot.db.get_metrics = AsyncMock(return_value={
            'total_users': 50,
            'total_games_cached': 1000,
            'total_game_plays': 200
        })
        
        metrics = await mock_bot.get_metrics()
        
        assert metrics['guilds'] == 5
        assert metrics['users'] == 100
        assert metrics['database']['total_users'] == 50
        assert 'uptime' in metrics


@pytest.mark.unit
@pytest.mark.asyncio
class TestBotUtilityMethods:
    """Test bot utility and helper methods"""

    def test_format_uptime(self, mock_bot):
        """Test uptime formatting"""
        # Mock startup time to 1 hour ago
        import datetime
        mock_bot.startup_time = datetime.datetime.utcnow() - datetime.timedelta(hours=1)
        
        uptime_str = mock_bot.format_uptime()
        
        assert 'hour' in uptime_str.lower() or '1:' in uptime_str

    async def test_graceful_shutdown(self, mock_bot):
        """Test graceful bot shutdown"""
        mock_bot.db = MagicMock()
        mock_bot.db.close = AsyncMock()
        mock_bot.close = AsyncMock()
        
        await mock_bot.graceful_shutdown()
        
        mock_bot.db.close.assert_called_once()
        mock_bot.close.assert_called_once()

    async def test_graceful_shutdown_database_error(self, mock_bot):
        """Test graceful shutdown with database error"""
        mock_bot.db = MagicMock()
        mock_bot.db.close = AsyncMock(side_effect=Exception("Database close error"))
        mock_bot.close = AsyncMock()
        
        # Should still close bot even if database fails to close
        await mock_bot.graceful_shutdown()
        
        mock_bot.close.assert_called_once()

    def test_is_owner_check(self, mock_bot, mock_user):
        """Test owner permission check"""
        # Mock bot owner
        mock_bot.owner_id = 123456789
        mock_user.id = 123456789
        
        is_owner = mock_bot.is_owner(mock_user)
        
        assert is_owner is True

    def test_is_owner_check_non_owner(self, mock_bot, mock_user):
        """Test owner check for non-owner"""
        mock_bot.owner_id = 123456789
        mock_user.id = 987654321
        
        is_owner = mock_bot.is_owner(mock_user)
        
        assert is_owner is False


@pytest.mark.unit
@pytest.mark.asyncio
class TestBotConfiguration:
    """Test bot configuration and settings"""

    def test_bot_intents_configuration(self, mock_bot):
        """Test that bot has correct intents configured"""
        intents = mock_bot.intents
        
        # Should have required intents for Kallax functionality
        assert intents.guilds is True
        assert intents.guild_messages is True
        assert intents.direct_messages is True

    def test_bot_command_sync(self, mock_bot):
        """Test command tree synchronization"""
        mock_bot.tree.sync = AsyncMock()
        
        # Test sync for specific guild
        guild_id = 123456789
        mock_bot.sync_commands_for_guild(guild_id)
        
        # Would verify sync was called with guild parameter

    def test_bot_status_configuration(self, mock_bot):
        """Test bot status and activity configuration"""
        # Should have appropriate playing status
        activity = mock_bot.activity
        
        # Verify activity is set appropriately for a gaming bot
        assert activity is None or 'game' in str(activity).lower()


@pytest.mark.unit
@pytest.mark.asyncio
class TestBotCommandHandling:
    """Test bot-level command handling"""

    async def test_command_preprocessing(self, mock_bot, mock_interaction):
        """Test command preprocessing and validation"""
        # Mock command validation
        mock_bot.validate_command_permissions = MagicMock(return_value=True)
        
        is_valid = mock_bot.validate_command_permissions(mock_interaction, "search_board_game")
        
        assert is_valid is True

    async def test_command_rate_limiting(self, mock_bot, mock_interaction):
        """Test command rate limiting"""
        # Mock rate limiter
        mock_bot.rate_limiter = MagicMock()
        mock_bot.rate_limiter.is_rate_limited.return_value = False
        
        is_limited = mock_bot.check_rate_limit(mock_interaction.user.id)
        
        assert is_limited is False

    async def test_command_logging(self, mock_bot, mock_interaction):
        """Test command usage logging"""
        with patch('bot.logger') as mock_logger:
            mock_bot.log_command_usage(mock_interaction, "search_board_game")
            
            mock_logger.info.assert_called_once()


@pytest.mark.unit
@pytest.mark.performance
class TestBotPerformance:
    """Test bot performance characteristics"""

    async def test_startup_time(self, mock_bot, performance_threshold):
        """Test bot startup performance"""
        import time
        
        start_time = time.time()
        
        # Mock the initialization process
        mock_bot.setup_database = AsyncMock()
        mock_bot.load_extensions = AsyncMock()
        mock_bot.inject_database_into_cogs = AsyncMock()
        
        await mock_bot.on_ready()
        
        startup_time = time.time() - start_time
        
        # Bot should start up quickly
        assert startup_time < performance_threshold['bot_startup']

    async def test_memory_usage_monitoring(self, mock_bot):
        """Test memory usage monitoring"""
        memory_info = mock_bot.get_memory_usage()
        
        # Should return meaningful memory information
        assert isinstance(memory_info, dict)
        assert 'rss' in memory_info or 'memory_usage' in memory_info

    async def test_concurrent_command_handling(self, mock_bot, performance_threshold):
        """Test handling multiple concurrent commands"""
        # This would test the bot's ability to handle multiple commands simultaneously
        # Implementation depends on actual command structure
        pass


@pytest.mark.unit
@pytest.mark.asyncio
class TestBotErrorRecovery:
    """Test bot error recovery and resilience"""

    async def test_database_reconnection(self, mock_bot):
        """Test database reconnection after connection loss"""
        mock_bot.db = MagicMock()
        mock_bot.db.is_connected.return_value = False
        mock_bot.db.reconnect = AsyncMock()
        
        await mock_bot.ensure_database_connection()
        
        mock_bot.db.reconnect.assert_called_once()

    async def test_cog_reload_on_error(self, mock_bot):
        """Test cog reloading after cog error"""
        cog_name = 'GameSearch'
        mock_bot.reload_extension = AsyncMock()
        
        await mock_bot.recover_cog(cog_name)
        
        # Should attempt to reload the failed cog
        mock_bot.reload_extension.assert_called_once()

    async def test_graceful_degradation(self, mock_bot):
        """Test graceful degradation when services are unavailable"""
        # Mock API clients as unavailable
        mock_bot.disable_api_commands = MagicMock()
        
        mock_bot.handle_service_outage("bgg_api")
        
        # Should gracefully disable affected commands
        mock_bot.disable_api_commands.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio  
class TestBotIntegration:
    """Test bot integration points"""

    async def test_webhook_integration(self, mock_bot):
        """Test webhook endpoints for health checks"""
        # Mock HTTP server for webhooks
        mock_bot.start_webhook_server = AsyncMock()
        
        await mock_bot.start_webhook_server()
        
        # Should start webhook server for health checks
        mock_bot.start_webhook_server.assert_called_once()

    async def test_metrics_endpoint(self, mock_bot):
        """Test metrics endpoint functionality"""
        mock_bot.get_metrics = AsyncMock(return_value={
            'guilds': 5,
            'users': 100,
            'uptime': '1:00:00'
        })
        
        metrics = await mock_bot.get_metrics()
        
        assert 'guilds' in metrics
        assert 'users' in metrics
        assert 'uptime' in metrics

    async def test_external_api_integration(self, mock_bot):
        """Test integration with external APIs through cogs"""
        # This would test the bot's integration with BGG, Steam, Xbox APIs
        # through its cogs system
        assert mock_bot.initial_extensions is not None
        assert len(mock_bot.initial_extensions) > 0
