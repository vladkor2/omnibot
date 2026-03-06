from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from .common import restricted, private

# Состояние для ConversationHandler
WAITING_FOR_MESSAGE = 1

@restricted
async def r_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /r - начало рассылки"""
    # Проверяем, что команда вызвана в личном чате
    if update.effective_chat.type != 'private':
        await update.message.reply_text(
            "❌ Команда /r работает только в личном чате с ботом."
        )
        return ConversationHandler.END
    
    await update.message.reply_text(
        "📝 Отправь сообщение для рассылки.\n"
        "Или отправь /cancel для отмены."
    )
    
    return WAITING_FOR_MESSAGE

@restricted
async def receive_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение сообщения для рассылки"""
    message_text = update.message.text
    
    # Получаем список чатов из конфига
    broadcast_chats = context.bot_data.get('broadcast_chats', [])
    
    if not broadcast_chats:
        await update.message.reply_text(
            "❌ Список чатов для рассылки пуст!\n"
            "Добавь ID чатов в config.json в поле broadcast_chats"
        )
        return ConversationHandler.END
    
    # Отправляем подтверждение
    status_msg = await update.message.reply_text(
        f"📤 Начинаю рассылку в {len(broadcast_chats)} чатов...\n"
        f"Сообщение: \"{message_text[:50]}{'...' if len(message_text) > 50 else ''}\""
    )
    
    # Отправляем сообщение во все чаты
    success = 0
    failed = 0
    
    for chat_id in broadcast_chats:
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"📢 **Сообщение от админа:**\n\n{message_text}",
                parse_mode='Markdown'
            )
            success += 1
        except Exception as e:
            failed += 1
            print(f"Ошибка отправки в чат {chat_id}: {e}")
    
    # Отправляем отчет
    report = f"✅ Рассылка завершена!\n✓ Успешно: {success}\n✗ Ошибок: {failed}"
    await status_msg.edit_text(report)
    
    return ConversationHandler.END

@restricted
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена рассылки"""
    await update.message.reply_text("❌ Рассылка отменена.")
    return ConversationHandler.END