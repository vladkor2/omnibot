from ..base_chain import BaseChain
from ..steps import TextStep

class RChain(BaseChain):
    """Команда /r - простая рассылка"""
    
    command = "r"
    description = "📢 Простая рассылка по чатам"
    
    steps = [
        TextStep(
            name="message",
            prompt="📝 Введите сообщение для рассылки:"
        )
    ]
    
    async def execute(self, update, context):
        """Отправка сообщения во все чаты"""
        data = context.user_data['chain_data']
        message = data['message']
        
        chats = context.bot_data.get('broadcast_chats', [])
        
        if not chats:
            return "❌ Список чатов для рассылки пуст!"
        
        success = 0
        failed = 0
        
        for chat_id in chats:
            try:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"📢 {message}"
                )
                success += 1
            except Exception as e:
                failed += 1
                logger.error(f"Ошибка отправки в {chat_id}: {e}")
        
        return f"✅ Рассылка завершена!\n✓ Успешно: {success}\n✗ Ошибок: {failed}"