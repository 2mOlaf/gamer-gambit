"""
Mock Discord objects for testing without Discord connection.
These mocks simulate Discord.py objects and interactions.
"""

from unittest.mock import AsyncMock, MagicMock
from typing import Optional, Dict, Any, List
import asyncio


class MockDiscordUser:
    """Mock Discord User object"""
    
    def __init__(self, user_id: int = 123456789, display_name: str = "TestUser"):
        self.id = user_id
        self.display_name = display_name
        self.name = display_name
        self.discriminator = "0000"
        self.avatar = None
        self.display_avatar = MockAsset("https://example.com/avatar.png")
        
    def __str__(self):
        return f"{self.name}#{self.discriminator}"


class MockDiscordMember(MockDiscordUser):
    """Mock Discord Member object (extends User)"""
    
    def __init__(self, user_id: int = 123456789, display_name: str = "TestUser", guild_id: int = 987654321):
        super().__init__(user_id, display_name)
        self.guild_id = guild_id
        self.guild = MockDiscordGuild(guild_id)


class MockDiscordGuild:
    """Mock Discord Guild object"""
    
    def __init__(self, guild_id: int = 987654321, name: str = "Test Server"):
        self.id = guild_id
        self.name = name


class MockAsset:
    """Mock Discord Asset (for avatars, etc.)"""
    
    def __init__(self, url: str):
        self.url = url


class MockDiscordInteraction:
    """Mock Discord Interaction object for slash commands"""
    
    def __init__(self, user: MockDiscordUser = None, guild: MockDiscordGuild = None):
        self.user = user or MockDiscordUser()
        self.guild = guild or MockDiscordGuild()
        self.response = MockInteractionResponse()
        self.followup = MockInteractionFollowup()
        
    def __str__(self):
        return f"Interaction by {self.user} in {self.guild.name}"


class MockInteractionResponse:
    """Mock Discord InteractionResponse"""
    
    def __init__(self):
        self.is_done = False
        self.deferred = False
        
    async def defer(self, thinking: bool = False, ephemeral: bool = False):
        """Mock defer response"""
        self.deferred = True
        self.is_done = True
        
    async def send_message(self, content: str = None, embed=None, ephemeral: bool = False):
        """Mock send message response"""
        self.is_done = True
        return MockDiscordMessage(content=content, embed=embed)


class MockInteractionFollowup:
    """Mock Discord InteractionFollowup"""
    
    async def send(self, content: str = None, embed=None, ephemeral: bool = False):
        """Mock followup send"""
        return MockDiscordMessage(content=content, embed=embed)


class MockDiscordMessage:
    """Mock Discord Message object"""
    
    def __init__(self, content: str = None, embed=None, author: MockDiscordUser = None):
        self.content = content or ""
        self.embed = embed
        self.author = author or MockDiscordUser()
        self.embeds = [embed] if embed else []


class MockDiscordEmbed:
    """Mock Discord Embed object"""
    
    def __init__(self, title: str = None, description: str = None, color=None, url: str = None):
        self.title = title
        self.description = description
        self.color = color
        self.url = url
        self.fields = []
        self.footer = None
        self.author = None
        self.thumbnail = None
        self.image = None
        
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
        
    def set_author(self, name: str, url: str = None, icon_url: str = None):
        """Set embed author"""
        self.author = {'name': name, 'url': url, 'icon_url': icon_url}
        return self
        
    def set_thumbnail(self, url: str):
        """Set embed thumbnail"""
        self.thumbnail = {'url': url}
        return self
        
    def set_image(self, url: str):
        """Set embed image"""
        self.image = {'url': url}
        return self


class MockBot:
    """Mock Discord Bot for testing cogs"""
    
    def __init__(self):
        self.database = None  # Will be set by tests
        self.user = MockDiscordUser(999888777, "TestBot")
        self.guilds = [MockDiscordGuild()]
        self.latency = 0.05  # Mock 50ms latency
        self._ready = True
        
    def is_ready(self):
        return self._ready
        
    async def add_cog(self, cog):
        """Mock adding cog to bot"""
        cog.bot = self
        return True


class MockDiscordColor:
    """Mock Discord Color class"""
    
    def __init__(self, value: int):
        self.value = value
        
    @classmethod
    def blue(cls):
        return cls(0x3498db)
        
    @classmethod
    def red(cls):
        return cls(0xe74c3c)
        
    @classmethod
    def green(cls):
        return cls(0x2ecc71)
        
    @classmethod
    def orange(cls):
        return cls(0xf39c12)
        
    @classmethod
    def purple(cls):
        return cls(0x9b59b6)
        
    @classmethod
    def gold(cls):
        return cls(0xf1c40f)
        
    @classmethod
    def light_gray(cls):
        return cls(0x95a5a6)


# Helper function to create mock interactions
def create_mock_interaction(user_id: int = 123456789, display_name: str = "TestUser") -> MockDiscordInteraction:
    """Create a mock Discord interaction for testing"""
    user = MockDiscordUser(user_id, display_name)
    return MockDiscordInteraction(user)


# Helper function to create mock bot with database
def create_mock_bot(database=None) -> MockBot:
    """Create a mock bot with optional database"""
    bot = MockBot()
    if database:
        bot.database = database
    return bot
