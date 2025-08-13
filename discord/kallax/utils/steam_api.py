import asyncio
import logging
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import os

import aiohttp

logger = logging.getLogger(__name__)

class SteamApiClient:
    """Steam Web API Client"""
    
    BASE_URL = "https://api.steampowered.com"
    STORE_URL = "https://store.steampowered.com/api"
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("STEAM_API_KEY")
        self.session: Optional[aiohttp.ClientSession] = None
        
        if not self.api_key:
            logger.warning("Steam API key not provided. Some functionality will be limited.")
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
