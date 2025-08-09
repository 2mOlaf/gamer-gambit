import asyncio
import logging
import re
from typing import Dict, List, Optional, Any
from xml.etree import ElementTree as ET

import aiohttp
import xmltodict
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class BGGApiClient:
    """BoardGameGeek XML API Client"""
    
    BASE_URL = "https://boardgamegeek.com/xmlapi2"
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            
    async def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Optional[Dict]:
        """Make a request to BGG API with retries and rate limiting"""
        if not self.session:
            raise RuntimeError("Client must be used as async context manager")
            
        url = f"{self.BASE_URL}/{endpoint}"
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                async with self.session.get(url, params=params) as response:
                    if response.status == 202:
                        # BGG API returns 202 when processing, need to wait and retry
                        logger.info(f"BGG API processing request, waiting {retry_delay}s...")
                        await asyncio.sleep(retry_delay)
                        retry_delay *= 2
                        continue
                        
                    if response.status == 200:
                        content = await response.text()
                        # Parse XML to dict
                        return xmltodict.parse(content)
                        
                    logger.warning(f"BGG API returned status {response.status}")
                    
            except Exception as e:
                logger.error(f"Error making BGG API request: {e}")
                
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
                retry_delay *= 2
                
        return None
    
    async def search_games(self, query: str, exact: bool = False) -> List[Dict[str, Any]]:
        """Search for games by name"""
        params = {
            'query': query,
            'type': 'boardgame',
        }
        if exact:
            params['exact'] = '1'
            
        data = await self._make_request('search', params)
        if not data or 'items' not in data:
            return []
            
        items = data['items']
        if not items or 'item' not in items:
            return []
            
        # Handle single item vs list of items
        game_items = items['item']
        if not isinstance(game_items, list):
            game_items = [game_items]
            
        results = []
        for item in game_items:
            if isinstance(item, dict):
                result = {
                    'bgg_id': int(item.get('@id', 0)),
                    'name': item.get('name', {}).get('@value', 'Unknown'),
                    'year_published': item.get('yearpublished', {}).get('@value'),
                }
                if result['bgg_id']:
                    results.append(result)
                    
        return results
    
    async def get_game_details(self, game_ids: List[int]) -> List[Dict[str, Any]]:
        """Get detailed information for games"""
        if not game_ids:
            return []
            
        # BGG API can handle multiple IDs
        ids_str = ','.join(map(str, game_ids))
        params = {
            'id': ids_str,
            'stats': '1',
        }
        
        data = await self._make_request('thing', params)
        if not data or 'items' not in data:
            return []
            
        items = data['items']
        if not items or 'item' not in items:
            return []
            
        # Handle single item vs list of items
        game_items = items['item']
        if not isinstance(game_items, list):
            game_items = [game_items]
            
        results = []
        for item in game_items:
            if not isinstance(item, dict):
                continue
                
            try:
                game_data = self._parse_game_item(item)
                if game_data:
                    results.append(game_data)
            except Exception as e:
                logger.error(f"Error parsing game item: {e}")
                
        return results
    
    def _parse_game_item(self, item: Dict) -> Optional[Dict[str, Any]]:
        """Parse a single game item from BGG API response"""
        try:
            bgg_id = int(item.get('@id', 0))
            if not bgg_id:
                return None
                
            # Get primary name
            names = item.get('name', [])
            if not isinstance(names, list):
                names = [names]
                
            primary_name = None
            for name in names:
                if isinstance(name, dict) and name.get('@type') == 'primary':
                    primary_name = name.get('@value')
                    break
                    
            if not primary_name and names:
                primary_name = names[0].get('@value') if isinstance(names[0], dict) else str(names[0])
                
            # Get description and clean HTML
            description = item.get('description', '')
            if description:
                description = self._clean_html(description)
                
            # Parse player count
            poll = item.get('poll', [])
            if not isinstance(poll, list):
                poll = [poll]
                
            suggested_players = self._parse_suggested_players(poll)
            
            # Parse statistics
            stats = item.get('statistics', {}).get('ratings', {})
            
            game_data = {
                'bgg_id': bgg_id,
                'name': primary_name or 'Unknown Game',
                'year_published': self._safe_int(item.get('yearpublished', {}).get('@value')),
                'image_url': item.get('image'),
                'thumbnail_url': item.get('thumbnail'),
                'description': description[:1000] if description else None,  # Truncate for storage
                'min_players': self._safe_int(item.get('minplayers', {}).get('@value')),
                'max_players': self._safe_int(item.get('maxplayers', {}).get('@value')),
                'playing_time': self._safe_int(item.get('playingtime', {}).get('@value')),
                'min_playtime': self._safe_int(item.get('minplaytime', {}).get('@value')),
                'max_playtime': self._safe_int(item.get('maxplaytime', {}).get('@value')),
                'min_age': self._safe_int(item.get('minage', {}).get('@value')),
                'rating': self._safe_float(stats.get('average', {}).get('@value')),
                'rating_count': self._safe_int(stats.get('usersrated', {}).get('@value')),
                'weight': self._safe_float(stats.get('averageweight', {}).get('@value')),
                'suggested_players': suggested_players,
            }
            
            return game_data
            
        except Exception as e:
            logger.error(f"Error parsing game item: {e}")
            return None
    
    def _parse_suggested_players(self, polls: List[Dict]) -> Dict[str, str]:
        """Parse suggested player count from polls"""
        suggested = {}
        
        for poll in polls:
            if not isinstance(poll, dict) or poll.get('@name') != 'suggested_numplayers':
                continue
                
            results = poll.get('results', [])
            if not isinstance(results, list):
                results = [results]
                
            for result in results:
                if not isinstance(result, dict):
                    continue
                    
                numplayers = result.get('@numplayers', '')
                if not numplayers:
                    continue
                    
                votes = result.get('result', [])
                if not isinstance(votes, list):
                    votes = [votes]
                    
                best_votes = 0
                recommendation = 'Not Recommended'
                
                for vote in votes:
                    if not isinstance(vote, dict):
                        continue
                        
                    value = vote.get('@value')
                    numvotes = self._safe_int(vote.get('@numvotes', 0))
                    
                    if value == 'Best' and numvotes > best_votes:
                        recommendation = 'Best'
                        best_votes = numvotes
                    elif value == 'Recommended' and recommendation != 'Best':
                        recommendation = 'Recommended'
                        
                suggested[numplayers] = recommendation
                
        return suggested
    
    async def get_user_collection(self, username: str, collection_types: List[str] = None) -> List[Dict[str, Any]]:
        """Get user's game collection"""
        if not collection_types:
            collection_types = ['own', 'wishlist', 'fortrade', 'want']
            
        params = {
            'username': username,
            'stats': '1',
        }
        
        # Add collection type filters
        for ctype in collection_types:
            params[ctype] = '1'
            
        data = await self._make_request('collection', params)
        if not data or 'items' not in data:
            return []
            
        items = data['items']
        if not items or 'item' not in items:
            return []
            
        # Handle single item vs list
        collection_items = items['item']
        if not isinstance(collection_items, list):
            collection_items = [collection_items]
            
        results = []
        for item in collection_items:
            if not isinstance(item, dict):
                continue
                
            try:
                collection_item = {
                    'bgg_id': int(item.get('@objectid', 0)),
                    'name': item.get('name', {}).get('#text', 'Unknown'),
                    'year_published': self._safe_int(item.get('yearpublished')),
                    'thumbnail': item.get('thumbnail'),
                    'own': item.get('status', {}).get('@own') == '1',
                    'wishlist': item.get('status', {}).get('@wishlist') == '1',
                    'fortrade': item.get('status', {}).get('@fortrade') == '1',
                    'want': item.get('status', {}).get('@want') == '1',
                    'rating': self._safe_float(item.get('stats', {}).get('rating', {}).get('@value')),
                }
                
                if collection_item['bgg_id']:
                    results.append(collection_item)
                    
            except Exception as e:
                logger.error(f"Error parsing collection item: {e}")
                
        return results
    
    async def get_user_plays(self, username: str, game_id: int = None, page: int = 1) -> Dict[str, Any]:
        """Get user's recorded plays"""
        params = {
            'username': username,
            'page': page,
        }
        
        if game_id:
            params['id'] = game_id
            
        data = await self._make_request('plays', params)
        if not data or 'plays' not in data:
            return {'plays': [], 'total': 0}
            
        plays_data = data['plays']
        total = self._safe_int(plays_data.get('@total', 0))
        
        plays = []
        if 'play' in plays_data:
            play_items = plays_data['play']
            if not isinstance(play_items, list):
                play_items = [play_items]
                
            for play in play_items:
                if not isinstance(play, dict):
                    continue
                    
                try:
                    # Parse players
                    players = []
                    if 'players' in play and 'player' in play['players']:
                        player_items = play['players']['player']
                        if not isinstance(player_items, list):
                            player_items = [player_items]
                            
                        for player in player_items:
                            if isinstance(player, dict):
                                players.append({
                                    'name': player.get('@name', 'Unknown'),
                                    'score': player.get('@score'),
                                    'new': player.get('@new') == '1',
                                    'win': player.get('@win') == '1',
                                })
                    
                    play_data = {
                        'play_id': int(play.get('@id', 0)),
                        'date': play.get('@date'),
                        'quantity': self._safe_int(play.get('@quantity', 1)),
                        'length': self._safe_int(play.get('@length', 0)),
                        'incomplete': play.get('@incomplete') == '1',
                        'nowinstats': play.get('@nowinstats') == '1',
                        'location': play.get('@location'),
                        'game_id': int(play.get('item', {}).get('@objectid', 0)),
                        'game_name': play.get('item', {}).get('@name', 'Unknown'),
                        'players': players,
                        'comments': play.get('comments'),
                    }
                    
                    plays.append(play_data)
                    
                except Exception as e:
                    logger.error(f"Error parsing play: {e}")
                    
        return {
            'plays': plays,
            'total': total,
            'page': page,
        }
    
    @staticmethod
    def _clean_html(html_content: str) -> str:
        """Clean HTML content and return plain text"""
        if not html_content:
            return ""
            
        # Use BeautifulSoup to clean HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        text = soup.get_text()
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    @staticmethod
    def _safe_int(value) -> Optional[int]:
        """Safely convert value to int"""
        if value is None or value == '':
            return None
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return None
    
    @staticmethod
    def _safe_float(value) -> Optional[float]:
        """Safely convert value to float"""
        if value is None or value == '':
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
