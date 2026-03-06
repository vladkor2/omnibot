from telegram import Update
from telegram.ext import ContextTypes
from functools import wraps
from config import config  # Импортируем единственный экземпляр

def restricted(func):
    """Декоратор для ограничения доступа к командам (только для админа)"""
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id != config.admin_id:  # Используем config.admin_id
            await update.message.reply_text(
                "❌ Эта команда доступна только владельцу бота."
            )
            return
        return await func(update, context, *args, **kwargs)
    return wrapped

def private(func):
    """Только для админа И только в личных чатах"""
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        chat = update.effective_chat
        
        # Проверка на админа
        if user_id != config.admin_id:
            await update.message.reply_text(
                "❌ Эта команда доступна только владельцу бота."
            )
            return
        
        # Проверка на личный чат
        if chat.type != 'private':
            await update.message.reply_text(
                "❌ Эта команда работает только в личном чате с ботом."
            )
            return
        
        return await func(update, context, *args, **kwargs)
    return wrapped

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Приветственное сообщение"""
    user_id = update.effective_user.id
    
    if user_id == config.admin_id:
        text = (
            f"👋 С возвращением, хозяин!\n"
            f"Я {config.settings['bot']['name']} - твой личный помощник.\n\n"
            f"📌 Доступные команды:\n"
            f"/id - Показать ID текущего чата\n"
            f"/admin - Админ-панель (только для вас)"
        )
    else:
        text = (
            f"👋 Привет, {update.effective_user.first_name}!\n"
            f"Я личный помощник и доступен только своему владельцу."
        )
    
    await update.message.reply_text(text)

async def get_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать ID чата (публичная команда - доступна всем)"""
    chat = update.effective_chat
    user_id = update.effective_user.id
    
    text = f"📋 ID этого чата: `{chat.id}`"
    
    # Если это админ, показываем больше информации
    if user_id == config.admin_id:
        text += f"\n\n🔧 **Доп. информация для админа:**"
        text += f"\nТип чата: {chat.type}"
        text += f"\nНазвание: {chat.title or 'Личный чат'}"
        if chat.username:
            text += f"\nUsername: @{chat.username}"
    
    await update.message.reply_text(text, parse_mode='Markdown')

@restricted  # Только для админа
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Админская панель (только для владельца)"""
    # Получаем статистику
    chat_id = update.effective_chat.id
    
    text = (
        f"🔧 **Админ панель**\n\n"
        f"**Информация:**\n"
        f"• Ваш ID: `{config.admin_id}`\n"
        f"• Текущий чат ID: `{chat_id}`\n"
        f"• Режим отладки: {'✅' if config.debug else '❌'}\n"
        f"• Имя бота: {config.settings['bot']['name']}\n\n"
        f"**Статус:**\n"
        f"• ✅ Бот работает\n"
        f"• 📝 Команды загружены"
    )
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик неизвестных команд"""
    await update.message.reply_text(
        "❓ Неизвестная команда. Используй /start для начала работы."
    )

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Эхо для отладки (только если включен debug)"""
    if config.debug:
        await update.message.reply_text(
            f"📝 Отладка: {update.message.text}"
        )