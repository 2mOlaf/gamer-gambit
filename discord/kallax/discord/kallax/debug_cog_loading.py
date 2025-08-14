#!/usr/bin/env python3
"""
Debug script to test cog loading and identify import issues
"""
import sys
import os
import traceback
from pathlib import Path

# Add current directory to path
sys.path.insert(0, '.')

def test_cog_import(cog_name):
    """Test importing a specific cog and print detailed error info"""
    print(f"\n=== Testing {cog_name} ===")
    
    try:
        # Test basic file existence
        cog_file = Path(f'cogs/{cog_name}.py')
        if not cog_file.exists():
            print(f"❌ File does not exist: {cog_file}")
            return False
        else:
            print(f"✓ File exists: {cog_file}")
        
        # Test basic import
        print(f"Testing import of cogs.{cog_name}...")
        module = __import__(f'cogs.{cog_name}', fromlist=[''])
        print(f"✓ Basic import successful")
        
        # Test if it has the expected setup function
        if hasattr(module, 'setup'):
            print(f"✓ setup() function found")
        else:
            print(f"❌ setup() function not found")
            
        # Test if it has the expected cog class
        cog_class_name = ''.join(word.capitalize() for word in cog_name.split('_')) + 'Cog'
        if hasattr(module, cog_class_name):
            print(f"✓ Cog class {cog_class_name} found")
        else:
            print(f"❌ Expected cog class {cog_class_name} not found")
            # List available classes
            classes = [name for name in dir(module) if name.endswith('Cog')]
            if classes:
                print(f"   Available cog classes: {classes}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("Full traceback:")
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        print("Full traceback:")
        traceback.print_exc()
        return False

def test_utils_imports():
    """Test utility module imports"""
    print("\n=== Testing Utility Imports ===")
    
    utils = [
        'utils.database',
        'utils.bgg_api', 
        'utils.steam_api',
        'utils.xbox_api'
    ]
    
    for util in utils:
        try:
            __import__(util)
            print(f"✓ {util}")
        except Exception as e:
            print(f"❌ {util}: {e}")

def main():
    print("Kallax Bot Cog Loading Debug Tool")
    print("=================================")
    
    # Print Python environment info
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Python path: {sys.path[:3]}...")  # Show first 3 entries
    
    # Test utility imports first
    test_utils_imports()
    
    # Test each essential cog
    essential_cogs = ['user_profiles', 'game_search']
    
    success_count = 0
    for cog_name in essential_cogs:
        if test_cog_import(cog_name):
            success_count += 1
    
    print(f"\n=== Summary ===")
    print(f"Successfully loaded: {success_count}/{len(essential_cogs)} cogs")
    
    if success_count == len(essential_cogs):
        print("✓ All cogs loaded successfully! The issue might be environment-specific.")
    else:
        print("❌ Some cogs failed to load. Check the errors above.")

if __name__ == "__main__":
    main()
