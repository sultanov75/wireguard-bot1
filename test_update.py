#!/usr/bin/env python3
"""
Test script to verify the bot protection update
"""

import sys
import os
from pathlib import Path

def test_file_exists(file_path, description):
    """Test if file exists"""
    if Path(file_path).exists():
        print(f"✅ {description}: {file_path}")
        return True
    else:
        print(f"❌ {description}: {file_path} - NOT FOUND")
        return False

def test_file_contains(file_path, search_string, description):
    """Test if file contains specific string"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            if search_string in content:
                print(f"✅ {description}")
                return True
            else:
                print(f"❌ {description} - NOT FOUND")
                return False
    except FileNotFoundError:
        print(f"❌ {description} - FILE NOT FOUND: {file_path}")
        return False

def main():
    print("🧪 Testing WireGuard Bot Protection Update")
    print("=" * 50)
    
    all_tests_passed = True
    
    # Test 1: Check if update scripts exist
    print("\n📁 Testing update scripts:")
    tests = [
        ("install_bot_protection.sh", "Main installer script"),
        ("update_bot.py", "Code update script"),
        ("apply_updates.py", "Database migration script"),
        ("UPDATE_INSTRUCTIONS.md", "Installation instructions")
    ]
    
    for file_path, description in tests:
        if not test_file_exists(file_path, description):
            all_tests_passed = False
    
    # Test 2: Check if original files exist
    print("\n📂 Testing original bot files:")
    original_files = [
        ("app.py", "Main bot application"),
        ("handlers/admin.py", "Admin handlers"),
        ("handlers/user.py", "User handlers"),
        ("utils/watchdog.py", "Watchdog service"),
        ("database/selector.py", "Database selectors"),
        ("database/update.py", "Database updates"),
        ("utils/vpn_cfg_work.py", "VPN configuration")
    ]
    
    for file_path, description in original_files:
        if not test_file_exists(file_path, description):
            all_tests_passed = False
    
    # Test 3: Check if we can import required modules
    print("\n🐍 Testing Python imports:")
    try:
        import psycopg2
        print("✅ psycopg2 available")
    except ImportError:
        print("❌ psycopg2 not available - install with: pip install psycopg2-binary")
        all_tests_passed = False
    
    try:
        import aiofiles
        print("✅ aiofiles available")
    except ImportError:
        print("❌ aiofiles not available - install with: pip install aiofiles")
        all_tests_passed = False
    
    # Test 4: Check if config exists
    print("\n⚙️ Testing configuration:")
    if test_file_exists(".env", "Environment configuration"):
        if test_file_exists("data/config.py", "Config module"):
            try:
                sys.path.append('.')
                from data.config import Config
                config = Config()
                print("✅ Configuration loaded successfully")
            except Exception as e:
                print(f"❌ Configuration error: {e}")
                all_tests_passed = False
    else:
        all_tests_passed = False
    
    # Test 5: Simulate update process (dry run)
    print("\n🔄 Testing update process (dry run):")
    
    # Check if update_bot.py can be executed
    try:
        import subprocess
        result = subprocess.run([sys.executable, "update_bot.py", "--help"], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0 or "usage" in result.stdout.lower() or "help" in result.stdout.lower():
            print("✅ Update script is executable")
        else:
            print("⚠️ Update script may have issues")
    except Exception as e:
        print(f"⚠️ Could not test update script: {e}")
    
    # Final result
    print("\n" + "=" * 50)
    if all_tests_passed:
        print("🎉 ALL TESTS PASSED!")
        print("\n✅ Your bot is ready for the protection update!")
        print("\nTo install the update, run:")
        print("  ./install_bot_protection.sh")
        print("\nOr follow the manual instructions in UPDATE_INSTRUCTIONS.md")
    else:
        print("❌ SOME TESTS FAILED!")
        print("\n⚠️ Please fix the issues above before running the update.")
        print("\nCommon fixes:")
        print("  • Install missing dependencies: pip install psycopg2-binary aiofiles")
        print("  • Check your .env file configuration")
        print("  • Make sure you're in the bot directory")
    
    return all_tests_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)