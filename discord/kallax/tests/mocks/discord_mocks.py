"""
Comprehensive Discord mocks for Kallax bot testing.
These mocks simulate Discord.py objects without requiring Discord API connections.
"""

import asyncio
from typing import Dict, Any, Optional, List, Union
from unittest.mock import AsyncMock, MagicMock
import time


class MockDiscordUser:
    """Mock Discord User object"""
    
    def __init__(self, user_id: int, username: str, display_name: str = None):
        self.id = user_id
        self.name = username
        self.display_name = display_name or username
        self.discriminator = "0001"
        self.avatar = None
        self.bot = False
        self.system = False
        self.created_at = None
        self.display_avatar = MockDisplayAvatar()
        
        # Mock DM sending
        self.send = AsyncMock()
        
    def __str__(self):
        return f"{self.name}#{self.discriminator}"
    
    def mention(self):
        return f"<@{self.id}>"


class MockDisplayAvatar:
    """Mock Discord avatar object"""
    
    def __init__(self):
        self.url = "https://cdn.discordapp.com/avatars/123456789/mock_avatar.png"


class MockDiscordMember(MockDiscordUser):
    """Mock Discord Member object (extends User)"""
    
    def __init__(self, user_id: int, username: str, display_name: str = None):
        super().__init__(user_id, username, display_name)
        self.guild = None
        self.joined_at = None
        self.premium_since = None
        self.roles = []
        self.activities = []
        self.status = "online"
        self.nick = None


class MockDiscordGuild:
    """Mock Discord Guild (server) object"""
    
    def __init__(self, guild_id: int, name: str):
        self.id = guild_id
        self.name = name
        self.description = None
        self.icon = None
        self.owner_id = 123456789
        self.members = []
        self.channels = []
        self.roles = []
        self.created_at = None


class MockDiscordChannel:
    """Mock Discord Channel object"""
    
    def __init__(self, channel_id: int, name: str, channel_type="text"):
        self.id = channel_id
        self.name = name
        self.type = channel_type
        self.guild = None
        self.position = 0
        self.created_at = None
        
        # Mock message sending
        self.send = AsyncMock()
        self.edit = AsyncMock()


class MockDiscordInteractionResponse:
    """Mock Discord Interaction Response object"""
    
    def __init__(self):
        self.deferred = False
        self.responded = False
        
        # Mock response methods
        self.defer = AsyncMock(side_effect=self._defer)
        self.send_message = AsyncMock(side_effect=self._send_message)
        
    async def _defer(self, ephemeral=False):
        """Mock deferring response"""
        self.deferred = True
        
    async def _send_message(self, content=None, embed=None, ephemeral=False):
        """Mock sending response message"""
        self.responded = True
        return MockDiscordMessage(content=content, embed=embed)


class MockDiscordFollowup:
    """Mock Discord Interaction Followup object"""
    
    def __init__(self):
        self.send = AsyncMock(return_value=MockDiscordMessage())
        self.edit_message = AsyncMock()
        self.delete_message = AsyncMock()


class MockDiscordInteraction:
    """Mock Discord Interaction object"""
    
    def __init__(self, user: MockDiscordUser, command_name: str = "test", guild: MockDiscordGuild = None):
        self.user = user
        self.command = MagicMock()
        self.command.name = command_name
        self.guild = guild
        self.guild_id = guild.id if guild else None
        self.channel = MockDiscordChannel(987654321, "test-channel")
        self.channel_id = self.channel.id
        self.created_at = time.time()
        self.token = "mock_interaction_token"
        self.id = 555444333
        self.application_id = 777888999
        self.type = 2  # APPLICATION_COMMAND
        
        # Mock response and followup
        self.response = MockDiscordInteractionResponse()
        self.followup = MockDiscordFollowup()
        
        # Mock other methods
        self.is_expired = MagicMock(return_value=False)


class MockDiscordMessage:
    """Mock Discord Message object"""
    
    def __init__(self, content: str = None, embed=None, author: MockDiscordUser = None):
        self.id = 111222333
        self.content = content or ""
        self.embeds = [embed] if embed else []
        self.author = author or MockDiscordUser(123456789, "MockUser")
        self.channel = MockDiscordChannel(987654321, "test-channel")
        self.guild = None
        self.created_at = time.time()
        self.reactions = []
        
        # Mock message methods
        self.edit = AsyncMock()
        self.delete = AsyncMock()
        self.add_reaction = AsyncMock()
        self.remove_reaction = AsyncMock()
        self.clear_reactions = AsyncMock()
        self.pin = AsyncMock()
        self.unpin = AsyncMock()


class MockDiscordEmbed:
    """Mock Discord Embed object"""
    
    def __init__(self, title: str = None, description: str = None, color=None):
        self.title = title
        self.description = description
        self.color = color or 0x0099ff
        self.fields = []
        self.footer = {}
        self.author = {}
        self.thumbnail = {}
        self.image = {}
        self.timestamp = None
        
    def add_field(self, name: str, value: str, inline: bool = True):
        """Add field to embed"""
        self.fields.append({
            'name': name,
            'value': value,
            'inline': inline
        })
        return self
        
    def set_footer(self, text: str, icon_url: str = None):
        """Set embed footer"""
        self.footer = {'text': text, 'icon_url': icon_url}
        return self
        
    def set_author(self, name: str, icon_url: str = None, url: str = None):
        """Set embed author"""
        self.author = {'name': name, 'icon_url': icon_url, 'url': url}
        return self
        
    def set_thumbnail(self, url: str):
        """Set embed thumbnail"""
        self.thumbnail = {'url': url}
        return self
        
    def set_image(self, url: str):
        """Set embed image"""
        self.image = {'url': url}
        return self


class MockDiscordColor:
    """Mock Discord Color utilities"""
    
    @staticmethod
    def blue():
        return 0x0099ff
        
    @staticmethod
    def red():
        return 0xff0000
        
    @staticmethod
    def green():
        return 0x00ff00
        
    @staticmethod
    def orange():
        return 0xff9900
        
    @staticmethod
    def purple():
        return 0x9900ff


class MockKallaxBot:
    """Mock Kallax bot instance"""
    
    def __init__(self):
        self.user = MockDiscordUser(888777666, "KallaxBot", "Kallax")
        self.guilds = []
        self.latency = 0.05
        self.database = None
        self.startup_time = time.time()
        self.synced = True
        self.tree = MockCommandTree()
        self._cogs_loaded = set()
        
        # Mock bot methods
        self.wait_for = AsyncMock()
        self.get_user = MagicMock(return_value=None)
        self.get_guild = MagicMock(return_value=None)
        self.get_channel = MagicMock(return_value=None)
        self.is_ready = MagicMock(return_value=True)
        
        # Cog management
        self.load_extension = AsyncMock()
        self.unload_extension = AsyncMock()
        self.reload_extension = AsyncMock()
        self.get_cog = MagicMock(return_value=None)
        
    async def add_cog(self, cog):
        """Mock adding a cog"""
        cog_name = cog.__class__.__name__.lower()
        if cog_name.endswith('cog'):
            cog_name = cog_name[:-3]
        self._cogs_loaded.add(cog_name)
        return True


class MockCommandTree:
    """Mock Discord command tree"""
    
    def __init__(self):
        self.commands = {}
        
    def get_commands(self):
        """Get registered commands"""
        return list(self.commands.values())
        
    def add_command(self, command):
        """Add command to tree"""
        self.commands[command.name] = command


class MockAppCommand:
    """Mock Discord app command"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.options = []
        self.choices = {}


# Factory functions for creating common mock objects

def create_mock_user(user_id: int = 123456789, username: str = "TestUser") -> MockDiscordUser:
    """Create a mock Discord user"""
    return MockDiscordUser(user_id, username)


def create_mock_member(user_id: int = 123456789, username: str = "TestMember") -> MockDiscordMember:
    """Create a mock Discord member"""
    return MockDiscordMember(user_id, username)


def create_mock_guild(guild_id: int = 555666777, name: str = "Test Guild") -> MockDiscordGuild:
    """Create a mock Discord guild"""
    return MockDiscordGuild(guild_id, name)


def create_mock_interaction(
    user: MockDiscordUser = None,
    command_name: str = "test",
    guild: MockDiscordGuild = None
) -> MockDiscordInteraction:
    """Create a mock Discord interaction"""
    if user is None:
        user = create_mock_user()
    if guild is None and command_name != "dm_command":
        guild = create_mock_guild()
    return MockDiscordInteraction(user, command_name, guild)


def create_mock_bot() -> MockKallaxBot:
    """Create a mock Kallax bot"""
    return MockKallaxBot()


# Mock context managers and utilities

class MockAsyncContext:
    """Mock async context manager"""
    
    def __init__(self, return_value=None):
        self.return_value = return_value
        
    async def __aenter__(self):
        return self.return_value
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return False


# Mock for aiohttp responses in API tests
class MockAiohttpResponse:
    """Mock aiohttp response for API testing"""
    
    def __init__(self, json_data: Dict[str, Any] = None, text_data: str = None, status: int = 200):
        self._json_data = json_data or {}
        self._text_data = text_data or ""
        self.status = status
        self.headers = {}
        
    async def json(self):
        return self._json_data
        
    async def text(self):
        return self._text_data
        
    def raise_for_status(self):
        if self.status >= 400:
            raise Exception(f"HTTP {self.status}")


# Export commonly used mocks
__all__ = [
    'MockDiscordUser',
    'MockDiscordMember', 
    'MockDiscordGuild',
    'MockDiscordChannel',
    'MockDiscordInteraction',
    'MockDiscordMessage',
    'MockDiscordEmbed',
    'MockDiscordColor',
    'MockKallaxBot',
    'MockAsyncContext',
    'MockAiohttpResponse',
    'create_mock_user',
    'create_mock_member',
    'create_mock_guild',
    'create_mock_interaction',
    'create_mock_bot'
]
