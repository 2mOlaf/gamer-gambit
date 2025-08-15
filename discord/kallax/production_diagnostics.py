#!/usr/bin/env python3
"""
Simple diagnostic script to check for missing dependencies that could prevent game_search cog from loading
"""

import sys
import os

def check_dependencies():
    """Check if required dependencies are available"""
    print("=== Production Environment Diagnostics ===")
    print(f"Python version: {sys.version}")
    print(f"Current working directory: {os.getcwd()}")
    
    dependencies = [
        'aiohttp',
        'xmltodict', 
        'bs4',  # beautifulsoup4
        'discord',
        'pathlib'
    ]
    
    missing_deps = []
    available_deps = []
    
    for dep in dependencies:
        try:
            if dep == 'bs4':
                from bs4 import BeautifulSoup
                available_deps.append(f"{dep} (BeautifulSoup)")
            elif dep == 'pathlib':
                from pathlib import Path
                available_deps.append(dep)
            elif dep == 'aiohttp':
                import aiohttp
                available_deps.append(f"{dep} v{aiohttp.__version__}")
            elif dep == 'xmltodict':
                import xmltodict
                available_deps.append(dep)
            elif dep == 'discord':
                import discord
                available_deps.append(f"{dep} v{discord.__version__}")
            else:
                __import__(dep)
                available_deps.append(dep)
        except ImportError as e:
            missing_deps.append((dep, str(e)))
    
    print("\n=== Available Dependencies ===")
    for dep in available_deps:
        print(f"✅ {dep}")
    
    print("\n=== Missing Dependencies ===")
    if missing_deps:
        for dep, error in missing_deps:
            print(f"❌ {dep}: {error}")
    else:
        print("✅ All dependencies available")
    
    # Test cog imports specifically
    print("\n=== Testing Cog Imports ===")
    cogs_to_test = ['user_profiles', 'game_search']
    
    for cog_name in cogs_to_test:
        try:
            full_cog_name = f'cogs.{cog_name}'
            print(f"Testing import: {full_cog_name}")
            
            if cog_name == 'user_profiles':
                from cogs.user_profiles import UserProfilesCog
                print(f"✅ {full_cog_name} - imported successfully")
            elif cog_name == 'game_search':
                from cogs.game_search import GameSearchCog
                print(f"✅ {full_cog_name} - imported successfully")
            
        except Exception as e:
            print(f"❌ {full_cog_name} - failed to import: {e}")
            import traceback
            print(f"   Full error: {traceback.format_exc()}")
    
    # Check specific API client imports
    print("\n=== Testing API Client Imports ===")
    api_clients = ['bgg_api', 'steam_api', 'xbox_api']
    
    for client in api_clients:
        try:
            full_client_name = f'utils.{client}'
            print(f"Testing import: {full_client_name}")
            
            if client == 'bgg_api':
                from utils.bgg_api import BGGApiClient
                print(f"✅ {full_client_name} - BGGApiClient imported")
            elif client == 'steam_api':
                from utils.steam_api import SteamApiClient  
                print(f"✅ {full_client_name} - SteamApiClient imported")
            elif client == 'xbox_api':
                from utils.xbox_api import XboxApiClient
                print(f"✅ {full_client_name} - XboxApiClient imported")
                
        except Exception as e:
            print(f"❌ {full_client_name} - failed to import: {e}")
            import traceback
            print(f"   Full error: {traceback.format_exc()}")

if __name__ == "__main__":
    check_dependencies()
