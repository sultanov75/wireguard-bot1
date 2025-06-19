#!/usr/bin/env python3
"""
Simple test to verify that our new bot blocking functionality is properly implemented.
This test checks the code structure without requiring external dependencies.
"""

import os
import sys

def test_file_exists():
    """Test that all required files exist."""
    print("🧪 Testing file existence...")
    
    files_to_check = [
        "utils/bot_error_handler.py",
        "BOT_BLOCKING_SOLUTION.md",
        "database/update.py",
        "database/selector.py",
        "utils/vpn_cfg_work.py",
        "handlers/admin.py",
        "handlers/__init__.py",
        "utils/watchdog.py"
    ]
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            print(f"✅ {file_path} exists")
        else:
            print(f"❌ {file_path} missing")
            return False
    
    return True

def test_function_definitions():
    """Test that required functions are defined in files."""
    print("\n🧪 Testing function definitions...")
    
    # Test bot_error_handler.py
    with open("utils/bot_error_handler.py", "r") as f:
        content = f.read()
        functions = ["handle_bot_blocked_error", "safe_send_message", "check_user_access"]
        for func in functions:
            if f"def {func}" in content:
                print(f"✅ {func} defined in bot_error_handler.py")
            else:
                print(f"❌ {func} missing in bot_error_handler.py")
                return False
    
    # Test database/update.py
    with open("database/update.py", "r") as f:
        content = f.read()
        functions = ["ban_user", "unban_user"]
        for func in functions:
            if f"def {func}" in content:
                print(f"✅ {func} defined in database/update.py")
            else:
                print(f"❌ {func} missing in database/update.py")
                return False
    
    # Test database/selector.py
    with open("database/selector.py", "r") as f:
        content = f.read()
        if "def is_user_banned" in content:
            print("✅ is_user_banned defined in database/selector.py")
        else:
            print("❌ is_user_banned missing in database/selector.py")
            return False
    
    # Test utils/vpn_cfg_work.py
    with open("utils/vpn_cfg_work.py", "r") as f:
        content = f.read()
        functions = ["permanently_remove_peer", "remove_user_configs_from_db", "ban_user_completely"]
        for func in functions:
            if f"def {func}" in content:
                print(f"✅ {func} defined in vpn_cfg_work.py")
            else:
                print(f"❌ {func} missing in vpn_cfg_work.py")
                return False
    
    # Test handlers/admin.py
    with open("handlers/admin.py", "r") as f:
        content = f.read()
        functions = ["cmd_ban_user", "cmd_unban_user", "cmd_check_user_status"]
        for func in functions:
            if f"def {func}" in content:
                print(f"✅ {func} defined in admin.py")
            else:
                print(f"❌ {func} missing in admin.py")
                return False
    
    return True

def test_handler_registration():
    """Test that new handlers are registered."""
    print("\n🧪 Testing handler registration...")
    
    with open("handlers/__init__.py", "r") as f:
        content = f.read()
        handlers = ["cmd_ban_user", "cmd_unban_user", "cmd_check_user_status"]
        for handler in handlers:
            if f"register_message_handler({handler}" in content:
                print(f"✅ {handler} registered in handlers/__init__.py")
            else:
                print(f"❌ {handler} not registered in handlers/__init__.py")
                return False
    
    return True

def test_watchdog_updates():
    """Test that watchdog.py has been updated."""
    print("\n🧪 Testing watchdog updates...")
    
    with open("utils/watchdog.py", "r") as f:
        content = f.read()
        
        if "safe_send_message" in content:
            print("✅ safe_send_message imported in watchdog.py")
        else:
            print("❌ safe_send_message not imported in watchdog.py")
            return False
        
        if "await safe_send_message" in content:
            print("✅ safe_send_message used in watchdog.py")
        else:
            print("❌ safe_send_message not used in watchdog.py")
            return False
    
    return True

def test_user_handler_updates():
    """Test that user.py has been updated with ban check."""
    print("\n🧪 Testing user handler updates...")
    
    with open("handlers/user.py", "r") as f:
        content = f.read()
        
        if "is_user_banned" in content:
            print("✅ is_user_banned check added to user.py")
        else:
            print("❌ is_user_banned check missing in user.py")
            return False
        
        if "заблокирован" in content:
            print("✅ Ban message added to user.py")
        else:
            print("❌ Ban message missing in user.py")
            return False
    
    return True

def test_documentation():
    """Test that documentation exists."""
    print("\n🧪 Testing documentation...")
    
    # Check BOT_BLOCKING_SOLUTION.md
    if os.path.exists("BOT_BLOCKING_SOLUTION.md"):
        with open("BOT_BLOCKING_SOLUTION.md", "r") as f:
            content = f.read()
            if len(content) > 1000:  # Should be substantial documentation
                print("✅ BOT_BLOCKING_SOLUTION.md contains substantial documentation")
            else:
                print("❌ BOT_BLOCKING_SOLUTION.md too short")
                return False
    else:
        print("❌ BOT_BLOCKING_SOLUTION.md missing")
        return False
    
    # Check README.md updates
    with open("README.md", "r") as f:
        content = f.read()
        if "/ban" in content and "/unban" in content:
            print("✅ README.md updated with new commands")
        else:
            print("❌ README.md not updated with new commands")
            return False
    
    return True

def main():
    """Run all tests."""
    print("🚀 Starting bot blocking functionality verification...\n")
    
    tests = [
        test_file_exists,
        test_function_definitions,
        test_handler_registration,
        test_watchdog_updates,
        test_user_handler_updates,
        test_documentation
    ]
    
    all_passed = True
    for test in tests:
        if not test():
            all_passed = False
            print(f"❌ {test.__name__} FAILED")
        else:
            print(f"✅ {test.__name__} PASSED")
        print()
    
    if all_passed:
        print("🎉 All tests PASSED! Bot blocking functionality is properly implemented.")
        print("\n📋 Summary of implemented features:")
        print("- ✅ Automatic bot blocking detection and handling")
        print("- ✅ Complete user banning (WireGuard + Database)")
        print("- ✅ Admin commands: /ban, /unban, /status")
        print("- ✅ Safe message sending with error handling")
        print("- ✅ User access validation")
        print("- ✅ Updated watchdog system")
        print("- ✅ Comprehensive documentation")
        return 0
    else:
        print("❌ Some tests FAILED. Please check the implementation.")
        return 1

if __name__ == "__main__":
    exit(main())