import psycopg2 as pg
from loguru import logger
from data import configuration
from datetime import datetime, timedelta


def update_user_payment(user_id: int) -> None:
    """
    Update user payment end date in table users
    add 30 days to current date if user don't have subscription at the moment
    and add 30 days to date in subscription_end_date if user have not expired subscription now
    """
    try:
        conn = pg.connect(**configuration.db_connection_parameters)
        with conn.cursor() as cursor:
            cursor.execute(
                """--sql
                UPDATE users SET subscription_end_date = CASE
                WHEN subscription_end_date < %s THEN %s + %s
                ELSE subscription_end_date + %s END
                WHERE user_id = %s
                """,
                (
                    datetime.now(),
                    datetime.now(),
                    timedelta(days=30),
                    timedelta(days=30),
                    user_id,
                ),
            )

            conn.commit()

            # get username for log
            cursor.execute(
                """--sql
                SELECT username FROM users WHERE user_id = %s
                """,
                (user_id,),
            )
            username = cursor.fetchone()[0]

            logger.info(
                f"[+] user {user_id}::{username} payment updated; added: 30 days"
            )
    except (Exception, pg.DatabaseError) as error:
        logger.error(f"[-] {error}")
        return None


def update_user_config_count(user_id: int) -> None:
    """Update user config count in table users
    add 1 to current config count"""
    try:
        conn = pg.connect(**configuration.db_connection_parameters)
        with conn.cursor() as cursor:
            cursor.execute(
                """--sql
                UPDATE users SET config_count = config_count + 1 WHERE user_id = %s
                """,
                (user_id,),
            )

            conn.commit()
            logger.info(f"[+] user {user_id} config count updated to {cursor.rowcount}")
    except (Exception, pg.DatabaseError) as error:
        logger.error(f"[-] {error}")
        return None


def update_given_subscription_time(user_id: int, days: int) -> None:
    """Update user payment end date in table users
    add given days to date in table if user have not expired subscription now
    else add given days to current date"""
    try:
        conn = pg.connect(**configuration.db_connection_parameters)
        with conn.cursor() as cursor:
            cursor.execute(
                """--sql
                UPDATE users SET subscription_end_date = CASE
                WHEN subscription_end_date < %s THEN %s + %s
                ELSE subscription_end_date + %s END
                WHERE user_id = %s
                """,
                (
                    datetime.now(),
                    datetime.now(),
                    timedelta(days=days),
                    timedelta(days=days),
                    user_id,
                ),
            )

            conn.commit()

            # get username for log
            cursor.execute(
                """--sql
                SELECT username FROM users WHERE user_id = %s
                """,
                (user_id,),
            )
            username = cursor.fetchone()[0]

            logger.info(
                f"[+] user {user_id}::{username} payment updated [BY ADMIN]; added: {days} days"
            )
    except (Exception, pg.DatabaseError) as error:
        logger.error(f"[-] {error}")
        return None


def set_user_enddate_to_n(user_id: int, days: int) -> None:
    """Update user payment end date in table users
    set date to datetime.now() + N days"""
    try:
        conn = pg.connect(**configuration.db_connection_parameters)
        with conn.cursor() as cursor:
            cursor.execute(
                """--sql
                UPDATE users SET subscription_end_date = %s WHERE user_id = %s
                """,
                (datetime.now() + timedelta(days=days), user_id),
            )

            conn.commit()

            # get username for log
            cursor.execute(
                """--sql
                SELECT username FROM users WHERE user_id = %s
                """,
                (user_id,),
            )
            username = cursor.fetchone()[0]

            logger.info(
                f"""[+] user {user_id}::{username} payment updated [BY ADMIN]; set to:
                {datetime.now() + timedelta(days=days)}"""
            )
    except (Exception, pg.DatabaseError) as error:
        logger.error(f"[-] {error}")
        return None


def ban_user(user_id: int) -> None:
    """Ban user permanently by setting is_banned to True and subscription_end_date to far past"""
    try:
        conn = pg.connect(**configuration.db_connection_parameters)
        with conn.cursor() as cursor:
            # Get username for logging
            cursor.execute(
                """--sql
                SELECT username FROM users WHERE user_id = %s
                """,
                (user_id,),
            )
            result = cursor.fetchone()
            username = result[0] if result else "unknown"

            # Ban user and set subscription to expired
            cursor.execute(
                """--sql
                UPDATE users SET 
                    is_banned = TRUE,
                    subscription_end_date = %s
                WHERE user_id = %s
                """,
                (datetime.now() - timedelta(days=9999), user_id),
            )

            conn.commit()
            logger.warning(f"[!] User {user_id}::{username} has been BANNED (bot blocked)")
            
    except (Exception, pg.DatabaseError) as error:
        logger.error(f"[-] Error banning user {user_id}: {error}")
        return None


def unban_user(user_id: int) -> None:
    """Unban user by setting is_banned to False"""
    try:
        conn = pg.connect(**configuration.db_connection_parameters)
        with conn.cursor() as cursor:
            # Get username for logging
            cursor.execute(
                """--sql
                SELECT username FROM users WHERE user_id = %s
                """,
                (user_id,),
            )
            result = cursor.fetchone()
            username = result[0] if result else "unknown"

            # Unban user
            cursor.execute(
                """--sql
                UPDATE users SET is_banned = FALSE WHERE user_id = %s
                """,
                (user_id,),
            )

            conn.commit()
            logger.info(f"[+] User {user_id}::{username} has been UNBANNED")
            
    except (Exception, pg.DatabaseError) as error:
        logger.error(f"[-] Error unbanning user {user_id}: {error}")
        return None
