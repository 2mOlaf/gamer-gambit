"""
Database operations for Jarvfjallet bot.
Handles game data storage, user assignments, and legacy JSON import.
"""

import asyncio
import json
import logging
import sqlite3
from pathlib import Path
from typing import Optional, Dict, List, Any
import aiosqlite
from datetime import datetime

logger = logging.getLogger(__name__)

class Database:
    """Database manager for Jarvfjallet bot"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._initialized = False
        self._connection = None
        
        # Ensure data directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
    async def initialize(self):
        """Initialize the database and create tables"""
        if self._initialized:
            return
            
        try:
            await self._create_tables()
            self._initialized = True
            logger.info(f"Database initialized: {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
            
    async def _create_tables(self):
        """Create the necessary database tables"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            # Games table - stores all game information
            await db.execute("""
                CREATE TABLE IF NOT EXISTS games (
                    id INTEGER PRIMARY KEY,
                    game_url TEXT NOT NULL,
                    thumb_url TEXT,
                    windows BOOLEAN DEFAULT FALSE,
                    mac BOOLEAN DEFAULT FALSE,
                    linux BOOLEAN DEFAULT FALSE,
                    game_name TEXT NOT NULL,
                    game_host TEXT,
                    dev_name TEXT,
                    dev_url TEXT,
                    short_text TEXT,
                    reviewer TEXT,
                    thumbnail TEXT,
                    review_url TEXT,
                    review_date INTEGER,
                    assign_date INTEGER,
                    created_at INTEGER DEFAULT (strftime('%s', 'now')),
                    updated_at INTEGER DEFAULT (strftime('%s', 'now'))
                )
            """)
            
            # User assignments table - tracks user gaming activity
            await db.execute("""
                CREATE TABLE IF NOT EXISTS user_assignments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    username TEXT,
                    game_id INTEGER NOT NULL,
                    assigned_at INTEGER DEFAULT (strftime('%s', 'now')),
                    completed_at INTEGER,
                    review_url TEXT,
                    status TEXT DEFAULT 'assigned',
                    FOREIGN KEY (game_id) REFERENCES games (id)
                )
            """)
            
            # Indexes for better performance
            await db.execute("CREATE INDEX IF NOT EXISTS idx_games_reviewer ON games(reviewer)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_games_status ON games(reviewer, review_date)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_user_assignments_user ON user_assignments(user_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_user_assignments_status ON user_assignments(status)")
            
            await db.commit()
            
    async def has_games(self) -> bool:
        """Check if database has any games"""
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT COUNT(*) FROM games")
            count = await cursor.fetchone()
            return count[0] > 0
            
    async def import_from_json(self, json_file_path: str):
        """Import games from legacy JSON file"""
        await self.initialize()
        
        logger.info(f"Importing data from {json_file_path}")
        
        with open(json_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            
        games = data.get('games', [])
        imported_count = 0
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            for game in games:
                try:
                    # Convert boolean strings to actual booleans
                    windows = game.get('windows', False) == True
                    mac = game.get('mac', False) == True
                    linux = game.get('linux', False) == True
                    
                    # Convert date fields
                    review_date = game.get('reviewdate')
                    assign_date = game.get('assigndate')
                    
                    # Convert empty strings to None for optional fields
                    reviewer = game.get('reviewer', '') or None
                    review_url = game.get('reviewurl', '') or None
                    thumbnail = game.get('thumbnail', '') or None
                    
                    await db.execute("""
                        INSERT OR REPLACE INTO games (
                            id, game_url, thumb_url, windows, mac, linux,
                            game_name, game_host, dev_name, dev_url, short_text,
                            reviewer, thumbnail, review_url, review_date, assign_date
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        game.get('id'),
                        game.get('gameUrl'),
                        game.get('thumbUrl'),
                        windows, mac, linux,
                        game.get('gameName'),
                        game.get('gameHost'),
                        game.get('devName'),
                        game.get('devUrl'),
                        game.get('shortText'),
                        reviewer,
                        thumbnail,
                        review_url,
                        review_date,
                        assign_date
                    ))
                    imported_count += 1
                    
                except Exception as e:
                    logger.warning(f"Failed to import game {game.get('id', 'unknown')}: {e}")
                    
            await db.commit()
            
        logger.info(f"Imported {imported_count} games from JSON file")
        
    async def get_random_unassigned_game(self) -> Optional[Dict[str, Any]]:
        """Get a random game that hasn't been assigned"""
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM games 
                WHERE reviewer IS NULL OR reviewer = ''
                ORDER BY RANDOM() 
                LIMIT 1
            """)
            row = await cursor.fetchone()
            
            if row:
                return dict(row)
            return None
            
    async def assign_game_to_user(self, game_id: int, user_id: str, username: str = None) -> bool:
        """Assign a game to a user"""
        await self.initialize()
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                # Update the games table
                await db.execute("""
                    UPDATE games 
                    SET reviewer = ?, assign_date = ?, updated_at = strftime('%s', 'now')
                    WHERE id = ?
                """, (user_id, int(datetime.now().timestamp() * 1000), game_id))
                
                # Create assignment record
                await db.execute("""
                    INSERT INTO user_assignments (user_id, username, game_id, status)
                    VALUES (?, ?, ?, 'assigned')
                """, (user_id, username, game_id))
                
                await db.commit()
                return True
                
        except Exception as e:
            logger.error(f"Failed to assign game {game_id} to user {user_id}: {e}")
            return False
            
    async def get_user_assignments(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all games assigned to a user"""
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT g.*, ua.assigned_at, ua.completed_at, ua.status
                FROM games g
                JOIN user_assignments ua ON g.id = ua.game_id
                WHERE ua.user_id = ?
                ORDER BY ua.assigned_at DESC
            """, (user_id,))
            
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
            
    async def get_user_games_legacy(self, user_id: str, username: str = None) -> List[Dict[str, Any]]:
        """Get user's games using legacy method (for backward compatibility)"""
        await self.initialize()
        
        conditions = []
        params = []
        
        if user_id:
            conditions.append("reviewer = ?")
            params.append(user_id)
            
        if username:
            if conditions:
                conditions.append("OR reviewer = ?")
            else:
                conditions.append("reviewer = ?")
            params.append(username)
            
        if not conditions:
            return []
            
        where_clause = " WHERE " + " ".join(conditions)
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(f"""
                SELECT * FROM games {where_clause}
                ORDER BY assign_date DESC
            """, params)
            
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
            
    async def update_review_completion(self, game_id: int, review_url: str) -> bool:
        """Mark a game review as completed"""
        await self.initialize()
        
        try:
            review_date = int(datetime.now().timestamp() * 1000)
            
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                # Update games table
                await db.execute("""
                    UPDATE games 
                    SET review_url = ?, review_date = ?, updated_at = strftime('%s', 'now')
                    WHERE id = ?
                """, (review_url, review_date, game_id))
                
                # Update assignment status
                await db.execute("""
                    UPDATE user_assignments 
                    SET completed_at = ?, review_url = ?, status = 'completed'
                    WHERE game_id = ?
                """, (review_date, review_url, game_id))
                
                await db.commit()
                return True
                
        except Exception as e:
            logger.error(f"Failed to update review completion for game {game_id}: {e}")
            return False
            
    async def get_game_stats(self) -> Dict[str, int]:
        """Get statistics about games in the database"""
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            # Total games
            cursor = await db.execute("SELECT COUNT(*) FROM games")
            total_games = (await cursor.fetchone())[0]
            
            # Assigned games (has reviewer)
            cursor = await db.execute("SELECT COUNT(*) FROM games WHERE reviewer IS NOT NULL AND reviewer != ''")
            assigned_games = (await cursor.fetchone())[0]
            
            # Unassigned games
            unassigned_games = total_games - assigned_games
            
            # Completed reviews (has review_date)
            cursor = await db.execute("SELECT COUNT(*) FROM games WHERE review_date IS NOT NULL AND review_date != ''")
            completed_reviews = (await cursor.fetchone())[0]
            
            return {
                'total_games': total_games,
                'assigned_games': assigned_games,
                'unassigned_games': unassigned_games,
                'completed_reviews': completed_reviews
            }
            
    async def get_game_by_id(self, game_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific game by ID"""
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM games WHERE id = ?", (game_id,))
            row = await cursor.fetchone()
            
            if row:
                return dict(row)
            return None
            
    async def close(self):
        """Close database connection"""
        if self._connection:
            await self._connection.close()
            self._connection = None
        self._initialized = False
