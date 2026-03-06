#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from telegram import Update
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    filters,
    ConversationHandler
)

# Импортируем конфиг - он загрузится один раз здесь
from config import config
# Импортируем обработчики
from handlers import common
#from handlers import broadcast
from handlers.broadcast import get_handlers, get_commands_description

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG if config.debug else logging.INFO
)
logger = logging.getLogger(__name__)

def setup_handlers(app: Application):
    """Регистрация всех обработчиков"""

    # Загружаем список чатов для рассылки из config.json
    broadcast_chats = config.settings.get('broadcast_chats', [])
    app.bot_data['broadcast_chats'] = broadcast_chats
    logger.info(f"Загружено чатов для рассылки: {len(broadcast_chats)}")

    # === Публичные команды (доступны всем) ===
    app.add_handler(CommandHandler("start", common.start))
    app.add_handler(CommandHandler("id", common.get_chat_id))
    
    # === Приватные команды (только для админа) ===
    app.add_handler(CommandHandler("admin", common.admin_panel))
    
    for handler in get_handlers():
        app.add_handler(handler)

    # === Обработчик неизвестных команд ===
    app.add_handler(MessageHandler(filters.COMMAND, common.unknown_command))
    
    # === Эхо для отладки (только если включен debug) ===
    if config.debug:
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, common.echo))
    
    logger.info(f"Зарегистрировано обработчиков: {len(app.handlers.get(0, []))}")

def main():
    """Основная функция запуска бота"""
    try:
        # Проверяем наличие токена
        if not config.tg_bot_token:
            logger.error("Токен бота не найден в secrets.json!")
            return
        
        # Проверяем наличие admin_id
        if not config.admin_id:
            logger.warning("Admin ID не указан в config.json! Некоторые функции могут быть недоступны.")
        
        # Создаем приложение
        logger.info("Создание приложения бота...")
        application = Application.builder().token(config.tg_bot_token).build()
        
        # Регистрируем обработчики
        setup_handlers(application)
        
        # Выводим информацию о запуске
        logger.info(f"🤖 Бот '{config.settings['bot']['name']}' запущен!")
        logger.info(f"👤 Admin ID: {config.admin_id}")
        logger.info(f"🔧 Режим отладки: {config.debug}")
        logger.info("🚀 Начинаем polling...")
        
        # Запускаем бота
        application.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        logger.error(f"Критическая ошибка при запуске бота: {e}", exc_info=True)
        raise

if __name__ == '__main__':
    main()