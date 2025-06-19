from aiogram import types
from aiogram.dispatcher import FSMContext
from loader import bot, vpn_config
from loguru import logger

from data import configuration
import database
import keyboards as kb
from middlewares import rate_limit

from pprint import pformat
from datetime import datetime
from aiogram.utils.markdown import hcode, hbold, hpre
from io import BytesIO
from database import selector


def is_admin(func):
    async def wrapped(message: types.Message, state: FSMContext):
        if message.from_user.id in configuration.admins:
            await func(message, state)
        else:
            admins_usernames = [
                selector.get_username_by_id(ADMIN) for ADMIN in configuration.admins
            ]
            if not admins_usernames:
                await message.answer("You don't have permission to use this command.")
                logger.warning(
                    f"Admins usernames not found. Check config.py file. {configuration.admins}"
                )
                return

            usernames_references = "".join(
                [f"@{username} " for username in admins_usernames]
            )
            await message.answer(
                f"You don't have permission to use this command.\n"
                f"Please, contact with admins: {usernames_references}",
                parse_mode=types.ParseMode.HTML,
            )

    return wrapped


@rate_limit(limit=3)
@is_admin
# function for getting info about message in pretty format
async def cmd_info(message: types.Message, state: FSMContext) -> types.Message | str:
    await message.answer(
        f"{hpre(pformat(message.to_python()))}", parse_mode=types.ParseMode.HTML
    )


@rate_limit(limit=3)
@is_admin
async def statistic_endtime(message: types.Message, state: FSMContext):
    args = message.text.split()[1:]
    users = database.selector.get_all_usernames_and_enddate()
    if not users:
        await message.answer(
            f"{hbold('Error: database is empty ')}", parse_mode=types.ParseMode.HTML
        )
        return
    # sort by enddate high to low
    users.sort(key=lambda x: x[1], reverse=True)

    if args:
        users = filter_users_by_status(users, args[0])

    if not users:
        await message.answer(
            f"{hbold('Error: users with this status not found ')}",
            parse_mode=types.ParseMode.HTML,
        )
        return

    pretty_string = "".join(
        [f'{user[0]} - {user[1].strftime("%d-%m-%Y")}\n' for user in users]
    )

    if len(pretty_string) > 4096:
        io_string = BytesIO(pretty_string.encode("utf-8"))
        await message.answer_document(
            types.InputFile(
                io_string,
                filename=f"statistic_endtime_{datetime.now().strftime('%d-%m-%Y')}.txt",
            )
        )

    else:
        await message.answer(
            f"{hcode('username')} - {hbold('enddate')}\n\n{pretty_string}",
            parse_mode=types.ParseMode.HTML,
        )


def filter_users_by_status(users: list, status: str) -> list:
    if status == "active":
        return [user for user in users if user[1] >= datetime.now()]

    elif status in ["inactive", "notactive", "expired"]:
        return [user for user in users if user[1] < datetime.now()]


@rate_limit(limit=3)
@is_admin
async def give_subscription_time(
    message: types.Message, state: FSMContext
) -> types.Message:
    # /give pheezz 30
    # or /give 123456789 30
    if len(message.text.split()) != 3:
        message.answer(
            f"Неверный формат команды\n"
            f"{hcode('/give username days')}\n"
            f"{hcode('/give user_id days')}"
        )
        return

    if message.text.split()[1].isdigit():
        user_id = int(message.text.split()[1])
        days = message.text.split()[2]
    else:
        username, days = message.text.split()[1:]
        user_id = database.selector.get_user_id(username)

    try:
        database.update.update_given_subscription_time(user_id=user_id, days=int(days))
        is_subscription_expired = database.selector.is_subscription_expired(user_id)
        if is_subscription_expired:
            await vpn_config.disconnect_peer(user_id)
            await bot.send_message(
                user_id,
                "Ваша подписка истекла.",
                reply_markup=await kb.free_user_kb(user_id=user_id),
            )
    except Exception as e:
        await message.answer(f"Error: {e.__repr__()}")
    else:
        if not is_subscription_expired:
            await vpn_config.reconnect_payed_user(user_id=user_id)
        await bot.send_message(
            user_id,
            f"Поздравляем! Администратор продлил вашу подписку на {hbold(days)} дней!",
            reply_markup=await kb.payed_user_kb()
            if not is_subscription_expired
            else await kb.free_user_kb(user_id=user_id),
            parse_mode=types.ParseMode.HTML,
        )
        for admin in configuration.admins:
            await bot.send_message(
                chat_id=admin,
                text=f"Пользователю {hcode(user_id)} продлена подписка на {hbold(days)} дней.\n"
                f"Теперь она актуальна до: {hbold(database.selector.get_subscription_end_date(user_id))}",
                parse_mode=types.ParseMode.HTML,
            )


@rate_limit(limit=3)
@is_admin
async def restart_wg_service_admin(message: types.Message, state: FSMContext):
    vpn_config.restart_service()
    await message.answer("Сервис WireGuard перезапущен")


@rate_limit(limit=3)
@is_admin
async def cmd_ban_user(message: types.Message, state: FSMContext):
    """Ban user permanently - /ban <user_id>"""
    try:
        args = message.text.split()
        if len(args) != 2:
            await message.answer("Использование: /ban <user_id>")
            return
        
        user_id = int(args[1])
        
        if not database.selector.is_exist_user(user_id):
            await message.answer(f"Пользователь {user_id} не найден в базе данных")
            return
        
        # Completely ban user
        await vpn_config.ban_user_completely(user_id)
        
        username = database.selector.get_username_by_id(user_id)
        await message.answer(
            f"✅ Пользователь {hcode(user_id)}::{hcode(username)} заблокирован навсегда.\n"
            f"Все конфигурации удалены из WireGuard и базы данных.",
            parse_mode=types.ParseMode.HTML
        )
        
        # Notify other admins
        for admin in configuration.admins:
            if admin != message.from_user.id:
                await bot.send_message(
                    chat_id=admin,
                    text=f"Пользователь {hcode(user_id)}::{hcode(username)} заблокирован администратором {hcode(message.from_user.username)}",
                    parse_mode=types.ParseMode.HTML,
                )
                
    except ValueError:
        await message.answer("Неверный формат user_id")
    except Exception as e:
        logger.error(f"Error banning user: {e}")
        await message.answer(f"Ошибка при блокировке пользователя: {e}")


@rate_limit(limit=3)
@is_admin
async def cmd_unban_user(message: types.Message, state: FSMContext):
    """Unban user - /unban <user_id>"""
    try:
        args = message.text.split()
        if len(args) != 2:
            await message.answer("Использование: /unban <user_id>")
            return
        
        user_id = int(args[1])
        
        if not database.selector.is_exist_user(user_id):
            await message.answer(f"Пользователь {user_id} не найден в базе данных")
            return
        
        if not database.selector.is_user_banned(user_id):
            await message.answer(f"Пользователь {user_id} не заблокирован")
            return
        
        # Unban user
        database.update.unban_user(user_id)
        
        username = database.selector.get_username_by_id(user_id)
        await message.answer(
            f"✅ Пользователь {hcode(user_id)}::{hcode(username)} разблокирован.\n"
            f"Теперь он может снова использовать бота.",
            parse_mode=types.ParseMode.HTML
        )
        
        # Notify other admins
        for admin in configuration.admins:
            if admin != message.from_user.id:
                await bot.send_message(
                    chat_id=admin,
                    text=f"Пользователь {hcode(user_id)}::{hcode(username)} разблокирован администратором {hcode(message.from_user.username)}",
                    parse_mode=types.ParseMode.HTML,
                )
                
    except ValueError:
        await message.answer("Неверный формат user_id")
    except Exception as e:
        logger.error(f"Error unbanning user: {e}")
        await message.answer(f"Ошибка при разблокировке пользователя: {e}")


@rate_limit(limit=3)
@is_admin
async def cmd_check_user_status(message: types.Message, state: FSMContext):
    """Check user status - /status <user_id>"""
    try:
        args = message.text.split()
        if len(args) != 2:
            await message.answer("Использование: /status <user_id>")
            return
        
        user_id = int(args[1])
        
        if not database.selector.is_exist_user(user_id):
            await message.answer(f"Пользователь {user_id} не найден в базе данных")
            return
        
        username = database.selector.get_username_by_id(user_id)
        is_banned = database.selector.is_user_banned(user_id)
        subscription_end = database.selector.get_subscription_end_date(user_id)
        is_expired = database.selector.is_subscription_end(user_id)
        
        status_text = f"👤 Пользователь {hcode(user_id)}::{hcode(username)}\n\n"
        status_text += f"🚫 Заблокирован: {'Да' if is_banned else 'Нет'}\n"
        status_text += f"📅 Подписка до: {subscription_end}\n"
        status_text += f"⏰ Статус подписки: {'Истекла' if is_expired else 'Активна'}\n"
        
        # Check configs
        configs = database.selector.all_user_configs(user_id)
        if configs:
            status_text += f"📱 Конфигурации: {', '.join([config[0] for config in configs])}\n"
        else:
            status_text += f"📱 Конфигурации: Нет\n"
        
        await message.answer(status_text, parse_mode=types.ParseMode.HTML)
        
    except ValueError:
        await message.answer("Неверный формат user_id")
    except Exception as e:
        logger.error(f"Error checking user status: {e}")
        await message.answer(f"Ошибка при проверке статуса пользователя: {e}")
