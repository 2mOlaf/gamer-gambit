import aiosqlite
import asyncio
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
import time
import os

logger = logging.getLogger(__name__)

class Database:
    """Optimized database manager for Kallax bot with connection pooling and lazy loading"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.connection: Optional[aiosqlite.Connection] = None
        self._initialized = False
        self._initialization_lock = asyncio.Lock()
        self._connection_lock = asyncio.Lock()
        self._last_health_check = 0
        self._health_check_interval = 300  # 5 minutes
        self._table_cache = set()  # Cache which tables exist
        
    async def initialize(self):
        """Initialize database and create tables with lazy loading"""
        async with self._initialization_lock:
            if self._initialized:
                return
                
            # Ensure data directory exists
            db_dir = Path(self.db_path).parent
            db_dir.mkdir(parents=True, exist_ok=True)
            
            # Check if database file exists to skip table creation if possible
            db_exists = Path(self.db_path).exists()
            
            # Configure connection with optimizations
            self.connection = await aiosqlite.connect(
                self.db_path,
                timeout=30.0,
                isolation_level=None  # Autocommit mode for better performance
            )
            
            # Optimize SQLite settings
            await self.connection.execute("PRAGMA journal_mode=WAL")
            await self.connection.execute("PRAGMA synchronous=NORMAL") 
            await self.connection.execute("PRAGMA cache_size=10000")
            await self.connection.execute("PRAGMA temp_store=memory")
            await self.connection.execute("PRAGMA mmap_size=268435456")  # 256MB
            
            if not db_exists:
                await self._create_tables()
                logger.info(f"Database created and initialized at {self.db_path}")
            else:
                await self._validate_schema()
                logger.info(f"Database connected at {self.db_path}")
                
            self._initialized = True
            
    async def _validate_schema(self):
        """Validate existing database schema"""
        try:
            # Quick schema validation - just check if key tables exist
            cursor = await self.connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name IN (?, ?, ?, ?)",
                ('user_profiles', 'game_cache', 'game_plays', 'server_settings')
            )
            existing_tables = {row[0] for row in await cursor.fetchall()}
            
            required_tables = {'user_profiles', 'game_cache', 'game_plays', 'server_settings'}
            missing_tables = required_tables - existing_tables
            
            if missing_tables:
                logger.warning(f"Missing tables: {missing_tables}. Creating missing tables.")
                await self._create_missing_tables(missing_tables)
            else:
                self._table_cache = existing_tables
                
        except Exception as e:
            logger.warning(f"Schema validation failed, recreating tables: {e}")
            await self._create_tables()
            
    async def _create_missing_tables(self, missing_tables: set):
        """Create only missing tables instead of all tables"""
        table_definitions = {
            'user_profiles': """
                CREATE TABLE IF NOT EXISTS user_profiles (
                    discord_id INTEGER PRIMARY KEY,
                    bgg_username TEXT,
                    steam_id TEXT,
                    xbox_gamertag TEXT,
                    weekly_stats_enabled BOOLEAN DEFAULT FALSE,
                    weekly_stats_channel_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_user_profiles_bgg_username ON user_profiles(bgg_username);
            """,
            'game_cache': """
                CREATE TABLE IF NOT EXISTS game_cache (
                    bgg_id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    year_published INTEGER,
                    image_url TEXT,
                    thumbnail_url TEXT,
                    description TEXT,
                    min_players INTEGER,
                    max_players INTEGER,
                    playing_time INTEGER,
                    min_playtime INTEGER,
                    max_playtime INTEGER,
                    min_age INTEGER,
                    rating REAL,
                    rating_count INTEGER,
                    weight REAL,
                    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """,
            'game_plays': """
                CREATE TABLE IF NOT EXISTS game_plays (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    discord_id INTEGER NOT NULL,
                    bgg_id INTEGER,
                    game_name TEXT NOT NULL,
                    play_date DATE NOT NULL,
                    duration_minutes INTEGER,
                    player_count INTEGER,
                    players TEXT,
                    scores TEXT,
                    comments TEXT,
                    location TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (discord_id) REFERENCES user_profiles(discord_id)
                );
                CREATE INDEX IF NOT EXISTS idx_game_plays_discord_id ON game_plays(discord_id);
                CREATE INDEX IF NOT EXISTS idx_game_plays_date ON game_plays(play_date);
            """,
            'server_settings': """
                CREATE TABLE IF NOT EXISTS server_settings (
                    guild_id INTEGER PRIMARY KEY,
                    weekly_stats_channel_id INTEGER,
                    command_prefix TEXT DEFAULT '!',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """
        }
        
        for table_name in missing_tables:
            if table_name in table_definitions:
                await self.connection.executescript(table_definitions[table_name])
                logger.info(f"Created missing table: {table_name}")
                
        await self.connection.commit()
        
    async def get_connection(self):
        """Get database connection with lazy initialization"""
        if not self._initialized:
            await self.initialize()
            
        # Health check connection - DISABLED due to hanging issue
        # current_time = time.time()
        # if current_time - self._last_health_check > self._health_check_interval:
            # try:
                # await self.connection.execute("SELECT 1")
                # self._last_health_check = current_time
            # except Exception as e:
                # logger.warning(f"Database health check failed, reconnecting: {e}")
                # await self._reconnect()
                
        return self.connection
        
    async def _reconnect(self):
        """Reconnect to database"""
        async with self._connection_lock:
            # try:
                if self.connection:
                    await self.connection.close()
            except:
                pass
                
            self.connection = await aiosqlite.connect(
                self.db_path,
                timeout=30.0,
                isolation_level=None
            )
            
            # Reapply optimizations
            await self.connection.execute("PRAGMA journal_mode=WAL")
            await self.connection.execute("PRAGMA synchronous=NORMAL")
            await self.connection.execute("PRAGMA cache_size=10000")
            await self.connection.execute("PRAGMA temp_store=memory")
            await self.connection.execute("PRAGMA mmap_size=268435456")
            
            logger.info("Database reconnected successfully")
        
    async def _create_tables(self):
        """Create all necessary tables"""
        await self.connection.executescript("""
            -- User profiles table
            CREATE TABLE IF NOT EXISTS user_profiles (
                discord_id INTEGER PRIMARY KEY,
                bgg_username TEXT,
                steam_id TEXT,
                xbox_gamertag TEXT,
                weekly_stats_enabled BOOLEAN DEFAULT FALSE,
                weekly_stats_channel_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Game cache table for BGG data
            CREATE TABLE IF NOT EXISTS game_cache (
                bgg_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                year_published INTEGER,
                image_url TEXT,
                thumbnail_url TEXT,
                description TEXT,
                min_players INTEGER,
                max_players INTEGER,
                playing_time INTEGER,
                min_playtime INTEGER,
                max_playtime INTEGER,
                min_age INTEGER,
                rating REAL,
                rating_count INTEGER,
                weight REAL,
                cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Game plays tracking
            CREATE TABLE IF NOT EXISTS game_plays (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                discord_id INTEGER NOT NULL,
                bgg_id INTEGER,
                game_name TEXT NOT NULL,
                play_date DATE NOT NULL,
                duration_minutes INTEGER,
                player_count INTEGER,
                players TEXT, -- JSON array of player names
                scores TEXT, -- JSON object of player scores
                comments TEXT,
                location TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (discord_id) REFERENCES user_profiles(discord_id)
            );
            
            -- Server settings
            CREATE TABLE IF NOT EXISTS server_settings (
                guild_id INTEGER PRIMARY KEY,
                weekly_stats_channel_id INTEGER,
                command_prefix TEXT DEFAULT '!',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Game collections from BGG
            CREATE TABLE IF NOT EXISTS game_collections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                discord_id INTEGER NOT NULL,
                bgg_id INTEGER NOT NULL,
                collection_type TEXT NOT NULL, -- 'own', 'want', 'wishlist', etc.
                rating REAL,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (discord_id) REFERENCES user_profiles(discord_id),
                UNIQUE(discord_id, bgg_id, collection_type)
            );
            
            -- Create indexes for better performance
            CREATE INDEX IF NOT EXISTS idx_user_profiles_bgg_username ON user_profiles(bgg_username);
            CREATE INDEX IF NOT EXISTS idx_game_plays_discord_id ON game_plays(discord_id);
            CREATE INDEX IF NOT EXISTS idx_game_plays_date ON game_plays(play_date);
            CREATE INDEX IF NOT EXISTS idx_game_collections_user ON game_collections(discord_id);
        """)
        await self.connection.commit()
        
    async def close(self):
        """Close database connection"""
        if self.connection:
            await self.connection.close()
            
    # User Profile Methods
    async def get_user_profile(self, discord_id: int) -> Optional[Dict[str, Any]]:
        """Get user profile by Discord ID"""
        logger.info(f"Looking up profile for discord_id: {discord_id}")
        conn = await self.get_connection()
        cursor = await conn.execute(
            "SELECT * FROM user_profiles WHERE discord_id = ?", 
            (discord_id,)
        )
        row = await cursor.fetchone()
        if row:
            columns = [description[0] for description in cursor.description]
            profile = dict(zip(columns, row))
            logger.info(f"Found profile: {profile}")
            return profile
        logger.info(f"No profile found for discord_id: {discord_id}")
        return None
        
    async def create_user_profile(self, discord_id: int, **kwargs) -> bool:
        """Create or update user profile"""
        try:
            conn = await self.get_connection()
            await conn.execute("""
                INSERT OR REPLACE INTO user_profiles 
                (discord_id, bgg_username, steam_id, xbox_gamertag, weekly_stats_enabled, weekly_stats_channel_id, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                discord_id,
                kwargs.get('bgg_username'),
                kwargs.get('steam_id'),
                kwargs.get('xbox_gamertag'),
                kwargs.get('weekly_stats_enabled', False),
                kwargs.get('weekly_stats_channel_id')
            ))
            return True
        except Exception as e:
            logger.error(f"Error creating user profile: {e}")
            return False
            
    async def update_user_profile(self, discord_id: int, **kwargs) -> bool:
        """Update specific fields in user profile"""
        try:
            updates = []
            values = []
            
            for field in ['bgg_username', 'steam_id', 'xbox_gamertag', 'weekly_stats_enabled', 'weekly_stats_channel_id']:
                if field in kwargs:
                    updates.append(f"{field} = ?")
                    values.append(kwargs[field])
                    
            if not updates:
                return True
                
            updates.append("updated_at = CURRENT_TIMESTAMP")
            values.append(discord_id)
            
            query = f"UPDATE user_profiles SET {', '.join(updates)} WHERE discord_id = ?"
            cursor = await self.connection.execute(query, values)
            await self.connection.commit()
            
            # Check if any rows were actually updated
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error updating user profile: {e}")
            return False
    
    # Game Cache Methods
    async def cache_game(self, game_data: Dict[str, Any]) -> bool:
        """Cache game data from BGG"""
        try:
            await self.connection.execute("""
                INSERT OR REPLACE INTO game_cache 
                (bgg_id, name, year_published, image_url, thumbnail_url, description, 
                 min_players, max_players, playing_time, min_playtime, max_playtime, 
                 min_age, rating, rating_count, weight, cached_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                game_data.get('bgg_id'),
                game_data.get('name'),
                game_data.get('year_published'),
                game_data.get('image_url'),
                game_data.get('thumbnail_url'),
                game_data.get('description'),
                game_data.get('min_players'),
                game_data.get('max_players'),
                game_data.get('playing_time'),
                game_data.get('min_playtime'),
                game_data.get('max_playtime'),
                game_data.get('min_age'),
                game_data.get('rating'),
                game_data.get('rating_count'),
                game_data.get('weight')
            ))
            await self.connection.commit()
            return True
        except Exception as e:
            logger.error(f"Error caching game: {e}")
            return False
            
    async def get_cached_game(self, bgg_id: int) -> Optional[Dict[str, Any]]:
        """Get cached game data"""
        cursor = await self.connection.execute(
            "SELECT * FROM game_cache WHERE bgg_id = ?", 
            (bgg_id,)
        )
        row = await cursor.fetchone()
        if row:
            columns = [description[0] for description in cursor.description]
            return dict(zip(columns, row))
        return None
    
    # Server Settings Methods
    async def get_server_settings(self, guild_id: int) -> Optional[Dict[str, Any]]:
        """Get server settings"""
        cursor = await self.connection.execute(
            "SELECT * FROM server_settings WHERE guild_id = ?", 
            (guild_id,)
        )
        row = await cursor.fetchone()
        if row:
            columns = [description[0] for description in cursor.description]
            return dict(zip(columns, row))
        return None
        
    async def update_server_settings(self, guild_id: int, **kwargs) -> bool:
        """Update server settings"""
        try:
            await self.connection.execute("""
                INSERT OR REPLACE INTO server_settings 
                (guild_id, weekly_stats_channel_id, command_prefix, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                guild_id,
                kwargs.get('weekly_stats_channel_id'),
                kwargs.get('command_prefix', '!')
            ))
            await self.connection.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating server settings: {e}")
            return False
