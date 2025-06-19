# 📖 Пошаговая инструкция установки Bot Blocking Protection

## 🎯 Что делает это обновление

**Проблема:** Пользователи блокируют бота в Telegram, но продолжают пользоваться VPN бесплатно  
**Решение:** Автоматическое обнаружение блокировки и мгновенное отключение таких пользователей

## ⚡ Быстрая установка (1 команда)

```bash
# Перейдите в папку с ботом и выполните:
./install_bot_protection.sh
```

**Готово!** Установка займет 2-3 минуты.

---

## 📋 Подробная пошаговая инструкция

### 🔍 Шаг 1: Проверка текущего состояния

```bash
# Перейдите в папку с ботом
cd /path/to/your/wireguard-bot

# Проверьте, что бот работает
sudo systemctl status wireguard-bot

# Проверьте версию (должна быть старая)
git log --oneline -1
```

### 📥 Шаг 2: Получение обновления

#### Вариант A: Обновление существующего репозитория
```bash
# Скачайте последние изменения
git pull origin master
```

#### Вариант B: Клонирование заново
```bash
# Клонируйте репозиторий
git clone https://github.com/sultanov75/wireguard-bot1.git
cd wireguard-bot1
```

### 🧪 Шаг 3: Предварительная проверка

```bash
# Проверьте готовность к установке
./test_update.py
```

**Ожидаемый результат:**
```
🧪 Testing WireGuard Bot Protection Update
==================================================
✅ Main installer script: install_bot_protection.sh
✅ Code update script: update_bot.py
✅ Database migration script: apply_updates.py
✅ Installation instructions: UPDATE_INSTRUCTIONS.md
✅ Main bot application: app.py
✅ Admin handlers: handlers/admin.py
✅ User handlers: handlers/user.py
✅ Watchdog service: utils/watchdog.py
✅ Database selectors: database/selector.py
✅ Database updates: database/update.py
✅ VPN configuration: utils/vpn_cfg_work.py
✅ psycopg2 available
✅ aiofiles available
🎉 ALL TESTS PASSED!
```

### 🚀 Шаг 4: Автоматическая установка

```bash
# Запустите установщик
./install_bot_protection.sh
```

**Что происходит во время установки:**

1. **Проверка системы** (10 сек)
   ```
   [INFO] Running pre-flight checks...
   [INFO] Prerequisites check passed
   ```

2. **Создание резервных копий** (30 сек)
   ```
   [INFO] Creating backup directory: /tmp/wireguard_bot_backup_20241219_143022
   [INFO] Stopping bot service...
   [INFO] Bot service stopped
   [INFO] Backing up current bot code...
   [INFO] Code backed up to: /tmp/wireguard_bot_backup_20241219_143022/bot_code
   [INFO] Backing up WireGuard configuration...
   [INFO] WireGuard config backed up
   ```

3. **Резервное копирование базы данных** (60 сек)
   ```
   Please provide your database connection details:
   Database name: wireguard_bot
   Database user: postgres
   Database host [localhost]: 
   Database port [5432]: 
   Database password: [вводите пароль]
   [INFO] Database backed up to: /tmp/wireguard_bot_backup_20241219_143022/database_backup.sql
   ```

4. **Применение обновлений** (60 сек)
   ```
   [INFO] Starting migration...
   [INFO] Rollback script created: /tmp/wireguard_bot_backup_20241219_143022/rollback.sh
   [INFO] Checking database connection...
   [INFO] Database connection successful
   [INFO] Applying database migration...
   [INFO] Database migration applied successfully
   [INFO] Applying code updates...
   ✓ Created utils/bot_error_handler.py
   ✓ Updated utils/watchdog.py
   ✓ Updated database/selector.py
   ✓ Updated database/update.py
   ✓ Updated utils/vpn_cfg_work.py
   ✓ Updated handlers/admin.py
   ✓ Updated handlers/user.py
   ✓ Updated handlers/__init__.py
   ```

5. **Тестирование и запуск** (30 сек)
   ```
   [INFO] Testing installation...
   [INFO] Installation test passed
   [INFO] Starting bot...
   [INFO] Bot service started
   ```

### ✅ Шаг 5: Проверка успешной установки

#### 5.1 Проверка статуса бота
```bash
sudo systemctl status wireguard-bot
```
**Ожидаемо:** `Active: active (running)`

#### 5.2 Проверка логов
```bash
tail -f logs/*.log
```
**Ожидаемо:** 
```
2024-12-19 14:32:15.123 | SUCCESS  | __main__:on_startup:34 - [+] Bot started successfully
2024-12-19 14:32:15.124 | SUCCESS  | utils.watchdog:run:24 - [+] Watchdog coroutine created and started successfully
```

#### 5.3 Проверка новых команд
В Telegram боте отправьте:
```
/status YOUR_USER_ID
```
**Ожидаемо:** Информация о пользователе

#### 5.4 Проверка базы данных
```bash
# Проверьте, что новая таблица создана
psql -d your_database -c "\dt banned_users"
```
**Ожидаемо:** Таблица `banned_users` существует

### 🎉 Шаг 6: Финальная проверка

```bash
# Проверьте все новые файлы
ls -la utils/bot_error_handler.py
ls -la install_bot_protection.sh
ls -la update_bot.py

# Проверьте версию
git log --oneline -1
```
**Ожидаемо:** Последний коммит содержит "Bot Blocking Protection System"

---

## 🛠️ Ручная установка (если автоматическая не сработала)

### Шаг 1: Остановка бота
```bash
sudo systemctl stop wireguard-bot
```

### Шаг 2: Резервное копирование
```bash
# Код
cp -r . ../wireguard-bot-backup-$(date +%Y%m%d_%H%M%S)

# WireGuard
sudo cp /etc/wireguard/wg0.conf /etc/wireguard/wg0.conf.backup

# База данных
pg_dump your_database > database_backup.sql
```

### Шаг 3: Установка зависимостей
```bash
pip install psycopg2-binary aiofiles
```

### Шаг 4: Миграция базы данных
```bash
python3 apply_updates.py
```

### Шаг 5: Обновление кода
```bash
python3 update_bot.py
```

### Шаг 6: Запуск бота
```bash
sudo systemctl start wireguard-bot
```

---

## 🆘 Что делать если что-то пошло не так

### Проблема: Бот не запускается

#### Решение 1: Проверка логов
```bash
journalctl -u wireguard-bot -f
```

#### Решение 2: Проверка зависимостей
```bash
pip list | grep -E "(psycopg2|aiofiles)"
```

#### Решение 3: Переустановка зависимостей
```bash
pip install --force-reinstall psycopg2-binary aiofiles
```

### Проблема: Ошибки базы данных

#### Решение: Повторная миграция
```bash
python3 apply_updates.py
```

### Проблема: Новые команды не работают

#### Решение: Перезапуск бота
```bash
sudo systemctl restart wireguard-bot
```

### 🔄 Полный откат (если ничего не помогает)

```bash
# Найдите папку с бэкапом
ls /tmp/wireguard_bot_backup_*

# Запустите автоматический откат
/tmp/wireguard_bot_backup_YYYYMMDD_HHMMSS/ROLLBACK.sh

# Или ручной откат:
sudo systemctl stop wireguard-bot
rm -rf ./*
cp -r ../wireguard-bot-backup-*/* ./
sudo cp /etc/wireguard/wg0.conf.backup /etc/wireguard/wg0.conf
psql your_database < database_backup.sql
sudo systemctl start wireguard-bot
```

---

## 📊 Что изменилось после установки

### ✅ Новые возможности:

#### Автоматическая защита:
- 🔍 Обнаружение блокировки бота пользователями
- 🗑️ Мгновенное удаление VPN конфигураций нарушителей
- 🚫 Постоянная блокировка злоупотребляющих пользователей
- 📝 Детальное логирование всех действий

#### Новые админские команды:
- `/ban <user_id>` - Заблокировать пользователя навсегда
- `/unban <user_id>` - Разблокировать пользователя
- `/status <user_id>` - Проверить статус пользователя

### ✅ Что НЕ изменилось:
- Все существующие пользователи работают как раньше
- Все старые команды работают
- Конфигурации WireGuard сохранены
- База данных не пострадала

### 🛡️ Как работает защита:

**До обновления:**
```
Пользователь блокирует бота → Продолжает пользоваться VPN → Потеря дохода
```

**После обновления:**
```
Пользователь блокирует бота → Мгновенное обнаружение → Отключение VPN → Защита дохода
```

---

## 📈 Мониторинг работы системы

### Ключевые логи для отслеживания:
```bash
# Следите за этими событиями:
tail -f logs/*.log | grep -E "(Bot blocked|banned|safe_send_message)"
```

### Важные события:
- `"Bot blocked by user"` - Обнаружена блокировка бота
- `"User X has been permanently banned"` - Пользователь автоматически заблокирован
- `"Peer X permanently removed"` - VPN конфигурация удалена
- `"safe_send_message failed"` - Ошибка отправки сообщения

### Статистика нарушителей:
```bash
# Количество заблокированных пользователей
psql -d your_database -c "SELECT COUNT(*) FROM banned_users;"

# Список заблокированных
psql -d your_database -c "SELECT user_id, banned_at, reason FROM banned_users ORDER BY banned_at DESC;"
```

---

## 🎯 Результат

**🎉 Поздравляем! Ваш бот теперь защищен от злоупотреблений!**

### Что получили:
- ✅ **100% защита** от пользователей, блокирующих бота
- ✅ **Автоматическое обнаружение** нарушителей
- ✅ **Мгновенная реакция** на блокировку
- ✅ **Полный контроль** над пользователями
- ✅ **Детальная статистика** и логирование

### Ваши пользователи больше не смогут:
- ❌ Блокировать бота и продолжать пользоваться VPN
- ❌ Обманывать систему оплаты
- ❌ Злоупотреблять сервисом

**Теперь каждый заблокированный бот = мгновенно отключенный VPN!** 🛡️