# ⚡ Быстрая установка Bot Blocking Protection

## 🎯 Что это?
Защита от пользователей, которые блокируют бота, но продолжают пользоваться VPN.

## 🚀 Установка в 3 команды

### 1. Скачайте обновление:
```bash
cd /path/to/your/wireguard-bot
git pull origin master
```

### 2. Запустите автоматическую установку:
```bash
chmod +x install_bot_protection.sh
./install_bot_protection.sh
```

### 3. Проверьте результат:
```bash
sudo systemctl status wireguard-bot
```

## ✅ Готово!

Теперь пользователи, заблокировавшие бота, автоматически теряют доступ к VPN.

### 🔧 Новые команды:
- `/ban <user_id>` - Заблокировать пользователя
- `/unban <user_id>` - Разблокировать пользователя  
- `/status <user_id>` - Проверить статус пользователя

### 🆘 Если что-то пошло не так:
```bash
/tmp/wireguard_bot_backup_*/ROLLBACK.sh
```

**📚 Подробная инструкция:** `INSTALLATION_GUIDE.md`