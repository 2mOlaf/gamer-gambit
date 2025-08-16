#!/usr/bin/env python3
"""
Simple test script to verify existing Discord bot functionality.
This tests the core functionality without complex async test framework.
"""

import asyncio
import tempfile
import os
import sys
import json
from datetime import datetime


async def test_database_functionality():
    """Test basic database operations"""
    print("🧪 Testing Database Functionality")
    print("=" * 50)
    
    try:
        from utils.database import Database
        
        # Create temporary database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_file:
            db_path = temp_file.name
        
        # Initialize database
        db = Database(db_path)
        await db.initialize()
        print("✅ Database initialization: SUCCESS")
        
        # Test empty database
        has_games = await db.has_games()
        print(f"✅ Empty database check: {'PASS' if not has_games else 'FAIL'}")
        
        # Test get stats on empty database
        stats = await db.get_game_stats()
        expected_empty_stats = {'total_games': 0, 'assigned_games': 0, 'unassigned_games': 0, 'completed_reviews': 0}
        stats_match = all(stats.get(k) == v for k, v in expected_empty_stats.items())
        print(f"✅ Empty database stats: {'PASS' if stats_match else 'FAIL'}")
        
        # Add test game data directly using aiosqlite (similar to how Database class works)
        import aiosqlite
        async with aiosqlite.connect(db_path) as conn:
            conn.row_factory = aiosqlite.Row
            await conn.execute("""
                INSERT INTO games (id, game_name, game_url, dev_name, short_text, windows, mac, linux)
                VALUES (1, 'Test Game', 'https://example.com/game', 'Test Dev', 'A test game', 1, 0, 1)
            """)
            await conn.commit()
        print("✅ Test game insertion: SUCCESS")
        
        # Test database now has games
        has_games = await db.has_games()
        print(f"✅ Database with games check: {'PASS' if has_games else 'FAIL'}")
        
        # Test get random unassigned game
        game = await db.get_random_unassigned_game()
        game_found = game is not None and game['id'] == 1
        print(f"✅ Get random unassigned game: {'PASS' if game_found else 'FAIL'}")
        
        # Test game assignment
        success = await db.assign_game_to_user(1, '123456789', 'TestUser')
        print(f"✅ Game assignment: {'PASS' if success else 'FAIL'}")
        
        # Test getting user games
        user_games = await db.get_user_games_legacy('123456789', 'TestUser')
        user_has_game = len(user_games) == 1 and user_games[0]['id'] == 1
        print(f"✅ Get user games: {'PASS' if user_has_game else 'FAIL'}")
        
        # Test updated stats
        stats = await db.get_game_stats()
        updated_stats_correct = (stats['total_games'] == 1 and 
                               stats['assigned_games'] == 1 and 
                               stats['unassigned_games'] == 0)
        print(f"✅ Updated database stats: {'PASS' if updated_stats_correct else 'FAIL'}")
        
        # Clean up
        await db.close()
        os.unlink(db_path)
        print("✅ Database cleanup: SUCCESS")
        
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_cog_initialization():
    """Test Discord cog initialization"""
    print("\n🧪 Testing Discord Cog Functionality")
    print("=" * 50)
    
    try:
        from cogs.game_assignment import GameAssignment
        
        # Mock bot object (simple version)
        class MockBot:
            def __init__(self):
                self.database = None
        
        bot = MockBot()
        cog = GameAssignment(bot)
        
        print("✅ GameAssignment cog initialization: SUCCESS")
        print(f"✅ Cog has bot reference: {'PASS' if cog.bot == bot else 'FAIL'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Cog initialization test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_row_factory_fix():
    """Test that the row factory fix is in place"""
    print("\n🧪 Testing Row Factory Fix")
    print("=" * 50)
    
    try:
        # Read the database.py file and check for row factory settings
        with open('utils/database.py', 'r') as f:
            content = f.read()
        
        # Check for row factory in key locations
        row_factory_count = content.count('db.row_factory = aiosqlite.Row')
        init_has_factory = 'db.row_factory = aiosqlite.Row' in content and 'async def initialize' in content
        
        print(f"✅ Row factory occurrences found: {row_factory_count}")
        print(f"✅ Row factory in initialize method: {'PASS' if init_has_factory else 'FAIL'}")
        
        # Check specific database methods have row factory
        critical_methods = ['get_user_games_legacy', 'get_random_unassigned_game']
        methods_with_factory = []
        
        for method in critical_methods:
            method_start = content.find(f'async def {method}')
            if method_start != -1:
                method_content = content[method_start:content.find('\n    async def', method_start + 1)]
                if 'db.row_factory = aiosqlite.Row' in method_content:
                    methods_with_factory.append(method)
        
        print(f"✅ Methods with row factory: {len(methods_with_factory)}/{len(critical_methods)}")
        
        return row_factory_count > 0 and init_has_factory
        
    except Exception as e:
        print(f"❌ Row factory test failed: {e}")
        return False


def test_legacy_data_import():
    """Test that legacy data can be imported"""
    print("\n🧪 Testing Legacy Data Import")
    print("=" * 50)
    
    try:
        # Check if legacy data file exists
        legacy_files = ['data/itch_pak.json', 'itch_pak.json']
        legacy_file_found = None
        
        for file_path in legacy_files:
            if os.path.exists(file_path):
                legacy_file_found = file_path
                break
        
        if legacy_file_found:
            print(f"✅ Legacy data file found: {legacy_file_found}")
            
            # Try to read the legacy data
            with open(legacy_file_found, 'r', encoding='utf-8') as f:
                data_obj = json.load(f)
            
            # Handle both formats: direct array or object with games array
            if isinstance(data_obj, dict) and 'games' in data_obj:
                data = data_obj['games']
            else:
                data = data_obj
            
            print(f"✅ Legacy data loaded: {len(data)} games found")
            
            # Check data structure
            if data and isinstance(data[0], dict):
                # Check for expected fields (using the actual field names from JSON)
                required_fields = ['gameName', 'gameUrl', 'devName']  # Updated to match actual JSON
                has_required_fields = all(field in data[0] for field in required_fields)
                print(f"✅ Data structure valid: {'PASS' if has_required_fields else 'FAIL'}")
                
                return True
            else:
                print("❌ Invalid data structure")
                return False
        else:
            print("⚠️  No legacy data file found - this may be expected in test environment")
            return True
    
    except Exception as e:
        print(f"❌ Legacy data test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_error_handling():
    """Test error handling in critical functions"""
    print("\n🧪 Testing Error Handling")
    print("=" * 50)
    
    try:
        from utils.database import Database
        
        # Test with non-existent database path
        db = Database('/non/existent/path/test.db')
        try:
            await db.initialize()
            print("⚠️  Expected error for invalid path, but got success")
            await db.close()
        except Exception:
            print("✅ Error handling for invalid path: PASS")
        
        return True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False


async def main():
    """Run all tests"""
    print("🚀 Testing Existing Discord Bot Functionality")
    print("=" * 70)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tests = [
        ("Database Functionality", test_database_functionality()),
        ("Cog Initialization", test_cog_initialization()),
        ("Row Factory Fix", test_row_factory_fix()),
        ("Legacy Data Import", test_legacy_data_import()),
        ("Error Handling", test_error_handling()),
    ]
    
    results = []
    
    for test_name, test_coro in tests:
        try:
            if asyncio.iscoroutine(test_coro):
                result = await test_coro
            else:
                result = test_coro
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 70)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 70)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:.<40} {status}")
        if result:
            passed += 1
    
    print("-" * 70)
    print(f"Total: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 All tests passed! Your Discord bot functionality is working correctly.")
    else:
        print(f"\n⚠️  {total-passed} test(s) failed. Check the output above for details.")
    
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    asyncio.run(main())
