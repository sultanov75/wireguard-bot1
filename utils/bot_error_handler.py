"""
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
