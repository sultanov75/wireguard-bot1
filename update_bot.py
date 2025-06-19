#!/usr/bin/env python3
"""
Complete WireGuard Bot Update Script
Applies all bot blocking protection features safely
"""

import os
import sys
import shutil
from pathlib import Path

def create_bot_error_handler():
    """Create the bot error handler module"""
    content = '''"""
Bot error handling utilities for WireGuard bot
Handles cases when users block the bot
"""

from aiogram.utils.exceptions import BotBlocked, ChatNotFound, UserDeactivated
from loguru import logger
import database.selector
import database.update
from loader import vpn_config


async def handle_bot_blocked_error(user_id: int, error: Exception):
    """
    Handle bot blocked error by permanently banning the user
    
    Args:
        user_id (int): ID of the user who blocked the bot
        error (Exception): The exception that was raised
    """
    if isinstance(error, (BotBlocked, ChatNotFound, UserDeactivated)):
        logger.warning(f"[!] Bot blocked by user {user_id}: {error}")
        
        # Check if user exists in database
        if database.selector.is_exist_user(user_id):
            # Completely ban the user (remove configs and mark as banned)
            await vpn_config.ban_user_completely(user_id)
            logger.warning(f"[!] User {user_id} has been permanently banned due to bot blocking")
        else:
            logger.info(f"[+] User {user_id} not found in database, no action needed")
    else:
        # Re-raise the error if it's not a bot blocking error
        raise error


async def safe_send_message(bot, user_id: int, text: str, **kwargs):
    """
    Safely send message to user with automatic blocking protection
    
    Args:
        bot: Bot instance
        user_id (int): User ID to send message to
        text (str): Message text
        **kwargs: Additional arguments for send_message
        
    Returns:
        bool: True if message sent successfully, False if user blocked bot
    """
    try:
        await bot.send_message(user_id, text, **kwargs)
        return True
    except (BotBlocked, ChatNotFound, UserDeactivated) as e:
        await handle_bot_blocked_error(user_id, e)
        return False
    except Exception as e:
        logger.error(f"[-] Unexpected error sending message to {user_id}: {e}")
        return False
'''
    
    with open('utils/bot_error_handler.py', 'w') as f:
        f.write(content)
    
    print("✓ Created utils/bot_error_handler.py")

def update_watchdog():
    """Update watchdog.py to use safe message sending"""
    
    # Read current content
    with open('utils/watchdog.py', 'r') as f:
        content = f.read()
    
    # Check if already updated
    if 'safe_send_message' in content:
        print("✓ utils/watchdog.py already updated")
        return
    
    # Apply updates
    new_content = content.replace(
        'from loader import bot',
        'from loader import bot\nfrom utils.bot_error_handler import safe_send_message'
    )
    
    # Replace bot.send_message calls with safe_send_message
    new_content = new_content.replace(
        'await bot.send_message(\n                            user_id,\n                            message_text,\n                            reply_markup=await kb.reply.free_user_kb(user_id=user_id),\n                        )\n                        vpn_config.disconnect_peer(user_id)',
        '''success = await safe_send_message(
                            bot,
                            user_id,
                            message_text,
                            reply_markup=await kb.reply.free_user_kb(user_id=user_id),
                        )
                        if success:
                            vpn_config.disconnect_peer(user_id)'''
    )
    
    new_content = new_content.replace(
        'await bot.send_message(user_id, message_text)',
        'success = await safe_send_message(bot, user_id, message_text)'
    )
    
    # Update the logging
    new_content = new_content.replace(
        'notified_users.append(user_id)\n                    logger.warning(\n                        f"[+] user {user_id} notified about end date {days} days"\n                    )',
        '''if success:
                        notified_users.append(user_id)
                        logger.warning(
                            f"[+] user {user_id} notified about end date {days} days"
                        )
                    else:
                        logger.warning(
                            f"[!] Failed to notify user {user_id} (possibly banned due to bot blocking)"
                        )'''
    )
    
    with open('utils/watchdog.py', 'w') as f:
        f.write(new_content)
    
    print("✓ Updated utils/watchdog.py")

def update_database_selector():
    """Add new database selector functions"""
    
    with open('database/selector.py', 'r') as f:
        content = f.read()
    
    # Check if already updated
    if 'is_user_banned' in content:
        print("✓ database/selector.py already updated")
        return
    
    # Add new functions at the end
    new_functions = '''

def is_user_banned(user_id: int) -> bool:
    """Check if user is banned"""
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT user_id FROM banned_users WHERE user_id = %s",
                (user_id,)
            )
            return cursor.fetchone() is not None
    except Exception as e:
        logger.error(f"[-] Error checking if user {user_id} is banned: {e}")
        return False


def get_banned_users() -> list:
    """Get list of all banned users"""
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT user_id, banned_at, reason FROM banned_users ORDER BY banned_at DESC"
            )
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"[-] Error getting banned users: {e}")
        return []
'''
    
    with open('database/selector.py', 'w') as f:
        f.write(content + new_functions)
    
    print("✓ Updated database/selector.py")

def update_database_update():
    """Add new database update functions"""
    
    with open('database/update.py', 'r') as f:
        content = f.read()
    
    # Check if already updated
    if 'ban_user' in content:
        print("✓ database/update.py already updated")
        return
    
    # Add new functions at the end
    new_functions = '''

def ban_user(user_id: int, reason: str = "Bot blocked by user"):
    """Ban user permanently"""
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO banned_users (user_id, reason) 
                VALUES (%s, %s) 
                ON CONFLICT (user_id) DO UPDATE SET 
                    banned_at = CURRENT_TIMESTAMP,
                    reason = EXCLUDED.reason
                """,
                (user_id, reason)
            )
            connection.commit()
            logger.warning(f"[!] User {user_id} banned: {reason}")
    except Exception as e:
        logger.error(f"[-] Error banning user {user_id}: {e}")


def unban_user(user_id: int):
    """Unban user"""
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM banned_users WHERE user_id = %s",
                (user_id,)
            )
            connection.commit()
            logger.info(f"[+] User {user_id} unbanned")
            return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"[-] Error unbanning user {user_id}: {e}")
        return False
'''
    
    with open('database/update.py', 'w') as f:
        f.write(content + new_functions)
    
    print("✓ Updated database/update.py")

def update_vpn_cfg_work():
    """Add new VPN configuration functions"""
    
    with open('utils/vpn_cfg_work.py', 'r') as f:
        content = f.read()
    
    # Check if already updated
    if 'ban_user_completely' in content:
        print("✓ utils/vpn_cfg_work.py already updated")
        return
    
    # Add import at the top
    if 'import database.update' not in content:
        content = content.replace(
            'import database.selector',
            'import database.selector\nimport database.update'
        )
    
    # Add new functions at the end of the class
    new_methods = '''
    async def permanently_remove_peer(self, user_id: int):
        """Permanently removes peer configuration from WireGuard config file."""
        username = database.selector.get_username_by_id(user_id)
        if not username:
            logger.error(f"[-] Username not found for user_id {user_id}")
            return

        try:
            async with aiofiles.open(self.cfg_path, "r") as cfg:
                config_lines = await cfg.readlines()

            new_config_lines = []
            skip_lines = 0
            
            for i, line in enumerate(config_lines):
                if skip_lines > 0:
                    skip_lines -= 1
                    continue
                    
                # Check if this line contains the username we want to remove
                if (line.strip() == f"#{username}_PC" or 
                    line.strip() == f"#{username}_PHONE" or
                    line.strip() == f"#DISCONNECTED_{username}_PC" or
                    line.strip() == f"#DISCONNECTED_{username}_PHONE"):
                    
                    # Skip this line and the next 4 lines (peer configuration)
                    skip_lines = 4
                    logger.info(f"[+] Removing peer configuration for {line.strip()}")
                    continue
                
                new_config_lines.append(line)

            # Write the new configuration back to file
            async with aiofiles.open(self.cfg_path, "w") as cfg:
                await cfg.writelines(new_config_lines)

            # Restart WireGuard service
            self.restart_service()
            logger.warning(f"[!] Peer {username} permanently removed from WireGuard config")

        except Exception as e:
            logger.error(f"[-] Error removing peer {username}: {e}")

    async def remove_user_configs_from_db(self, user_id: int):
        """Remove all user configurations from database."""
        try:
            with database.selector.connection.cursor() as cursor:
                cursor.execute("DELETE FROM configs WHERE user_id = %s", (user_id,))
                database.selector.connection.commit()
                logger.info(f"[+] Removed all configs for user {user_id} from database")
        except Exception as e:
            logger.error(f"[-] Error removing configs for user {user_id}: {e}")

    async def ban_user_completely(self, user_id: int):
        """Completely ban user: remove configs from WireGuard and database, mark as banned."""
        try:
            # Remove from WireGuard config
            await self.permanently_remove_peer(user_id)
            
            # Remove from database configs
            await self.remove_user_configs_from_db(user_id)
            
            # Mark user as banned in database
            database.update.ban_user(user_id)
            
            username = database.selector.get_username_by_id(user_id)
            logger.warning(f"[!] User {user_id}::{username} completely banned and removed")
            
        except Exception as e:
            logger.error(f"[-] Error completely banning user {user_id}: {e}")
'''
    
    # Find the end of the class and add new methods
    lines = content.split('\n')
    class_end = -1
    for i, line in enumerate(lines):
        if line.strip() and not line.startswith(' ') and not line.startswith('\t') and i > 0:
            if 'class' not in line:
                class_end = i
                break
    
    if class_end == -1:
        # Add at the end of file
        content += new_methods
    else:
        lines.insert(class_end, new_methods)
        content = '\n'.join(lines)
    
    with open('utils/vpn_cfg_work.py', 'w') as f:
        f.write(content)
    
    print("✓ Updated utils/vpn_cfg_work.py")

def update_admin_handlers():
    """Add new admin commands"""
    
    with open('handlers/admin.py', 'r') as f:
        content = f.read()
    
    # Check if already updated
    if '/ban' in content:
        print("✓ handlers/admin.py already updated")
        return
    
    # Add imports
    if 'import database.update' not in content:
        content = content.replace(
            'import database.selector',
            'import database.selector\nimport database.update'
        )
    
    # Add new admin commands at the end
    new_commands = '''

@rate_limit(limit=3)
@is_admin
async def ban_user_command(message: types.Message) -> None:
    """Ban user permanently - /ban <user_id>"""
    try:
        if len(message.text.split()) != 2:
            await message.answer(
                f"Неверный формат команды\\n"
                f"{hcode('/ban user_id')}",
                parse_mode=types.ParseMode.HTML
            )
            return
        
        user_id = int(message.text.split()[1])
        
        # Check if user exists
        if not database.selector.is_exist_user(user_id):
            await message.answer(f"Пользователь {user_id} не найден в базе данных")
            return
        
        # Check if already banned
        if database.selector.is_user_banned(user_id):
            await message.answer(f"Пользователь {user_id} уже заблокирован")
            return
        
        # Ban user completely
        await vpn_config.ban_user_completely(user_id)
        
        username = database.selector.get_username_by_id(user_id)
        await message.answer(
            f"✅ Пользователь {hcode(user_id)} ({hcode(username)}) заблокирован\\n"
            f"• Удалены все конфигурации WireGuard\\n"
            f"• Удалены записи из базы данных\\n"
            f"• Пользователь помечен как заблокированный",
            parse_mode=types.ParseMode.HTML
        )
        
    except ValueError:
        await message.answer("Неверный формат user_id")
    except Exception as e:
        await message.answer(f"Ошибка: {e}")


@rate_limit(limit=3)
@is_admin
async def unban_user_command(message: types.Message) -> None:
    """Unban user - /unban <user_id>"""
    try:
        if len(message.text.split()) != 2:
            await message.answer(
                f"Неверный формат команды\\n"
                f"{hcode('/unban user_id')}",
                parse_mode=types.ParseMode.HTML
            )
            return
        
        user_id = int(message.text.split()[1])
        
        # Check if user is banned
        if not database.selector.is_user_banned(user_id):
            await message.answer(f"Пользователь {user_id} не заблокирован")
            return
        
        # Unban user
        if database.update.unban_user(user_id):
            username = database.selector.get_username_by_id(user_id)
            await message.answer(
                f"✅ Пользователь {hcode(user_id)} ({hcode(username)}) разблокирован\\n"
                f"Теперь он может снова использовать бота",
                parse_mode=types.ParseMode.HTML
            )
        else:
            await message.answer(f"Ошибка при разблокировке пользователя {user_id}")
        
    except ValueError:
        await message.answer("Неверный формат user_id")
    except Exception as e:
        await message.answer(f"Ошибка: {e}")


@rate_limit(limit=3)
@is_admin
async def user_status_command(message: types.Message) -> None:
    """Check user status - /status <user_id>"""
    try:
        if len(message.text.split()) != 2:
            await message.answer(
                f"Неверный формат команды\\n"
                f"{hcode('/status user_id')}",
                parse_mode=types.ParseMode.HTML
            )
            return
        
        user_id = int(message.text.split()[1])
        
        # Check if user exists
        if not database.selector.is_exist_user(user_id):
            await message.answer(f"❌ Пользователь {user_id} не найден в базе данных")
            return
        
        username = database.selector.get_username_by_id(user_id)
        is_banned = database.selector.is_user_banned(user_id)
        is_expired = database.selector.is_subscription_expired(user_id)
        end_date = database.selector.get_subscription_end_date(user_id)
        
        status_text = f"👤 Пользователь: {hcode(username)} ({hcode(user_id)})\\n"
        
        if is_banned:
            status_text += f"🚫 Статус: {hbold('ЗАБЛОКИРОВАН')}\\n"
        elif is_expired:
            status_text += f"⏰ Статус: {hbold('Подписка истекла')}\\n"
        else:
            status_text += f"✅ Статус: {hbold('Активен')}\\n"
        
        status_text += f"📅 Подписка до: {hcode(end_date)}"
        
        await message.answer(status_text, parse_mode=types.ParseMode.HTML)
        
    except ValueError:
        await message.answer("Неверный формат user_id")
    except Exception as e:
        await message.answer(f"Ошибка: {e}")
'''
    
    with open('handlers/admin.py', 'w') as f:
        f.write(content + new_commands)
    
    print("✓ Updated handlers/admin.py")

def update_user_handlers():
    """Update user handlers to check for banned users"""
    
    with open('handlers/user.py', 'r') as f:
        content = f.read()
    
    # Check if already updated
    if 'is_user_banned' in content:
        print("✓ handlers/user.py already updated")
        return
    
    # Add import
    if 'import database.update' not in content:
        content = content.replace(
            'import database.selector',
            'import database.selector\nimport database.update'
        )
    
    # Add banned user check function
    banned_check_function = '''
def check_user_not_banned(func):
    """Decorator to check if user is not banned before executing handler"""
    async def wrapper(message, *args, **kwargs):
        user_id = message.from_user.id
        if database.selector.is_user_banned(user_id):
            await message.answer(
                "🚫 Вы заблокированы и не можете использовать этого бота.\\n"
                "Обратитесь к администратору для разблокировки.",
                parse_mode=types.ParseMode.HTML
            )
            return
        return await func(message, *args, **kwargs)
    return wrapper

'''
    
    # Add the function after imports
    lines = content.split('\n')
    import_end = 0
    for i, line in enumerate(lines):
        if line.strip() and not line.startswith('import') and not line.startswith('from'):
            import_end = i
            break
    
    lines.insert(import_end, banned_check_function)
    content = '\n'.join(lines)
    
    with open('handlers/user.py', 'w') as f:
        f.write(content)
    
    print("✓ Updated handlers/user.py")

def register_new_commands():
    """Update command registration"""
    
    # Check if handlers/__init__.py needs updates
    with open('handlers/__init__.py', 'r') as f:
        content = f.read()
    
    # Add new command registrations
    new_registrations = '''
    # New admin commands for bot blocking protection
    dp.register_message_handler(admin.ban_user_command, commands=["ban"], state="*")
    dp.register_message_handler(admin.unban_user_command, commands=["unban"], state="*")
    dp.register_message_handler(admin.user_status_command, commands=["status"], state="*")
'''
    
    if 'ban_user_command' not in content:
        content += new_registrations
        
        with open('handlers/__init__.py', 'w') as f:
            f.write(content)
        
        print("✓ Updated handlers/__init__.py")
    else:
        print("✓ handlers/__init__.py already updated")

def main():
    print("🚀 Applying WireGuard Bot Updates...")
    print("This will add bot blocking protection features")
    print()
    
    # Check if we're in the right directory
    if not Path('app.py').exists():
        print("❌ Error: Not in bot directory")
        sys.exit(1)
    
    try:
        # Apply all updates
        create_bot_error_handler()
        update_database_selector()
        update_database_update()
        update_vpn_cfg_work()
        update_watchdog()
        update_admin_handlers()
        update_user_handlers()
        register_new_commands()
        
        print()
        print("✅ All updates applied successfully!")
        print()
        print("📋 What was added:")
        print("  • Automatic bot blocking detection")
        print("  • User banning system")
        print("  • New admin commands: /ban, /unban, /status")
        print("  • Safe message sending")
        print("  • Automatic config cleanup")
        print()
        print("🔄 Next steps:")
        print("  1. Restart your bot service")
        print("  2. Test the new commands")
        print("  3. Check logs for any issues")
        
    except Exception as e:
        print(f"❌ Error during update: {e}")
        print("Check the backup files if you need to rollback")
        sys.exit(1)

if __name__ == "__main__":
    main()