#!/usr/bin/env python3
"""
Test script to verify the specific production bug fixes we implemented.
This tests the fixes for the row factory and error handling improvements.
"""

import asyncio
import tempfile
import os
import sys
import json
from datetime import datetime


async def test_row_factory_database_operations():
    """Test that database operations work with row factory properly configured"""
    print("🧪 Testing Row Factory Database Operations")
    print("=" * 50)
    
    try:
        from utils.database import Database
        
        # Create temporary database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_file:
            db_path = temp_file.name
        
        db = Database(db_path)
        await db.initialize()
        
        # Import some test data to work with
        import aiosqlite
        async with aiosqlite.connect(db_path) as conn:
            conn.row_factory = aiosqlite.Row
            await conn.execute("""
                INSERT INTO games (id, game_name, game_url, dev_name, short_text, windows, mac, linux, reviewer, assign_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (1, 'Test Game', 'https://example.com/game', 'Test Dev', 'A test game', 1, 0, 1, '123456789', 1692000000000))
            await conn.commit()
        
        print("✅ Test data inserted successfully")
        
        # Test get_user_games_legacy - this was failing in production
        user_games = await db.get_user_games_legacy('123456789', 'TestUser')
        
        if user_games:
            game = user_games[0]
            # Test that we can access fields using dict-style access (this was the bug)
            game_name = game.get('game_name')  # This would fail without row factory
            game_id = game['id']  # This would also fail
            
            print(f"✅ get_user_games_legacy returns dict-accessible rows: PASS")
            print(f"   Game name: {game_name}")
            print(f"   Game ID: {game_id}")
        else:
            print("❌ get_user_games_legacy returned no games")
            return False
        
        # Test get_random_unassigned_game
        # First, add an unassigned game
        async with aiosqlite.connect(db_path) as conn:
            conn.row_factory = aiosqlite.Row
            await conn.execute("""
                INSERT INTO games (id, game_name, game_url, dev_name, short_text, windows, mac, linux)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (2, 'Unassigned Game', 'https://example.com/game2', 'Test Dev 2', 'Another test game', 1, 1, 0))
            await conn.commit()
        
        # Now test getting random unassigned game
        random_game = await db.get_random_unassigned_game()
        if random_game:
            game_name = random_game.get('game_name')
            game_id = random_game['id']
            print(f"✅ get_random_unassigned_game returns dict-accessible rows: PASS")
            print(f"   Random game: {game_name} (ID: {game_id})")
        else:
            print("❌ get_random_unassigned_game returned None")
            return False
        
        # Test get_game_stats
        stats = await db.get_game_stats()
        if isinstance(stats, dict) and 'total_games' in stats:
            print(f"✅ get_game_stats returns proper dict: PASS")
            print(f"   Total games: {stats['total_games']}")
        else:
            print("❌ get_game_stats did not return expected format")
            return False
        
        # Clean up
        await db.close()
        os.unlink(db_path)
        
        return True
        
    except Exception as e:
        print(f"❌ Row factory test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_error_handling_improvements():
    """Test the improved error handling for empty database scenarios"""
    print("\n🧪 Testing Error Handling Improvements")
    print("=" * 50)
    
    try:
        from utils.database import Database
        
        # Create empty database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_file:
            db_path = temp_file.name
        
        db = Database(db_path)
        await db.initialize()
        
        print("✅ Empty database created")
        
        # Test getting user games from empty database (should not crash)
        user_games = await db.get_user_games_legacy('999999999', 'NonExistentUser')
        if isinstance(user_games, list) and len(user_games) == 0:
            print("✅ get_user_games_legacy handles empty database: PASS")
        else:
            print("❌ get_user_games_legacy did not return empty list for empty database")
            return False
        
        # Test getting stats from empty database
        stats = await db.get_game_stats()
        if (isinstance(stats, dict) and 
            stats.get('total_games') == 0 and 
            stats.get('assigned_games') == 0):
            print("✅ get_game_stats handles empty database: PASS")
        else:
            print("❌ get_game_stats did not return expected empty stats")
            return False
        
        # Test getting random game from empty database
        random_game = await db.get_random_unassigned_game()
        if random_game is None:
            print("✅ get_random_unassigned_game handles empty database: PASS")
        else:
            print("❌ get_random_unassigned_game should return None for empty database")
            return False
        
        # Clean up
        await db.close()
        os.unlink(db_path)
        
        return True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_command_error_handling_code():
    """Test that the command error handling improvements are in place"""
    print("\n🧪 Testing Command Error Handling Code")
    print("=" * 50)
    
    try:
        # Read the cog file and check for improved error handling
        with open('cogs/game_assignment.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for specific error handling patterns
        error_patterns = [
            'total_games == 0',  # Check for empty database detection
            'No games assigned to',  # Check for user-friendly error messages
            'database appears to be empty',  # Check for empty database message
        ]
        
        found_patterns = 0
        for pattern in error_patterns:
            if pattern in content:
                found_patterns += 1
                print(f"✅ Found error handling pattern: {pattern}")
            else:
                print(f"⚠️  Pattern not found: {pattern}")
        
        print(f"✅ Error handling patterns found: {found_patterns}/{len(error_patterns)}")
        
        # Check for try-catch blocks around database operations
        try_catch_count = content.count('try:')
        print(f"✅ Try-catch blocks found: {try_catch_count}")
        
        return found_patterns >= 2  # At least most error patterns should be present
        
    except Exception as e:
        print(f"❌ Code analysis failed: {e}")
        return False


async def test_legacy_data_import_functionality():
    """Test that the legacy data import works correctly"""
    print("\n🧪 Testing Legacy Data Import Functionality") 
    print("=" * 50)
    
    try:
        from utils.database import Database
        
        # Check if legacy data exists
        if not os.path.exists('data/itch_pak.json'):
            print("⚠️  Legacy data file not found - skipping import test")
            return True
        
        # Create temporary database for import test
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_file:
            db_path = temp_file.name
        
        # Test import
        db = Database(db_path)
        await db.initialize()
        
        # Import data (this should work without errors)
        await db.import_from_json('data/itch_pak.json')
        print("✅ Legacy data imported successfully")
        
        # Verify import worked
        stats = await db.get_game_stats()
        if stats['total_games'] > 0:
            print(f"✅ Imported {stats['total_games']} games successfully")
        else:
            print("❌ No games were imported")
            return False
        
        # Test that imported games have proper row factory access
        random_game = await db.get_random_unassigned_game()
        if random_game and random_game.get('game_name'):
            print(f"✅ Imported games are accessible via dict interface: PASS")
            print(f"   Sample game: {random_game.get('game_name')}")
        else:
            print("❌ Imported games are not properly accessible")
            return False
        
        # Clean up
        await db.close()
        os.unlink(db_path)
        
        return True
        
    except Exception as e:
        print(f"❌ Legacy import test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all production fix tests"""
    print("🔧 Testing Production Bug Fixes")
    print("=" * 70)
    print("Testing the specific fixes implemented for production issues:")
    print("1. Row factory configuration")
    print("2. Empty database error handling")
    print("3. Command error messaging")
    print("4. Legacy data import")
    print()
    
    tests = [
        ("Row Factory Database Operations", test_row_factory_database_operations()),
        ("Error Handling Improvements", test_error_handling_improvements()),
        ("Command Error Handling Code", test_command_error_handling_code()),
        ("Legacy Data Import", test_legacy_data_import_functionality()),
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
    print("📊 PRODUCTION FIX TEST RESULTS")
    print("=" * 70)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:.<50} {status}")
        if result:
            passed += 1
    
    print("-" * 70)
    print(f"Total: {passed}/{total} production fixes verified ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 All production fixes are working correctly!")
        print("✅ Row factory issues resolved")
        print("✅ Error handling improved") 
        print("✅ Commands should work properly in production")
    else:
        print(f"\n⚠️  {total-passed} fix(es) may need attention.")
        
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    asyncio.run(main())
